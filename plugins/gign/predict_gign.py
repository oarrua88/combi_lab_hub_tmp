"""Predict binding affinity (pKd) with GIGN (Yang et al., J. Phys. Chem. Lett. 2023) for many complexes.

GIGN (geometric interaction graph neural network) works on one graph that joins
the ligand atoms and the pocket atoms (residues within 5 A of the ligand), with
separate covalent and non-covalent (< 5 A) edges and the 3D coordinates.

The authors' pipeline is three scripts with paths written in the code
(preprocessing.py -> dataset_GIGN.py -> predict.py) and calls Open Babel through
os.system, which breaks on folders with spaces ("SOFTWARE SF"). This wrapper
does the same steps for a folder of complexes, one per sub-folder, and calls the
authors' functions and trained checkpoints directly:
  1. PyMOL: pocket = residues within 5 A of the ligand (waters and H removed)
  2. Open Babel: <code>_ligand.mol2 -> .pdb without hydrogens ("obabel -d")
  3. RDKit reads both .pdb files; dataset_GIGN.mols2graphs builds the graph
  4. GIGN(35, 256) with the trained weights -> pKd

Usage (inside the gign environment)
  python predict_gign.py --gign-dir <GIGN repository folder> -d <complexes folder> [-o predictions.csv]

Each complex needs <code>_protein.pdb and <code>_ligand.mol2.
By default the three trained models of the repository (repeat0..2) are run and
their mean is reported as pKd_predicted; --model 0|1|2 runs a single one.
"""
import argparse
import glob
import os
import pickle
import shutil
import subprocess
import sys
import tempfile
import warnings

import pandas as pd

DISTANCE = 5  # A, as in the authors' preprocessing.py and dataset_GIGN.py


def load(gign_dir, models=(0, 1, 2)):
    """Import the authors' code and load the trained models (CPU)."""
    code = os.path.join(os.path.abspath(gign_dir), "GIGN")
    if not os.path.isfile(os.path.join(code, "GIGN.py")):
        sys.exit("ERROR: %s does not look like the GIGN repository (GIGN/GIGN.py missing)" % gign_dir)
    sys.path.insert(0, code)
    warnings.filterwarnings("ignore")
    import torch
    from rdkit import RDLogger
    RDLogger.DisableLog("rdApp.*")
    from GIGN import GIGN
    import dataset_GIGN
    ckpts = sorted(glob.glob(os.path.join(code, "model", "*_GIGN_repeat*", "model", "*.pt")))
    if len(ckpts) != 3:
        sys.exit("ERROR: expected 3 checkpoints in %s, found %d" % (os.path.join(code, "model"), len(ckpts)))
    nets = []
    for i in models:
        net = GIGN(35, 256)
        net.load_state_dict(torch.load(ckpts[i], map_location="cpu"))
        net.eval()
        nets.append(net)
    return torch, nets, dataset_GIGN


def prepare(protein_pdb, ligand_mol2, work, code="lig"):
    """Pocket + ligand as RDKit molecules, exactly as the authors' preprocessing.py."""
    import pymol
    from rdkit import Chem
    os.makedirs(work, exist_ok=True)
    prot = os.path.join(work, "receptor.pdb")
    lig_mol2 = os.path.join(work, code + "_ligand.mol2")
    shutil.copyfile(protein_pdb, prot)
    shutil.copyfile(ligand_mol2, lig_mol2)
    pocket = os.path.join(work, "Pocket_%dA.pdb" % DISTANCE)
    lig_pdb = os.path.join(work, code + "_ligand.pdb")
    try:
        pymol.cmd.load(prot)
        pymol.cmd.remove("resn HOH")
        pymol.cmd.load(lig_mol2)
        pymol.cmd.remove("hydrogens")
        pymol.cmd.select("Pocket", "byres %s_ligand around %d" % (code, DISTANCE))
        pymol.cmd.save(pocket, "Pocket")
    finally:
        pymol.cmd.delete("all")
    r = subprocess.run(["obabel", lig_mol2, "-O", lig_pdb, "-d"], capture_output=True, text=True)
    if r.returncode != 0 or not os.path.isfile(lig_pdb):
        raise RuntimeError("Open Babel failed: " + (r.stderr or "").strip())
    ligand = Chem.MolFromPDBFile(lig_pdb, removeHs=True)
    pock = Chem.MolFromPDBFile(pocket, removeHs=True)
    if ligand is None or pock is None:
        raise RuntimeError("RDKit cannot read the %s" % ("ligand" if ligand is None else "pocket"))
    return ligand, pock


def score(torch, nets, ds, ligand, pocket, work):
    """List of pKd, one per loaded model."""
    from torch_geometric.data import Batch
    cpath = os.path.join(work, "complex.rdkit")
    gpath = os.path.join(work, "graph.pyg")
    with open(cpath, "wb") as f:
        pickle.dump((ligand, pocket), f)
    ds.mols2graphs(cpath, 0.0, gpath, dis_threshold=DISTANCE)
    if not os.path.isfile(gpath):
        raise RuntimeError("graph construction failed")
    data = Batch.from_data_list([torch.load(gpath)])
    with torch.no_grad():
        return [float(n(data).view(-1)[0]) for n in nets]


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--gign-dir", required=True, help="GIGN repository folder (contains GIGN/GIGN.py)")
    ap.add_argument("-d", "--directory", required=True, help="folder with one sub-folder per complex")
    ap.add_argument("-o", "--output", default="predictions.csv", help="output CSV (default: predictions.csv)")
    ap.add_argument("--model", choices=("0", "1", "2", "all"), default="all",
                    help="trained model to use: 0, 1, 2 or all (mean of the three, default)")
    args = ap.parse_args()

    models = (0, 1, 2) if args.model == "all" else (int(args.model),)
    torch, nets, ds = load(args.gign_dir, models)
    tmp = tempfile.mkdtemp(prefix="gign_")
    rows = []
    for code in sorted(os.listdir(args.directory)):
        folder = os.path.join(args.directory, code)
        prot = os.path.join(folder, code + "_protein.pdb")
        lig = os.path.join(folder, code + "_ligand.mol2")
        if not (os.path.isfile(prot) and os.path.isfile(lig)):
            continue
        try:
            work = os.path.join(tmp, code)
            ligand, pocket = prepare(prot, lig, work)
            preds = score(torch, nets, ds, ligand, pocket, work)
        except Exception as e:  # keep going with the other complexes
            print("Skipping %s: %s" % (code, e))
            continue
        mean = sum(preds) / len(preds)
        rows.append([code, round(mean, 4)] + [round(p, 4) for p in preds])
        print("%s\t%.4f\t%s" % (code, mean, " ".join("%.4f" % p for p in preds)))
    shutil.rmtree(tmp, ignore_errors=True)
    if not rows:
        sys.exit("ERROR: no complexes scored in " + args.directory)
    cols = ["pdbid", "pKd_predicted"] + ["pKd_model%d" % i for i in models]
    pd.DataFrame(rows, columns=cols).to_csv(args.output, index=False)
    print("Done: %d complexes -> %s" % (len(rows), os.path.abspath(args.output)))


if __name__ == "__main__":
    main()
