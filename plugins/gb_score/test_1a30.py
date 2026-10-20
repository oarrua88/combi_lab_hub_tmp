"""GB-Score installation test using the CASF-2016 core-set complex 1a30.

What it checks
  1. The 400 raw features of 1a30 computed on your machine are identical to the
     CombiLabHUB reference (reference/1a30_features.csv). For information it also
     shows how close they are to the features published by the GB-Score authors
     (reference/1a30_features_authors.csv, from total_set_2019.csv on Figshare);
     small protein-H differences (< 0.2) come from the PDBbind version of the files.
  2. If the trained model (gb_score.joblib) is given, the predicted pKd matches the
     reference prediction (reference/1a30_prediction.txt, 5.6171).
     The experimental value is 4.30.

Usage (inside the gb-score environment)
  python test_1a30.py --gb-dir <GB_Score folder> --complex <...\\coreset\\1a30> [--model <gb_score.joblib>]

Exit code 0 = PASS, 1 = FAIL.
"""
import argparse
import os
import shutil
import sys
import tempfile

import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import predict_gb_score as PG  # noqa: E402

REF_FEATURES = os.path.join(HERE, "reference", "1a30_features.csv")
AUTHORS_FEATURES = os.path.join(HERE, "reference", "1a30_features_authors.csv")
EXPERIMENTAL_PKD = 4.30   # CASF-2016 CoreSet.dat, Ki = 50 uM
TOL = 0.01


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--gb-dir", required=True, help="folder with the authors' generate_features.py")
    ap.add_argument("--complex", required=True, help="CASF-2016 folder of complex 1a30")
    ap.add_argument("--model", help="path to gb_score.joblib (optional: without it only features are tested)")
    args = ap.parse_args()

    gb_dir = os.path.abspath(args.gb_dir)
    src = os.path.abspath(args.complex)
    ligand = os.path.join(src, "1a30_ligand.mol2")
    protein = os.path.join(src, "1a30_protein.pdb")
    for f in (os.path.join(gb_dir, "generate_features.py"), ligand, protein):
        if not os.path.isfile(f):
            sys.exit("ERROR: file not found: " + f)
    if args.model and not os.path.isfile(args.model):
        sys.exit("ERROR: model not found: " + args.model)

    # generate_features.py reads the FIRST .mol2 and .pdb in each folder, and the
    # CASF folder also has 1a30_ligand_opt.mol2 and 1a30_pocket.pdb.
    work = tempfile.mkdtemp(prefix="gb_score_test_")
    cdir = os.path.join(work, "structures", "1a30")
    os.makedirs(cdir)
    shutil.copy(ligand, cdir)
    shutil.copy(protein, cdir)
    print("Working folder:", work)

    ok = True
    print("Computing features ...")
    raw = PG.compute_features(gb_dir, os.path.join(work, "structures"), os.path.join(work, "features.csv"))

    # 1) features
    ref = pd.read_csv(REF_FEATURES, index_col=0)["value"]
    mine = raw.loc["1a30"].reindex(ref.index)
    diff = (mine - ref).abs()
    n_bad = int((diff > TOL).sum())
    print("\n[1] Features: %d non-zero (reference %d), max difference %.4f"
          % ((mine != 0).sum(), (ref != 0).sum(), diff.max()))
    if n_bad:
        ok = False
        print("    FAIL - %d features differ, e.g.:" % n_bad)
        print(diff[diff > TOL].sort_values(ascending=False).head(10).to_string())
    else:
        print("    PASS - identical to the CombiLabHUB reference")
    auth = pd.read_csv(AUTHORS_FEATURES, index_col=0)["value"]
    print("    (info) max difference vs the authors' published features: %.3f"
          % (mine.reindex(auth.index) - auth).abs().max())

    # 2) prediction
    if args.model:
        ref_pred = float(open(os.path.join(HERE, "reference", "1a30_prediction.txt")).read().split()[0])
        print("\nLoading model (about 600 MB, takes a moment) ...")
        from joblib import load
        model = load(args.model)
        x = PG.preprocess(raw, PG.DEFAULT_PREP)
        pred = float(model.predict(x.loc[["1a30"]].values)[0])
        print("\n[2] Predicted pKd 1a30: %.4f (reference %.4f, experimental %.2f)"
              % (pred, ref_pred, EXPERIMENTAL_PKD))
        if abs(pred - ref_pred) <= TOL:
            print("    PASS - matches the reference prediction")
        else:
            ok = False
            print("    FAIL - check that the package versions match environment.yml")
    else:
        print("\n[2] Prediction skipped (use --model gb_score.joblib)")

    print("\nRESULT:", "PASS" if ok else "FAIL")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
