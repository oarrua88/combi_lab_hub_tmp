"""delta_LinF9_XGB installation test (Linux / Docker / WSL).

  [1] The authors' example test/1e66_wat must give 8.9115 (our value). The authors'
      README prints 8.893: the 0.019 difference comes from 4 of the 92 features (3
      smina terms and the AlphaSpace beta score), which depend on the MGLTools /
      AlphaSpace versions (see INSTALL.md, note 3).
  [2] CASF-2016 complex 1a30 must give pKd 5.1582. 88 of its 92 features, and the Lin_F9
      score (3.6566), are identical to the features the authors publish for 1a30 in
      dataset/test_set.csv; with their 4 other values the prediction would be 5.1792.
      The experimental value of 1a30 is 4.30.

Usage (inside the dlinf9 environment)
  python test_1a30.py --dl-dir <delta_LinF9_XGB folder> --complex <.../coreset/1a30> [--adt ...] [--msms ...]

Exit code 0 = PASS, 1 = FAIL.
"""
import argparse
import os
import shutil
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import predict_delta_linf9_xgb as W  # noqa: E402

REF_1E66 = 8.9115
README_1E66 = 8.893
REF_1A30 = 5.1582
AUTHORS_FEATURES_1A30 = 5.1792
EXPERIMENTAL_PKD = 4.30
TOL = 0.01


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dl-dir", required=True, help="delta_LinF9_XGB folder (script/, software/, saved_model/, test/)")
    ap.add_argument("--complex", required=True, help="CASF-2016 folder of complex 1a30")
    ap.add_argument("--adt", help="MGLTools prepare_receptor4.py")
    ap.add_argument("--msms", help="msms executable")
    a = ap.parse_args()
    dl = os.path.abspath(a.dl_dir)
    cx = os.path.abspath(a.complex)
    t1 = os.path.join(dl, "test", "1e66_wat")
    need = [os.path.join(t1, "1e66_protein.pdb"), os.path.join(t1, "1e66_ligand.mol2"),
            os.path.join(cx, "1a30_protein.pdb"), os.path.join(cx, "1a30_ligand.mol2")]
    for f in need:
        if not os.path.isfile(f):
            sys.exit("ERROR: file not found: " + f)
    tmp = tempfile.mkdtemp(prefix="dlinf9_test_")
    ok = True
    try:
        mod = W.setup(dl, a.adt, a.msms, tmp)
        print("Scoring the authors' example 1e66_wat ...")
        v = W.predict_one(mod, need[0], need[1], os.path.join(tmp, "1e66"))
        good = abs(v - REF_1E66) <= TOL
        ok = ok and good
        print("\n[1] 1e66_wat: %.4f (reference %.4f; authors' README %.3f)" % (v, REF_1E66, README_1E66))
        print("    PASS" if good else "    FAIL - check MGLTools, MSMS, RDKit, Open Babel and xgboost (environment files)")

        print("\nScoring 1a30 ...")
        v = W.predict_one(mod, need[2], need[3], os.path.join(tmp, "1a30"))
        good = abs(v - REF_1A30) <= TOL
        ok = ok and good
        print("\n[2] Predicted pKd 1a30: %.4f (reference %.4f; with the authors' published features %.4f; experimental %.2f)"
              % (v, REF_1A30, AUTHORS_FEATURES_1A30, EXPERIMENTAL_PKD))
        print("    PASS" if good else "    FAIL - the CASF-2016 pipeline gives a different value")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    print("\nRESULT: %s" % ("PASS" if ok else "FAIL"))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
