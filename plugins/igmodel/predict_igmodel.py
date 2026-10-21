"""IGModel - batch prediction for a folder of protein-ligand complexes (CPU).

IGModel (Wang et al., Brief. Bioinform. 2024) predicts both the RMSD of a ligand pose
and the binding affinity (pKd) from a pocket graph and a protein-ligand interaction
graph. This wrapper reuses the authors' scripts/ (ReceptorFile, PocketFeatures,
LigandFeature, ComplexGraph, model) unchanged and only adds:
  * one model load for all complexes, a temporary folder per complex;
  * the crystal ligand as both the pocket reference and the scored pose
    (the authors' "reference ligand" mode with models/saved_model.pth);
  * the ligand read from <code>_ligand.mol2 (RDKit cannot read several CASF-2016
    .sdf files, 1a30 among them); .sdf is used only if there is no .mol2;
  * the real error message when a complex fails (the authors' script prints only "Error").

Each complex folder must contain <code>_protein.pdb and <code>_ligand.mol2 (or .sdf).

Usage (inside the igmodel environment)
  python predict_igmodel.py --ig-dir <IGModel folder> -d <complexes folder> [-o predictions.csv]
"""
import argparse
import os
import shutil
import sys
import tempfile
import traceback
import warnings

os.environ.setdefault("DGLBACKEND", "pytorch")
warnings.filterwarnings("ignore")

import numpy as np
import pandas as pd

MODELS = {"ref": "saved_model.pth", "self-ref": "self-ref_model.pth"}


def load(ig_dir, mode="ref"):
    """Import the authors' modules and load the pickled model (needs scripts/ on sys.path)."""
    sys.path.insert(0, os.path.join(ig_dir, "scripts"))
    import torch
    import model as _m  # noqa: F401  (classes needed to unpickle the model)
    path = os.path.join(ig_dir, "models", MODELS[mode])
    try:
        net = torch.load(path, map_location="cpu", weights_only=False)
    except TypeError:                       # torch < 1.13 has no weights_only
        net = torch.load(path, map_location="cpu")
    net.eval()
    return net


def find_ligand(folder, code):
    for ext in (".mol2", ".sdf"):
        f = os.path.join(folder, code + "_ligand" + ext)
        if os.path.isfile(f):
            return f
    raise FileNotFoundError("no %s_ligand.mol2/.sdf in %s" % (code, folder))


def score_poses(net, protein, pose_file, ref_file=None, work=None):
    """Score every pose in pose_file. Returns a DataFrame (pose, pred_rmsd, pred_pkd)."""
    import dgl
    from dgl.dataloading import GraphDataLoader
    from rdkit import Chem
    from ligand_features import LigandFeature
    from load_receptor import ReceptorFile
    from pocket_features import PocketFeatures
    from cplx_graph import ComplexGraph
    from utils import run_an_eval_epoch, sdf_split, mol2_split

    own_tmp = work is None
    work = work or tempfile.mkdtemp(prefix="igmodel_")
    try:
        is_sdf = pose_file.lower().endswith(".sdf")
        names, blocks = (sdf_split if is_sdf else mol2_split)(pose_file)
        rec, pock_g = None, None
        if ref_file:
            rec = ReceptorFile(rec_fpath=protein, ref_lig_fpath=ref_file, temp_dpath=work)
            rec.clip_rec()
            rec.define_pocket()
            pock_g = dgl.add_self_loop(PocketFeatures(rec, pock_center=rec.pock_center).pock_to_graph())
        keys, cplx = [], []
        for i, block in enumerate(blocks):
            mol = Chem.MolFromMolBlock(block) if is_sdf else Chem.MolFromMol2Block(block)
            if mol is None:
                raise ValueError("RDKit cannot read pose %d of %s" % (i + 1, pose_file))
            lig = LigandFeature(mol=mol)
            lig.lig_to_graph()
            if pock_g is None:                      # self-reference mode: pocket from the first pose
                rec = ReceptorFile(rec_fpath=protein, ref_lig_fpath=None, temp_dpath=work)
                rec.parse_ref_coords(lig.pose_ha_xyz)
                rec.clip_rec()
                rec.define_pocket()
                pock_g = dgl.add_self_loop(PocketFeatures(rec, pock_center=rec.pock_center).pock_to_graph())
            cplx.append(ComplexGraph(rec, lig).get_cplx_graph())
            keys.append("%s-%d" % (names[i], i + 1))

        class DS:
            def __getitem__(self, idx):
                return idx, pock_g, cplx[idx]

            def __len__(self):
                return len(cplx)

        rmsd, pkd = run_an_eval_epoch(net, GraphDataLoader(DS(), batch_size=32, shuffle=False), device="cpu")
        return pd.DataFrame({"pose": keys, "pred_rmsd": np.asarray(rmsd).reshape(-1),
                             "pred_pkd": np.asarray(pkd).reshape(-1)})
    finally:
        if own_tmp:
            shutil.rmtree(work, ignore_errors=True)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--ig-dir", required=True, help="IGModel folder (with scripts/ and models/)")
    ap.add_argument("-d", "--directory", required=True, help="folder with one sub-folder per complex")
    ap.add_argument("-o", "--output", default="predictions.csv", help="output CSV (default: predictions.csv)")
    ap.add_argument("--mode", choices=("ref", "self-ref"), default="ref",
                    help="ref = crystal ligand defines the pocket, saved_model.pth (default); "
                         "self-ref = pose defines the pocket, self-ref_model.pth")
    a = ap.parse_args()
    ig = os.path.abspath(a.ig_dir)
    net = load(ig, a.mode)
    root = os.path.abspath(a.directory)
    codes = sorted(d for d in os.listdir(root) if os.path.isdir(os.path.join(root, d)))
    rows = []
    for n, code in enumerate(codes, 1):
        folder = os.path.join(root, code)
        try:
            lig = find_ligand(folder, code)
            df = score_poses(net, os.path.join(folder, code + "_protein.pdb"), lig,
                             ref_file=lig if a.mode == "ref" else None)
            rows.append((code, round(float(df.pred_pkd.iloc[0]), 4), round(float(df.pred_rmsd.iloc[0]), 4), ""))
            print("[%d/%d] %s  pKd %.4f" % (n, len(codes), code, rows[-1][1]))
        except Exception as e:                       # noqa: BLE001
            rows.append((code, None, None, str(e).splitlines()[0][:200]))
            print("[%d/%d] %s  ERROR: %s" % (n, len(codes), code, rows[-1][3]))
            if os.environ.get("IGMODEL_DEBUG"):
                traceback.print_exc()
    out = pd.DataFrame(rows, columns=["pdbid", "pKd_predicted", "pred_rmsd", "error"])
    os.makedirs(os.path.dirname(os.path.abspath(a.output)), exist_ok=True)
    out.to_csv(a.output, index=False)
    print("Done: %d complexes (%d errors) -> %s" % (len(out), out.pKd_predicted.isna().sum(), a.output))


if __name__ == "__main__":
    main()
