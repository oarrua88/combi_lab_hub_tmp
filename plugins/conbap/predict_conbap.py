"""ConBAP - batch prediction for a folder of protein-ligand complexes (CPU).

ConBAP (Luo et al., J. Chem. Inf. Model. 2024) predicts binding affinity with a network
pre-trained by contrastive learning on re-docked poses and fine-tuned on PDBbind.
This wrapper runs the authors' own pipeline, unchanged, for each complex:
  1. pocket = protein residues within 8 A of the ligand, with PyMOL
     (authors' preprocessing.generate_pocket: waters and hydrogens removed);
  2. (ligand, pocket) RDKit pair, then the four graphs of dataset_ConBAP.mols2graphs;
  3. the contrastive encoder (unsupervised/.../contrastive_no_filtered.pt) and the
     affinity head (supervised/model/20231007_111336_ConBAP_repeat0, the checkpoint
     of the authors' predict.py).
Changes: CPU, no fixed folder layout, one model load, and the ligand file.

Ligand file (--ligand): the authors read <code>.sdf with RDKit (sanitized). RDKit
cannot sanitize the CASF-2016 .sdf of several complexes, 1a30 among them, so the
default "auto" reads <code>_ligand.sdf and falls back to <code>_ligand.mol2.

Usage (inside the conbap environment)
  python predict_conbap.py --conbap-dir <ConBAP folder> -d <complexes folder> [-o predictions.csv]
"""
import argparse
import os
import pickle
import shutil
import sys
import tempfile
import warnings

warnings.filterwarnings("ignore")

import pandas as pd

UNSUP = os.path.join("unsupervised", "model", "20240111_193210_ConBAP_repeat3", "model", "contrastive_no_filtered.pt")
SUP = os.path.join("supervised", "model", "20231007_111336_ConBAP_repeat0", "model",
                   "epoch-292, train_loss-0.1220, train_rmse-0.3493, valid_rmse-1.1663, valid_pr-0.7788.pt")
DIST = 8


def load(cb_dir):
    sup = os.path.join(cb_dir, "supervised")
    if sup not in sys.path:
        sys.path.insert(0, sup)
    import torch
    from ConBAP import ConBAP, downstream_affinity
    enc = ConBAP(35, 256)
    enc.load_state_dict(torch.load(os.path.join(cb_dir, UNSUP), map_location="cpu"))
    net = downstream_affinity(enc, 256)
    net.load_state_dict(torch.load(os.path.join(cb_dir, SUP), map_location="cpu"))
    net.eval()
    return net


def read_ligand(folder, code, mode="auto"):
    from rdkit import Chem
    sdf = os.path.join(folder, code + "_ligand.sdf")
    mol2 = os.path.join(folder, code + "_ligand.mol2")
    tries = {"auto": [("sdf", sdf), ("mol2", mol2)], "sdf": [("sdf", sdf)], "mol2": [("mol2", mol2)],
             "sdf-nosanitize": [("sdf-nosanitize", sdf)]}[mode]
    for kind, f in tries:
        if not os.path.isfile(f):
            continue
        if kind == "sdf":
            m = Chem.MolFromMolFile(f, removeHs=True)
        elif kind == "mol2":
            m = Chem.MolFromMol2File(f, removeHs=True)
        else:
            m = Chem.MolFromMolFile(f, sanitize=False, removeHs=True)
        if m is not None:
            return m, f, kind
    raise ValueError("RDKit cannot read the ligand of %s (%s)" % (code, mode))


def make_pocket(protein, ligand_file, out_pdb):
    """Authors' generate_pocket: residues within 8 A of the ligand, no waters, no H."""
    import pymol
    from pymol import cmd
    pymol.finish_launching(["pymol", "-qc"]) if not hasattr(pymol, "_launched") else None
    pymol._launched = True
    cmd.load(protein, "prot")
    cmd.remove("resn HOH")
    cmd.load(ligand_file, "lig")
    cmd.remove("hydrogens")
    cmd.select("Pocket", "byres lig around %d" % DIST)
    cmd.save(out_pdb, "Pocket")
    cmd.delete("all")


def featurize(folder, code, work, ligand_mode="auto"):
    """Write the authors' four .pyg graphs for one complex into work/<code>/."""
    from rdkit import Chem
    from dataset_ConBAP import mols2graphs
    cdir = os.path.join(work, code)
    os.makedirs(cdir, exist_ok=True)
    lig, lig_file, kind = read_ligand(folder, code, ligand_mode)
    protein = os.path.join(folder, code + "_protein.pdb")
    # mols2graphs() reads the whole protein from <work>/protein/<code>_protein.pdb
    os.makedirs(os.path.join(work, "protein"), exist_ok=True)
    shutil.copy(protein, os.path.join(work, "protein", code + "_protein.pdb"))
    pocket_pdb = os.path.join(cdir, "Pocket_%dA.pdb" % DIST)
    make_pocket(protein, lig_file, pocket_pdb)
    pocket = Chem.MolFromPDBFile(pocket_pdb, sanitize=False, removeHs=True)
    if pocket is None:
        raise ValueError("RDKit cannot read the pocket of %s" % code)
    rd = os.path.join(cdir, "%s_%dA.rdkit" % (code, DIST))
    with open(rd, "wb") as f:
        pickle.dump((lig, pocket), f)
    paths = [os.path.join(cdir, "ConBAP-%s_%s_%dA.pyg" % (code, p, DIST)) for p in ("l", "p", "aa", "complex")]
    import contextlib, io
    with contextlib.redirect_stdout(io.StringIO()):     # mols2graphs prints the code
        mols2graphs(rd, code, 0.0, *paths, DIST)
    if not all(os.path.isfile(p) for p in paths):
        raise RuntimeError("graph construction failed for %s" % code)
    return kind


def score(net, work, codes):
    import torch
    from dataset_ConBAP import GraphDataset, PLIDataLoader
    df = pd.DataFrame({"pdb": codes, "affinity": 0.0})
    ds = GraphDataset(work, df, graph_type="ConBAP", dis_threshold=DIST, create=False)
    out = []
    with torch.no_grad():
        for cid, batch in zip(ds.complex_ids, PLIDataLoader(ds, batch_size=1, shuffle=False, num_workers=0)):
            out.append((cid, float(net(batch).reshape(-1)[0])))
    return out


def predict_folder(cb_dir, root, ligand_mode="auto", net=None, verbose=True):
    net = net or load(cb_dir)
    codes = sorted(d for d in os.listdir(root) if os.path.isdir(os.path.join(root, d)))
    work = tempfile.mkdtemp(prefix="conbap_")
    ok, rows = [], {}
    try:
        for n, code in enumerate(codes, 1):
            try:
                rows[code] = [None, featurize(os.path.join(root, code), code, work, ligand_mode), ""]
                ok.append(code)
            except Exception as e:                       # noqa: BLE001
                rows[code] = [None, "", str(e).splitlines()[0][:200]]
                if verbose:
                    print("[%d/%d] %s  ERROR: %s" % (n, len(codes), code, rows[code][2]))
        for code, p in score(net, work, ok):
            rows[code][0] = round(p, 4)
            if verbose:
                print("%s  pKd %.4f  (ligand from %s)" % (code, p, rows[code][1]))
    finally:
        shutil.rmtree(work, ignore_errors=True)
    return pd.DataFrame([(c,) + tuple(rows[c]) for c in codes],
                        columns=["pdbid", "pKd_predicted", "ligand_source", "error"])


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--conbap-dir", required=True, help="ConBAP folder (with supervised/ and unsupervised/)")
    ap.add_argument("-d", "--directory", required=True, help="folder with one sub-folder per complex")
    ap.add_argument("-o", "--output", default="predictions.csv", help="output CSV (default: predictions.csv)")
    ap.add_argument("--ligand", choices=("auto", "sdf", "mol2", "sdf-nosanitize"), default="auto",
                    help="ligand file: auto = .sdf, or .mol2 if RDKit cannot read the .sdf (default)")
    a = ap.parse_args()
    df = predict_folder(os.path.abspath(a.conbap_dir), os.path.abspath(a.directory), a.ligand)
    os.makedirs(os.path.dirname(os.path.abspath(a.output)), exist_ok=True)
    df.to_csv(a.output, index=False)
    print("Done: %d complexes (%d errors) -> %s" % (len(df), df.pKd_predicted.isna().sum(), a.output))


if __name__ == "__main__":
    main()
