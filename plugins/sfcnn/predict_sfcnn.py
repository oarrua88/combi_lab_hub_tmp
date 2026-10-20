"""Predict binding affinity (pKd) with Sfcnn (Wang et al., 2022) for many complexes.

Reuses the authors' predict.py (grid featurization + 3D CNN). The trained
weights (weights_22_112-0.0083.h5, 5.5 MB) ship with the authors' repository.
Their build_model() loads the weights from the CURRENT folder, so this wrapper
changes into the Sfcnn folder while building the model.

Usage (inside the sfcnn environment)
  python predict_sfcnn.py --sfcnn-dir <Sfcnn folder> -d <complexes folder> [-o predictions.csv]

Each complex needs its own folder with <code>_protein.pdb and <code>_ligand.mol2
(or .sdf / .pdb). CASF-2016 folders work as they are.
"""
import argparse
import os
import sys
from contextlib import contextmanager

os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "2")
os.environ["CUDA_VISIBLE_DEVICES"] = "-1"

import pandas as pd


@contextmanager
def cwd(path):
    old = os.getcwd()
    os.chdir(path)
    try:
        yield
    finally:
        os.chdir(old)


def load_model(sfcnn_dir):
    """Import the authors' predict.py and build the model with their weights."""
    sfcnn_dir = os.path.abspath(sfcnn_dir)
    sys.path.insert(0, sfcnn_dir)
    import predict as S
    with cwd(sfcnn_dir):
        model = S.build_model()
    return S, model


def read(path, fmt=None):
    from openbabel import pybel
    fmt = fmt or os.path.splitext(path)[1][1:].lower()
    return list(pybel.readfile(fmt, path))


def find_ligand(folder, code):
    for ext in ("mol2", "sdf", "pdb"):
        f = os.path.join(folder, "%s_ligand.%s" % (code, ext))
        if os.path.isfile(f):
            return f
    return None


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--sfcnn-dir", required=True, help="Sfcnn folder (with predict.py and weights_22_112-0.0083.h5)")
    ap.add_argument("-d", "--directory", required=True, help="folder with one sub-folder per complex")
    ap.add_argument("-o", "--output", default="predictions.csv", help="output CSV (default: predictions.csv)")
    args = ap.parse_args()

    S, model = load_model(args.sfcnn_dir)
    rows = []
    for code in sorted(os.listdir(args.directory)):
        folder = os.path.join(args.directory, code)
        protein = os.path.join(folder, code + "_protein.pdb")
        ligand = find_ligand(folder, code) if os.path.isdir(folder) else None
        if not os.path.isfile(protein) or ligand is None:
            continue
        pred = float(S.predict(read(protein)[0], read(ligand)[0], model).ravel()[0])
        rows.append((code, round(pred, 4)))
        print("%s\t%.4f" % (code, pred))
    if not rows:
        sys.exit("ERROR: no complexes found in " + args.directory)
    pd.DataFrame(rows, columns=["pdbid", "pKd_predicted"]).to_csv(args.output, index=False)
    print("Done: %d complexes -> %s" % (len(rows), os.path.abspath(args.output)))


if __name__ == "__main__":
    main()
