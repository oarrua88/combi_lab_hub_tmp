"""saCNN installation test with complex 1a30 (HIV-1 protease).

What it checks
  1. The authors' pre-computed features of their example complex 3jvr
     (data/feature/3jvr.h5 in the saCNN repository) give pKd 4.7484. This checks
     the network, the checkpoint and PyTorch.
  2. Our featurisation of 3jvr from its .pdb/.mol2 reproduces the authors'
     3jvr.h5 (max. difference < 1e-4). This checks moleculekit, pdb2pqr and propka.
  3. CASF-2016 1a30 (1a30_protein.pdb + 1a30_ligand.mol2) gives pKd 5.0950, the
     value Eaves et al. obtained (casf2016_saCNN_preds_and_times.csv in
     github.com/jeavesj/saCNN). The experimental value is 4.30.

Usage (inside the sacnn environment)
  python test_1a30.py --sacnn-dir <saCNN folder> --complex <...\\coreset\\1a30>

Exit code 0 = PASS, 1 = FAIL.
"""
import argparse
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import predict_sacnn as W  # noqa: E402

REF_3JVR = 4.7484
REF_1A30 = 5.0950
EXPERIMENTAL_PKD = 4.30
TOL = 0.01
FEATURE_TOL = 1e-4


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--sacnn-dir", required=True, help="saCNN folder (with src/ and checkpoint/model.pkl)")
    ap.add_argument("--complex", required=True, help="CASF-2016 folder of complex 1a30")
    args = ap.parse_args()

    sdir = os.path.abspath(args.sacnn_dir)
    casf = os.path.abspath(args.complex)
    h5 = os.path.join(sdir, "data", "feature", "3jvr.h5")
    ex = os.path.join(sdir, "data", "dataset", "3jvr")
    for f in (h5, os.path.join(ex, "3jvr_protein.pdb"), os.path.join(ex, "3jvr_ligand.mol2"),
              os.path.join(casf, "1a30_protein.pdb"), os.path.join(casf, "1a30_ligand.mol2")):
        if not os.path.isfile(f):
            sys.exit("ERROR: file not found: " + f)

    import h5py
    import numpy as np
    torch, model, rot = W.load(sdir)
    ok = True

    with h5py.File(h5, "r") as f:
        authors = f["data"][()][0]
    p = W.score(torch, model, rot, authors)
    good = abs(p - REF_3JVR) <= TOL
    ok = ok and good
    print("[1] Authors' features of 3jvr (data/feature/3jvr.h5): pKd %.4f (reference %.4f)" % (p, REF_3JVR))
    print("    PASS - matches the reference" if good else "    FAIL - check PyTorch / the checkpoint")

    ours, _ = W.featurize(os.path.join(ex, "3jvr_protein.pdb"), os.path.join(ex, "3jvr_ligand.mol2"))
    diff = float(np.abs(ours - authors).max())
    good = diff < FEATURE_TOL
    ok = ok and good
    print("\n[2] Our features of 3jvr vs the authors' 3jvr.h5: max. difference %.2e" % diff)
    print("    PASS - same features" if good else "    FAIL - check moleculekit / pdb2pqr / propka versions")

    data, prep = W.featurize(os.path.join(casf, "1a30_protein.pdb"), os.path.join(casf, "1a30_ligand.mol2"))
    p = W.score(torch, model, rot, data)
    good = abs(p - REF_1A30) <= TOL
    ok = ok and good
    print("\n[3] CASF-2016 1a30 (protein preparation: %s): pKd %.4f (reference %.4f, experimental %.2f)"
          % (prep, p, REF_1A30, EXPERIMENTAL_PKD))
    print("    PASS - matches the reference" if good else "    FAIL - check the package versions (environment.yml)")

    print("\nRESULT:", "PASS" if ok else "FAIL")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
