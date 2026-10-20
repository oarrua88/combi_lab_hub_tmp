"""Sfcnn installation test with complex 1a30 (HIV-1 protease).

What it checks (all against results published by the Sfcnn authors)
  1. CASF-2016 complex 1a30 gives pKd 5.4721, the value in the authors'
     Sfcnn/Sfcnn_2016_test.csv (their CASF-2016 predictions).
  2. Optionally (--decoys), the 74 docking poses in the authors' test/1a30_decoys.mol2
     give the same scores as the authors' test/output2.
The experimental value of 1a30 is 4.30.

Usage (inside the sfcnn environment)
  python test_1a30.py --sfcnn-dir <Sfcnn folder> --complex <...\\coreset\\1a30> [--decoys]

Exit code 0 = PASS, 1 = FAIL.
"""
import argparse
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import predict_sfcnn as W  # noqa: E402

REF_1A30 = 5.4721        # authors' Sfcnn/Sfcnn_2016_test.csv
EXPERIMENTAL_PKD = 4.30
TOL = 0.01


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--sfcnn-dir", required=True, help="Sfcnn folder (with predict.py, weights and test/)")
    ap.add_argument("--complex", required=True, help="CASF-2016 folder of complex 1a30")
    ap.add_argument("--decoys", action="store_true", help="also score the authors' 74 docking poses of 1a30")
    args = ap.parse_args()

    sdir = os.path.abspath(args.sfcnn_dir)
    protein = os.path.join(os.path.abspath(args.complex), "1a30_protein.pdb")
    ligand = os.path.join(os.path.abspath(args.complex), "1a30_ligand.mol2")
    for f in (os.path.join(sdir, "predict.py"), os.path.join(sdir, "weights_22_112-0.0083.h5"), protein, ligand):
        if not os.path.isfile(f):
            sys.exit("ERROR: file not found: " + f)

    print("Loading model ...")
    S, model = W.load_model(sdir)
    prot = W.read(protein)[0]
    ok = True

    pred = float(S.predict(prot, W.read(ligand)[0], model).ravel()[0])
    good = abs(pred - REF_1A30) <= TOL
    ok = ok and good
    print("\n[1] Predicted pKd 1a30: %.4f (authors %.4f, experimental %.2f)" % (pred, REF_1A30, EXPERIMENTAL_PKD))
    print("    PASS - matches the authors' prediction" if good else
          "    FAIL - check the Open Babel and TensorFlow versions (environment.yml)")

    if args.decoys:
        ref = [float(x) for x in open(os.path.join(sdir, "test", "output2")).read().splitlines()[1:] if x.strip()]
        mine = [float(S.predict(prot, lig, model).ravel()[0]) for lig in W.read(os.path.join(sdir, "test", "1a30_decoys.mol2"))]
        diff = max(abs(a - b) for a, b in zip(mine, ref)) if len(mine) == len(ref) else float("inf")
        good = diff <= TOL
        ok = ok and good
        print("\n[2] 1a30 docking poses: %d scored (authors %d), max difference %.4f" % (len(mine), len(ref), diff))
        print("    PASS - matches the authors' test/output2" if good else "    FAIL - differs from test/output2")

    print("\nRESULT:", "PASS" if ok else "FAIL")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
