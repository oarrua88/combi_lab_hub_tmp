"""MMPD-DTA installation test with complex 1a30 (HIV-1 protease).

What it checks
  1. The trained model result/best/best_model.pt has the expected MD5.
  2. The inputs rebuilt by predict_mmpd_dta.py from the CASF-2016 files
     (1a30_protein.pdb, 1a30_pocket.pdb, 1a30_ligand.mol2) are IDENTICAL to the
     authors' pre-built 1a30 in test2016.pt (data/processed/data.zip): node
     features, edges and their order, and the protein sequence. 1a30 is part of
     the authors' PDBbind2016 test set (experimental pKd 4.30).
  3. The model gives the same pKd with the rebuilt inputs and with the authors'
     ones, and the value is finite.
  4. pKd matches the CombiLabHUB reference REF_PKD (own value: the authors only
     publish metrics for the whole set, not per complex). Recorded on 23/10/2026:
     pKd 5.3879, identical with Windows conda (PyTorch 2.2.2) and Docker (PyTorch 2.3.1).

Usage (inside the mmpd_dta environment)
  python test_1a30.py --mmpd-dir <MMPD-DTA repo> --complex <...\\coreset\\1a30>
                      [--authors-data <test2016.pt>]

Exit code 0 = PASS, 1 = FAIL.
"""
import argparse
import math
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import predict_mmpd_dta as W  # noqa: E402

REF_PKD = 5.3879        # CombiLabHUB reference: 23/10/2026, lab PC, Windows conda AND Docker
EXPERIMENTAL_PKD = 4.30
TOL = 0.01


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--mmpd-dir", required=True, help="MMPD-DTA repository")
    ap.add_argument("--complex", required=True, help="CASF-2016 folder of complex 1a30")
    ap.add_argument("--authors-data", help="authors' test2016.pt (default: <mmpd-dir>/data/processed/test2016.pt)")
    args = ap.parse_args()

    casf = os.path.abspath(args.complex)
    files = [os.path.join(casf, "1a30" + s) for s in ("_protein.pdb", "_pocket.pdb", "_ligand.mol2")]
    for f in files:
        if not os.path.isfile(f):
            sys.exit("ERROR: file not found: " + f)
    model_path = os.path.join(args.mmpd_dir, "result", "best", "best_model.pt")
    test_pt = args.authors_data or os.path.join(args.mmpd_dir, "data", "processed", "test2016.pt")
    ok = True

    good = os.path.isfile(model_path) and W.md5(model_path) == W.MODEL_MD5
    print("[1] Model %s\n    %s" % (model_path, "PASS - MD5 " + W.MODEL_MD5 if good else "FAIL - wrong MD5 or file missing"))
    if not good:
        print("\nRESULT: FAIL")
        sys.exit(1)

    mine = W.build_inputs(*files)
    print("\n[2] Inputs rebuilt from the CASF-2016 files: complex graph %d nodes / %d edges, "
          "ligand graph %d nodes / %d edges, sequence %d residues"
          % (mine["x_s"].shape[0], mine["edge_index_s"].shape[1], mine["x_t"].shape[0],
             mine["edge_index_t"].shape[1], len(mine["sequence"])))
    auth = W.authors_inputs(test_pt, "1a30") if os.path.isfile(test_pt) else None
    if auth is None:
        ok = False
        print("    FAIL - authors' test2016.pt not found (%s); unzip data/processed/data.zip" % test_pt)
    else:
        same = all(np.array_equal(np.asarray(mine[k]), np.asarray(auth[k]))
                   for k in ("x_s", "edge_index_s", "x_t", "edge_index_t", "protein"))
        ok = ok and same
        print("    PASS - identical to the authors' 1a30 in test2016.pt" if same else
              "    FAIL - differs from the authors' graphs (check the RDKit version, environment.yml)")

    torch, model = W.load(args.mmpd_dir, model_path, check_md5=False)
    p_mine = W.predict(torch, model, mine)
    print("\n[3] Prediction with the rebuilt inputs: pKd %.4f (experimental %.2f)" % (p_mine, EXPERIMENTAL_PKD))
    good = math.isfinite(p_mine)
    if auth is not None:
        p_auth = W.predict(torch, model, auth)
        print("    with the authors' inputs:          pKd %.4f" % p_auth)
        good = good and abs(p_auth - p_mine) < 1e-5
    ok = ok and good
    print("    PASS" if good else "    FAIL - not finite or different from the authors' inputs")

    if REF_PKD is None:
        print("\n[4] No reference value recorded yet.")
        print("    Record REF_PKD = %.4f in test_1a30.py after checking the run." % p_mine)
    else:
        good = abs(p_mine - REF_PKD) <= TOL
        ok = ok and good
        print("\n[4] pKd %.4f vs CombiLabHUB reference %.4f" % (p_mine, REF_PKD))
        print("    PASS - matches the reference" if good else "    FAIL - check the package versions (environment.yml)")

    print("\nRESULT:", ("PASS" if ok else "FAIL") + (" (no reference value yet)" if ok and REF_PKD is None else ""))
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
