"""Predict binding affinity (pKd) with GB-Score (Rayka et al., 2022).

The GB-Score repository only ships the feature generator (generate_features.py).
The trained model (gb_score.joblib) expects the features AFTER the authors'
preprocessing in analysis.ipynb:
  1. keep only the columns that survive their variance (> 0.01) and
     correlation (<= 0.95) filters, and
  2. standardize each column with the mean and std of their full dataset
     (PDBbind 2019 general + refined set, total_set_2019.csv).
Those columns, means and stds are stored in reference/gb_score_preprocessing.csv
(computed with make_preprocessing.py from the authors' Figshare files).

Usage (inside the gb-score environment)
  python predict_gb_score.py --gb-dir <GB_Score folder> -d <complexes folder> -m <gb_score.joblib> [-o predictions.csv]

Feature note: protein elements are read from the PDB element column, which
reproduces the authors' published features (see compute_features).

Each complex needs its own folder with exactly one ligand .mol2 and one protein .pdb
(hydrogens included). For CASF-2016 use prepare_casf.py first.
Writes <output>.csv (pdbid, predicted pKd) and <output>_features.csv (raw 400 features).
"""
import argparse
import os
import sys

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_PREP = os.path.join(HERE, "reference", "gb_score_preprocessing.csv")


def compute_features(gb_dir, folder, out_csv=None):
    """400 GB-Score features per complex, using the authors' helper functions.

    IMPORTANT: the public generate_features.py assigns protein elements with a
    fixed atom-name table (atom_types) that misses many hydrogen names used in
    PDBbind files (HG21, HD11, HE21, HH11, ...). The features the authors
    published (and trained the model on) count those hydrogens, which is what
    you get when the element is taken from the PDB element column. Using the
    public table under-estimates every protein-H feature (up to 2x for 1a30),
    so here the element comes from the PDB file, as in the published data.
    """
    sys.path.insert(0, gb_dir)
    import generate_features as G  # authors' code: 10 x 10 elements x 4 residue groups, cutoff 12 A, exp 2
    from glob import glob
    from scipy import spatial
    from biopandas.mol2 import PandasMol2
    from biopandas.pdb import PandasPdb

    names = list(G.generate_columns_name(G.elements, G.amino_acid_groups).values())
    data = {}
    for entry in sorted(os.listdir(folder)):
        path = os.path.join(folder, entry)
        ligands = sorted(glob(os.path.join(path, "*.mol2")))
        proteins = sorted(glob(os.path.join(path, "*.pdb")))
        if not ligands or not proteins:
            print("Skipping %s: needs one .mol2 and one .pdb" % entry)
            continue
        try:
            lig = PandasMol2().read_mol2(ligands[0]).df
        except Exception:
            print("Error in file structure %s" % entry)
            continue
        lig["element_symbol"] = lig["atom_type"].apply(lambda x: x.split(".")[0])
        prot = PandasPdb().read_pdb(proteins[0]).df["ATOM"]
        feats = []
        for le in G.elements:
            lc = G.ligand_specific_element_coordinates(lig, le)
            for pe in G.elements:
                for group in G.amino_acid_groups:
                    pc = G.protein_specific_element_coordinates(prot, pe, group)
                    feats.append(G.weighting_sum(spatial.distance.cdist(lc, pc).ravel(), 12.0, 2))
        data[entry] = feats
    df = pd.DataFrame.from_dict(data, orient="index", columns=names)
    if out_csv:
        df.to_csv(out_csv)
    return df


def preprocess(raw, prep_csv):
    prep = pd.read_csv(prep_csv, index_col=0)
    missing = [c for c in prep.index if c not in raw.columns]
    if missing:
        sys.exit("ERROR: features missing from the input: %s" % missing[:5])
    x = raw[prep.index]
    return (x - prep["mean"]) / prep["std"]


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--gb-dir", required=True, help="folder with the authors' generate_features.py")
    ap.add_argument("-d", "--directory", required=True, help="folder with one sub-folder per complex")
    ap.add_argument("-m", "--model", required=True, help="gb_score.joblib")
    ap.add_argument("-p", "--prep", default=DEFAULT_PREP, help="preprocessing table (default: reference/gb_score_preprocessing.csv)")
    ap.add_argument("-o", "--output", default="predictions.csv", help="output CSV (default: predictions.csv)")
    args = ap.parse_args()

    out = os.path.abspath(args.output)
    feat_csv = os.path.splitext(out)[0] + "_features.csv"
    print("Computing features ...")
    raw = compute_features(os.path.abspath(args.gb_dir), os.path.abspath(args.directory), feat_csv)
    x = preprocess(raw, args.prep)

    print("Loading model (about 600 MB, takes a moment) ...")
    from joblib import load
    model = load(args.model)
    pred = pd.DataFrame({"pdbid": x.index, "pKd_predicted": np.round(model.predict(x.values), 4)})
    pred.to_csv(out, index=False)
    print("Done: %d complexes -> %s" % (len(pred), out))
    print("Features -> %s" % feat_csv)


if __name__ == "__main__":
    main()
