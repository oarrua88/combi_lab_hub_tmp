"""DeepRLI (Lin et al., Digital Discovery 2025) - batch prediction for CombiLabHUB.

Scores a folder of protein-ligand complexes with the authors' trained model
(trained_model.state_dict.pth, GitHub release v1.0.2) using the authors' own
preprocessing (deeprli.datasets.ComplexDataset) and model (deeprli.model.DeepRLI).

Input layout (CASF-2016 style, one sub-folder per complex):
    <folder>/<code>/<code>_protein.pdb      full protein (the pocket is cut by DeepRLI, 6.5 A)
    <folder>/<code>/<code>_ligand.sdf       ligand, tried first (authors' order: sdf, mol2)
    <folder>/<code>/<code>_ligand.mol2      used when RDKit cannot read the .sdf

DeepRLI has three read-out heads. The "scoring" head predicts the binding free
energy DeltaG in kcal/mol (the training target). It is converted to pKd with
pKd = -DeltaG / (ln(10) * R * T), T = 298.15 K, which is the relation used in
the authors' data (example index: pKd 5.70 <-> DeltaG -7.77).

Output CSV columns:
    pdbid, pKd_predicted, DeltaG_predicted, docking_score, screening_score, ligand_file

Usage (inside the deeprli environment, DGLBACKEND=pytorch):
    python predict_deeprli.py --deeprli-dir <DeepRLI repo> --model <trained_model.state_dict.pth>
                              -d <folder of complexes> -o predictions.csv
"""
import argparse
import logging
import math
import os
import shutil
import sys
import tempfile
import time

os.environ.setdefault("DGLBACKEND", "pytorch")

MODEL_MD5 = "334ada642693c0f68a8b0305e77f0a29"
LN10_RT = math.log(10) * 1.987204e-3 * 298.15   # kcal/mol, = 1.3643
LIGAND_TYPES = ["sdf", "mol2"]                   # authors' README order
DIST_CUTOFF = 6.5                                # authors' default


def md5(path):
    import hashlib
    h = hashlib.md5()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def find_complexes(folder, protein_suffix="_protein.pdb"):
    """Return [(code, protein, {ext: ligand path})] for every sub-folder with a protein and a ligand."""
    out = []
    for code in sorted(os.listdir(folder)):
        d = os.path.join(folder, code)
        if not os.path.isdir(d):
            continue
        prot = os.path.join(d, code + protein_suffix)
        ligs = {ext: os.path.join(d, "%s_ligand.%s" % (code, ext)) for ext in LIGAND_TYPES}
        ligs = {k: v for k, v in ligs.items() if os.path.isfile(v)}
        if os.path.isfile(prot) and ligs:
            out.append((code, prot, ligs))
    return out


def load(deeprli_dir, model_path, check_md5=True):
    """Import the authors' package and load the trained model on CPU (weights only)."""
    src = os.path.join(os.path.abspath(deeprli_dir), "src")
    if not os.path.isdir(os.path.join(src, "deeprli")):
        sys.exit("ERROR: %s does not look like the DeepRLI repository (no src/deeprli)" % deeprli_dir)
    if src not in sys.path:
        sys.path.insert(0, src)
    import torch
    from deeprli.model import DeepRLI

    if not os.path.isfile(model_path):
        sys.exit("ERROR: model not found: " + model_path)
    if check_md5 and md5(model_path) != MODEL_MD5:
        sys.exit("ERROR: MD5 of %s is not %s (wrong or corrupted download)" % (model_path, MODEL_MD5))

    # Hyper-parameters = defaults of the authors' infer.heavy.py
    model = DeepRLI(f_dropout_rate=0.0, g_dropout_rate=0.0, hidden_dim=64, num_attention_heads=8,
                    use_layer_norm=False, use_batch_norm=True, use_residual=True,
                    use_envelope=True, use_multi_obj=True)
    state = torch.load(model_path, map_location="cpu", weights_only=True)
    model.load_state_dict(state)
    model.eval()
    return torch, model


def score_complexes(torch, model, complexes, workdir=None, batch=16, keep=False):
    """Preprocess with the authors' ComplexDataset and score. Returns a list of dicts."""
    import pandas as pd
    from deeprli.datasets import ComplexDataset, HeavyDatasetForInfer

    root = workdir or tempfile.mkdtemp(prefix="deeprli_")
    raw = os.path.join(root, "raw")
    os.makedirs(os.path.join(root, "index"), exist_ok=True)
    rows = []
    for code, prot, ligs in complexes:
        d = os.path.join(raw, code)
        os.makedirs(d, exist_ok=True)
        shutil.copyfile(prot, os.path.join(d, "receptor.pdb"))
        for ext, path in ligs.items():
            shutil.copyfile(path, os.path.join(d, "ligand." + ext))
        rows.append({"complex_path": code})
    pd.DataFrame(rows).to_csv(os.path.join(root, "index", "data.csv"), index=False)

    logging.getLogger("deeprli").setLevel(logging.WARNING)
    ComplexDataset(root=root, data_index="index/data.csv", ligand_file_types=LIGAND_TYPES,
                   dist_cutoff=DIST_CUTOFF)
    processed_index = os.path.join(root, "index", "data.processed.csv")
    data = HeavyDatasetForInfer(root=root, data_index="index/data.processed.csv",
                                data_file="compiled/data.processed.pkl")
    codes = list(pd.read_csv(processed_index)["complex_path"].astype(str))

    loader = torch.utils.data.DataLoader(data, batch_size=batch, collate_fn=HeavyDatasetForInfer.collate_fn,
                                         num_workers=0)
    preds = [[], [], []]
    with torch.no_grad():
        for b in loader:
            res = model(b)
            for i in range(3):
                preds[i].extend(res[i].reshape(-1).tolist())

    used = {}
    for code in codes:
        for ext in LIGAND_TYPES:   # ComplexDataset keeps the first ligand file RDKit can read
            p = os.path.join(raw, code, "ligand." + ext)
            if os.path.isfile(p) and _readable(p, ext):
                used[code] = ext
                break

    out = []
    for code, dg, dock, scr in zip(codes, *preds):
        out.append({"pdbid": code, "pKd_predicted": -dg / LN10_RT, "DeltaG_predicted": dg,
                    "docking_score": dock, "screening_score": scr,
                    "ligand_file": "%s_ligand.%s" % (code, used.get(code, "?"))})
    missing = sorted(set(c for c, _, _ in complexes) - set(codes))
    if not keep and workdir is None:
        shutil.rmtree(root, ignore_errors=True)
    return out, missing


def _readable(path, ext):
    from rdkit import Chem, RDLogger
    RDLogger.DisableLog("rdApp.*")
    if ext == "sdf":
        m = Chem.SDMolSupplier(path)[0]
    else:
        m = Chem.MolFromMol2File(path)
    return m is not None


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--deeprli-dir", required=True, help="DeepRLI repository (with src/deeprli)")
    ap.add_argument("--model", help="trained_model.state_dict.pth (default: <deeprli-dir>/trained_model.state_dict.pth)")
    ap.add_argument("-d", "--dir", required=True, help="folder with one sub-folder per complex")
    ap.add_argument("-o", "--out", default="predictions.csv", help="output CSV")
    ap.add_argument("--batch", type=int, default=16)
    ap.add_argument("--workdir", help="keep DeepRLI's intermediate files here (default: temporary folder)")
    args = ap.parse_args()

    model_path = args.model or os.path.join(args.deeprli_dir, "trained_model.state_dict.pth")
    torch, model = load(args.deeprli_dir, model_path)
    torch.set_num_threads(max(1, os.cpu_count() or 1))

    complexes = find_complexes(args.dir)
    if not complexes:
        sys.exit("ERROR: no complexes found in " + args.dir)
    print("DeepRLI: %d complexes in %s" % (len(complexes), args.dir))
    t0 = time.time()
    out, missing = score_complexes(torch, model, complexes, workdir=args.workdir, batch=args.batch)
    dt = time.time() - t0

    import pandas as pd
    os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
    pd.DataFrame(out).to_csv(args.out, index=False, float_format="%.6f")
    print("Scored %d complexes in %.1f s -> %s" % (len(out), dt, args.out))
    if missing:
        print("WARNING: %d complexes could not be processed (no readable ligand/protein): %s"
              % (len(missing), ", ".join(missing)))


if __name__ == "__main__":
    main()
