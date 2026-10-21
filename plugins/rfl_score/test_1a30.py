"""RFL-Score installation test with complex 1a30 (HIV-1 protease).

  [1] Model check (any OS): the authors' Random Forest (scoring_function_160.rda, MD5 checked)
      on the 160 features of their example 1a30 (examples/1a30/1a30_160_input.csv) must give
      pKd 4.4494 (experimental 4.30).
  [2] Full pipeline (--full; Linux / Docker image): the 160 features are computed from the
      CASF-2016 files of 1a30 (+ the authors' FASTA examples/1a30/1A30.fasta.txt) with the
      authors' code and must be identical to their 1a30_160_input.csv, and the prediction
      must again be 4.4494.

Usage
  python test_1a30.py --rfl-dir <rfl-score_v1>                                 (check 1)
  python test_1a30.py --rfl-dir <rfl-score_v1> --complex <...coreset/1a30> --full  (checks 1 and 2)

Exit code 0 = PASS, 1 = FAIL.
"""
import argparse
import hashlib
import os
import shutil
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import predict_rfl_score as W  # noqa: E402

REF_1A30 = 4.4494
EXPERIMENTAL_PKD = 4.30
TOL = 0.0001
MD5 = {W.MODEL: "d1ad344ed3f167e2e053e97dd1f9890e",
       os.path.join("examples", "1a30", "1a30_160_input.csv"): "cc59df3203179361fbcb7d063dfb06dd"}


def md5(path):
    h = hashlib.md5()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--rfl-dir", required=True)
    ap.add_argument("--complex", help="CASF-2016 folder of complex 1a30 (for --full)")
    ap.add_argument("--full", action="store_true", help="also run the full feature pipeline (Linux / Docker)")
    a = ap.parse_args()
    rfl = os.path.abspath(a.rfl_dir)
    for f in MD5:
        if not os.path.isfile(os.path.join(rfl, f)):
            sys.exit("ERROR: file not found: " + os.path.join(rfl, f))
    import pandas as pd
    ok = True
    tmp = tempfile.mkdtemp(prefix="rfl_test_")
    try:
        bad = [f for f, m in MD5.items() if md5(os.path.join(rfl, f)) != m]
        ref_csv = os.path.join(rfl, "examples", "1a30", "1a30_160_input.csv")
        try:
            p = float(W.r_predict(rfl, ref_csv, os.path.join(tmp, "p1.csv")).pKd_predicted[0])
        except Exception as e:                          # noqa: BLE001
            print("[1] ERROR: %s" % e)
            print("\nRESULT: FAIL")
            return 1
        good = not bad and abs(p - REF_1A30) <= TOL
        ok = ok and good
        print("[1] Model + authors' features of 1a30: pKd %.4f (reference %.4f, experimental %.2f); files: %s"
              % (p, REF_1A30, EXPERIMENTAL_PKD, "MD5 OK" if not bad else "WRONG MD5: " + ", ".join(bad)))
        print("    PASS" if good else "    FAIL - check R and the randomForest package (environment.yml)")

        if a.full:
            if not a.complex:
                sys.exit("ERROR: --full needs --complex")
            cx = os.path.join(tmp, "cx", "1a30")
            os.makedirs(cx)
            for f in ("1a30_protein.pdb", "1a30_ligand.mol2"):
                shutil.copy(os.path.join(os.path.abspath(a.complex), f), cx)
            shutil.copy(os.path.join(rfl, "examples", "1a30", "1A30.fasta.txt"), cx)
            print("\nComputing the 160 features of 1a30 (Open Babel, PaDEL, DSSP, MGLTools, vina4dv ...) ...")
            try:
                feats, _ = W.featurize(rfl, [("1a30", cx)], os.path.join(tmp, "work"))
                fcsv = os.path.join(tmp, "f.csv")
                feats.to_csv(fcsv)
                p2 = float(W.r_predict(rfl, fcsv, os.path.join(tmp, "p2.csv")).pKd_predicted[0])
            except Exception as e:                      # noqa: BLE001
                print("\n[2] ERROR: %s" % e)
                print("\nRESULT: FAIL")
                return 1
            ref = pd.read_csv(ref_csv).iloc[0, 1:]
            mine = feats.iloc[0]
            diff = [c for c in ref.index if c not in mine.index or abs(float(mine[c]) - float(ref[c])) > 1e-6 * max(1, abs(float(ref[c])))]
            good = not diff and abs(p2 - REF_1A30) <= TOL
            ok = ok and good
            print("\n[2] Full pipeline: %d of 160 features differ from the authors' 1a30_160_input.csv; pKd %.4f (reference %.4f)"
                  % (len(diff), p2, REF_1A30))
            if diff:
                print("    differing: " + ", ".join(diff[:15]))
            print("    PASS" if good else "    FAIL - check the programs (INSTALL.md, section B)")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    print("\nRESULT: %s" % ("PASS" if ok else "FAIL"))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
