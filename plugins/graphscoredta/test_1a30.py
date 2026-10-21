"""GraphscoreDTA installation test.

GraphscoreDTA cannot score complex 1a30: the authors published their model and the
inputs already built for 279 of the 285 CASF-2016 complexes, but not the code that
builds those inputs, and 1a30 is one of the 6 complexes they left out
(1a30, 2zcr, 2zy1, 3ag9, 3bv9, 3uri).

So this test checks the installation the only way possible:
  [1] says whether 1a30 is in the authors' set (it is not);
  [2] scores the authors' 279 complexes and compares every value with their own
      result/predict_test2016.csv (must match within 0.001).

Usage (inside the gsdta environment)
  python test_1a30.py --gs-dir <GraphscoreDTA folder>

Exit code 0 = PASS, 1 = FAIL.
"""
import argparse
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import predict_graphscoredta as W  # noqa: E402

import numpy as np   # noqa: E402
import pandas as pd  # noqa: E402

TOL = 0.001
PCC_PAPER = 0.831


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--gs-dir", required=True, help="GraphscoreDTA folder (src/, model/, test_set/, result/)")
    ap.add_argument("--complex", help="ignored; accepted so that all CombiLabHUB tests take the same arguments")
    a = ap.parse_args()
    gs = os.path.abspath(a.gs_dir)
    need = [os.path.join(gs, "model", "modelp.pth"),
            os.path.join(gs, "test_set", "all_in_one_graph_test2016.bin"),
            os.path.join(gs, "test_set", "Vina_terms2016.pkl"),
            os.path.join(gs, "result", "predict_test2016.csv")]
    for f in need:
        if not os.path.isfile(f):
            sys.exit("ERROR: file not found: " + f +
                     ("\n  Download it from https://github.com/CSUBioGroup/GraphscoreDTA/releases/tag/Data"
                      if f.endswith(".bin") else ""))

    ids = set(pd.read_csv(os.path.join(gs, "test_set", "labels_test2016.csv"), dtype={"id": str}).id)
    print("[1] Is 1a30 in the authors' pre-processed CASF-2016 set? %s" % ("yes" if "1a30" in ids else "NO"))
    print("    GraphscoreDTA has no public featuriser, so 1a30 cannot be scored (see INSTALL.md).")

    print("\nScoring the authors' %d complexes on CPU ..." % len(ids))
    mine = W.predict(gs)
    ref = pd.read_csv(os.path.join(gs, "result", "predict_test2016.csv"), dtype={"pdbid": str})
    m = mine.merge(ref, on="pdbid")
    diff = float((m.pKd_predicted - m.predicted).abs().max()) if len(m) else float("inf")
    pcc = float(np.corrcoef(m.pKd_predicted, m.real)[0, 1]) if len(m) > 2 else float("nan")
    ok = len(m) == len(ref) == len(mine) and diff <= TOL
    print("\n[2] %d complexes scored, %d in the authors' result file, max difference %.5f" % (len(mine), len(ref), diff))
    print("    PCC on these 279 complexes: %.3f (paper %.3f on CASF-2016)" % (pcc, PCC_PAPER))
    print("    PASS - matches the authors' predictions" if ok else
          "    FAIL - check the PyTorch and DGL versions (environment.yml)")
    print("\nRESULT: %s" % ("PASS" if ok else "FAIL"))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
