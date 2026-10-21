"""Predict binding affinity (pKd) with EHIGN-PLA (Yang et al., 2024) for many complexes.

EHIGN (edge-enhanced heterogeneous interaction graph network) builds a DGL
heterograph with two node types (ligand atoms, pocket atoms within 5 A of the
ligand) and four edge types (ligand bonds, pocket bonds, ligand->pocket and
pocket->ligand contacts < 5 A), each edge with 3D geometric features. The model
gives two predictions (ligand->pocket and pocket->ligand) whose mean is pKd.

The authors' pipeline is preprocess_complex.py -> graph_constructor.py ->
test.py with paths written in the code, Open Babel called through os.system
(breaks on folders with spaces) and code for DGL 0.9. This wrapper does the same
steps for a folder of complexes, one per sub-folder, calling the authors'
functions and trained checkpoints directly:
  1. PyMOL: pocket = residues within 5 A of the ligand (waters and H removed)
  2. Open Babel: <code>_ligand.mol2 -> .pdb without hydrogens ("obabel -d")
  3. RDKit reads both .pdb files; graph_constructor.mols2graphs builds the graph
  4. DTIPredictor(35, 17, 256, 3) with the trained weights -> pKd

Usage (inside the gign environment, shared with GIGN)
  python predict_ehign_pla.py --ehign-dir <EHIGN_PLA repository folder> -d <complexes folder> [-o predictions.csv]

Each complex needs <code>_protein.pdb and <code>_ligand.mol2.
By default the three trained models of the repository (repeat0..2) are run and
their mean is reported as pKd_predicted; --model 0|1|2 runs a single one
(the authors' test.py uses model 0).
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

DISTANCE = 5  # A, as in the authors' preprocess_complex.py and graph_constructor.py


def load(ehign_dir, models=(0, 1, 2)):
    """Import the authors' code and load the trained models (CPU)."""
    code = os.path.abspath(ehign_dir)
    if not os.path.isfile(os.path.join(code, "EHIGN.py")):
        sys.exit("ERROR: %s does not look like the EHIGN_PLA repository (EHIGN.py missing)" % ehign_dir)
    sys.path.insert(0, code)
    warnings.filterwarnings("ignore")
    os.environ.setdefault("DGLBACKEND", "pytorch")
    import torch
    import dgl.function as fn
    from rdkit import RDLogger
    RDLogger.DisableLog("rdApp.*")
    # NIGConv.py uses dgl.function.copy_src, removed in DGL 1.0; copy_u is the
    # same message function under its new name.
    if not hasattr(fn, "copy_src"):
        fn.copy_src = fn.copy_u
    from EHIGN import DTIPredictor
    import graph_constructor
    ckpts = sorted(glob.glob(os.path.join(code, "model", "*_EHIGN_repeat*", "model", "*.pt")))
    if len(ckpts) != 3:
        sys.exit("ERROR: expected 3 checkpoints in %s, found %d" % (os.path.join(code, "model"), len(ckpts)))
    nets = []
    for i in models:
        net = DTIPredictor(node_feat_size=35, edge_feat_size=17, hidden_feat_size=256, layer_num=3)
        net.load_state_dict(torch.load(ckpts[i], map_location="cpu"))
        net.eval()
        nets.append(net)
    return torch, nets, graph_constructor


def prepare(protein_pdb, ligand_mol2, work, code="lig"):
    """Pocket + ligand as RDKit molecules, exactly as the authors' preprocess_complex.py."""
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


def score(torch, nets, gc, ligand, pocket, work):
    """List of pKd, one per loaded model (mean of the two model heads, as test.py)."""
    import dgl
    cpath = os.path.join(work, "complex.rdkit")
    gpath = os.path.join(work, "graph.dgl")
    with open(cpath, "wb") as f:
        pickle.dump((ligand, pocket), f)
    gc.mols2graphs(cpath, 0.0, gpath, dis_threshold=DISTANCE)
    if not os.path.isfile(gpath):  # the authors' function hides the error and saves nothing
        raise RuntimeError("graph construction failed (no contacts within 5 A, or NaN edge features)")
    out = []
    with torch.no_grad():
        for n in nets:
            g, _ = torch.load(gpath)  # reload: the model overwrites the node features in place
            lp, pl = n(dgl.batch([g]))
            out.append(float(((lp + pl) / 2).view(-1)[0]))
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--ehign-dir", required=True, help="EHIGN_PLA repository folder (contains EHIGN.py)")
    ap.add_argument("-d", "--directory", required=True, help="folder with one sub-folder per complex")
    ap.add_argument("-o", "--output", default="predictions.csv", help="output CSV (default: predictions.csv)")
    ap.add_argument("--model", choices=("0", "1", "2", "all"), default="all",
                    help="trained model to use: 0, 1, 2 or all (mean of the three, default)")
    args = ap.parse_args()

    models = (0, 1, 2) if args.model == "all" else (int(args.model),)
    torch, nets, gc = load(args.ehign_dir, models)
    tmp = tempfile.mkdtemp(prefix="ehign_")
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
            preds = score(torch, nets, gc, ligand, pocket, work)
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
