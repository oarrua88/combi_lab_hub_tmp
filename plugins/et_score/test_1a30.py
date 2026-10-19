"""ET-Score installation test using the CASF-2016 core-set complex 1a30.

What it checks
  1. The 1a30 features computed on your machine are identical to the features
     published by the ET-Score authors (Files.7z/features.xlsx).
  2. If the trained model (et_score.sav) is given, the predicted pKd matches the
     authors' reference prediction (5.684). The experimental value is 4.30.

Usage (inside the et-score environment)
  python test_1a30.py --et-dir <ET_Score folder> --complex <...\\coreset\\1a30> [--model <et_score.sav>]

Exit code 0 = PASS, 1 = FAIL.
"""
import argparse
import os
import shutil
import subprocess
import sys
import tempfile

import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
REF_FEATURES = os.path.join(HERE, "reference", "1a30_features.csv")
REF_PREDICTION = 5.6837   # authors' prediction for 1a30 (Files.7z/prediction.xlsx)
EXPERIMENTAL_PKD = 4.30   # CASF-2016 CoreSet.dat, Ki = 50 uM
TOL = 0.01


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--et-dir", required=True, help="folder with predict.py and generate_feature.py")
    ap.add_argument("--complex", required=True, help="CASF-2016 folder of complex 1a30")
    ap.add_argument("--model", help="path to et_score.sav (optional: without it only features are tested)")
    args = ap.parse_args()

    et_dir = os.path.abspath(args.et_dir)
    src = os.path.abspath(args.complex)
    ligand = os.path.join(src, "1a30_ligand.mol2")
    protein = os.path.join(src, "1a30_protein.pdb")
    for f in (os.path.join(et_dir, "predict.py"), ligand, protein):
        if not os.path.isfile(f):
            sys.exit("ERROR: file not found: " + f)
    if args.model and not os.path.isfile(args.model):
        sys.exit("ERROR: model not found: " + args.model)

    # ET-Score reads the FIRST .mol2 and .pdb it finds in each folder, and the
    # CASF folder also has 1a30_ligand_opt.mol2 and 1a30_pocket.pdb.
    # So we copy only the two correct files into a clean working folder.
    work = tempfile.mkdtemp(prefix="et_score_test_")
    cdir = os.path.join(work, "structures", "1a30")
    os.makedirs(cdir)
    shutil.copy(ligand, cdir)
    shutil.copy(protein, cdir)
    print("Working folder:", work)

    ok = True
    sys.path.insert(0, et_dir)
    import predict as P  # ET-Score settings: feature names, atom types, cutoff 12 A, exponent 2

    if args.model:
        print("Running predict.py ...")
        cmd = [sys.executable, os.path.join(et_dir, "predict.py"),
               "-m", os.path.abspath(args.model), "-d", "structures", "-f", "features.xlsx"]
        subprocess.check_call(cmd, cwd=work)
    else:
        print("No model given: computing features only ...")
        from generate_feature import FeatureGeneration
        FeatureGeneration(os.path.join(work, "structures"), P.atoms_list, P.amino_acid_class_names,
                          P.amino_acid_class, P.exp, P.cutoff, os.path.join(work, "features.xlsx")).compute()

    # 1) features
    mine = pd.read_excel(os.path.join(work, "features.xlsx"), index_col=0)
    mine = mine.reindex(columns=P.features).fillna(0.0).loc["1a30"]
    ref = pd.read_csv(REF_FEATURES, index_col=0)["value"].reindex(P.features).fillna(0.0)
    diff = (mine - ref).abs()
    n_bad = int((diff > TOL).sum())
    print("\n[1] Features: %d non-zero (reference %d), max difference %.4f"
          % ((mine != 0).sum(), (ref != 0).sum(), diff.max()))
    if n_bad:
        ok = False
        print("    FAIL - %d features differ, e.g.:" % n_bad)
        print(diff[diff > TOL].sort_values(ascending=False).head(10).to_string())
    else:
        print("    PASS - identical to the authors' features")

    # 2) prediction
    if args.model:
        pred = float(pd.read_excel(os.path.join(work, "prediction.xlsx"), index_col=0).loc["1a30", "prediction"])
        print("\n[2] Predicted pKd 1a30: %.4f (reference %.4f, experimental %.2f)"
              % (pred, REF_PREDICTION, EXPERIMENTAL_PKD))
        if abs(pred - REF_PREDICTION) <= TOL:
            print("    PASS - matches the authors' prediction")
        else:
            ok = False
            print("    FAIL - check that the package versions match environment.yml")
    else:
        print("\n[2] Prediction skipped (use --model et_score.sav)")

    print("\nRESULT:", "PASS" if ok else "FAIL")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
