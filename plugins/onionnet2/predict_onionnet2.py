"""Predict binding affinity (pKd) with OnionNet-2 (Wang et al., 2021) for many complexes.

The authors' scoring/predict.py scores ONE complex per run, needs the ligand as
.pdb and reloads the 885 MB model every time. This wrapper reuses the authors'
own feature code (ParseProtein, ParseLigand, GetFeatures from scoring/predict.py),
converts .mol2/.sdf ligands to .pdb with Open Babel (as the README says), and
loads the model once.

Usage (inside the onionnet2 environment)
  python predict_onionnet2.py --on-dir <OnionNet-2 folder> -d <complexes folder> -m <62shell_saved-model.h5> [-o predictions.csv]

Each complex needs its own folder with <code>_protein.pdb and one ligand file:
<code>_ligand.pdb, .mol2 or .sdf (in that order of preference). CASF-2016 folders
work as they are: the extra _pocket.pdb and _ligand_opt.mol2 files are ignored.

Note on waters: the parser also reads HETATM lines of the protein file, so
crystallographic waters (HOH) count as "OTH" residues. PDBbind protein files,
which the authors used, contain waters; CASF-2016 protein files do not. This
changes the prediction (see INSTALL.md).
"""
import argparse
import itertools
import os
import sys
import tempfile
from argparse import Namespace

os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "2")
os.environ["CUDA_VISIBLE_DEVICES"] = "-1"

import numpy as np
import pandas as pd

SHELLS = 62
SHAPE = [84, 124, 1]


def load_upstream(on_dir):
    """Import the authors' scoring/predict.py and set the globals it expects."""
    sys.path.insert(0, os.path.join(on_dir, "scoring"))
    import predict as P
    P.args = Namespace(shells=SHELLS, alpha=0.7)
    P.alpha = 0.7
    lig_ele = ['H', 'C', 'O', 'N', 'P', 'S', 'Hal', 'DU']
    rec_res = ['GLY', 'ALA', 'VAL', 'LEU', 'ILE', 'PRO', 'PHE', 'TYR', 'TRP', 'SER',
               'THR', 'CYS', 'MET', 'ASN', 'GLN', 'ASP', 'GLU', 'LYS', 'ARG', 'HIS', 'OTH']
    P.keys = ["_".join(x) for x in itertools.product(rec_res, lig_ele)]
    return P


def ligand_as_pdb(folder, code, workdir):
    """Return a .pdb path for the ligand, converting .mol2/.sdf with Open Babel if needed."""
    pdb = os.path.join(folder, code + "_ligand.pdb")
    if os.path.isfile(pdb):
        return pdb
    for ext in ("mol2", "sdf"):
        src = os.path.join(folder, "%s_ligand.%s" % (code, ext))
        if os.path.isfile(src):
            from openbabel import pybel
            mol = next(pybel.readfile(ext, src))
            out = os.path.join(workdir, code + "_ligand.pdb")
            mol.write("pdb", out, overwrite=True)
            return out
    return None


def compute_features(P, protein_pdb, ligand_pdb):
    return P.generate_features(protein_pdb, ligand_pdb)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--on-dir", required=True, help="OnionNet-2 folder (with scoring/ and models/)")
    ap.add_argument("-d", "--directory", required=True, help="folder with one sub-folder per complex")
    ap.add_argument("-m", "--model", required=True, help="62shell_saved-model.h5")
    ap.add_argument("-s", "--scaler", help="train_scaler.scaler (default: <on-dir>/models/train_scaler.scaler)")
    ap.add_argument("-o", "--output", default="predictions.csv", help="output CSV (default: predictions.csv)")
    args = ap.parse_args()

    on_dir = os.path.abspath(args.on_dir)
    scaler_path = args.scaler or os.path.join(on_dir, "models", "train_scaler.scaler")
    P = load_upstream(on_dir)
    work = tempfile.mkdtemp(prefix="onionnet2_")

    codes, feats = [], []
    for code in sorted(os.listdir(args.directory)):
        folder = os.path.join(args.directory, code)
        protein = os.path.join(folder, code + "_protein.pdb")
        if not os.path.isdir(folder) or not os.path.isfile(protein):
            continue
        ligand = ligand_as_pdb(folder, code, work)
        if ligand is None:
            print("Skipping %s: no ligand .pdb/.mol2/.sdf" % code)
            continue
        feats.append(compute_features(P, protein, ligand))
        codes.append(code)
    if not codes:
        sys.exit("ERROR: no complexes found in " + args.directory)
    print("Features computed for %d complexes" % len(codes))

    import joblib
    import tensorflow as tf
    scaler = joblib.load(scaler_path)
    x = scaler.transform(np.array(feats)).reshape([-1] + SHAPE)
    print("Loading model (885 MB, takes a moment) ...")
    model = tf.keras.models.load_model(args.model, custom_objects={"RMSE": P.RMSE, "PCC": P.PCC, "PCC_RMSE": P.PCC_RMSE})
    pred = model.predict(x).ravel()
    pd.DataFrame({"pdbid": codes, "pKd_predicted": np.round(pred, 4)}).to_csv(args.output, index=False)
    print("Done -> %s" % os.path.abspath(args.output))


if __name__ == "__main__":
    main()
