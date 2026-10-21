"""IGModel installation test.

  [1] The authors' example (samples/1bcu, 10 docking poses, crystal ligand as pocket
      reference, models/saved_model.pth) must give the pKd and RMSD values printed in
      the authors' notebook scripts/scoring-demo.ipynb.
  [2] CASF-2016 complex 1a30 (protein + crystal ligand .mol2) must give pKd 5.0653.
      This value is ours (Linux, 21/10/2026, same versions as environment.yml):
      neither the authors nor Eaves et al. publish per-complex CASF-2016 values.
      The experimental value of 1a30 is 4.30.

Usage (inside the igmodel environment)
  python test_1a30.py --ig-dir <IGModel folder> --complex <...\\coreset\\1a30>

Exit code 0 = PASS, 1 = FAIL.
"""
import argparse
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import predict_igmodel as W  # noqa: E402

# scripts/scoring-demo.ipynb (authors), pose -> (pred_rmsd, pred_pkd)
REF_1BCU = {1: (0.405091, 4.184812), 2: (0.647050, 4.100025), 3: (2.626471, 2.096566),
            4: (3.638276, 1.068059), 5: (3.841610, 1.556922), 6: (4.976994, -0.403105),
            7: (5.079344, -0.465075), 8: (3.763524, 1.701476), 9: (7.514856, -2.740049),
            10: (7.302489, -2.573426)}
REF_1A30 = 5.0653
EXPERIMENTAL_PKD = 4.30
TOL_1BCU = 0.001
TOL_1A30 = 0.01


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--ig-dir", required=True, help="IGModel folder (with scripts/, models/ and samples/)")
    ap.add_argument("--complex", required=True, help="CASF-2016 folder of complex 1a30")
    a = ap.parse_args()
    ig = os.path.abspath(a.ig_dir)
    cx = os.path.abspath(a.complex)
    s = os.path.join(ig, "samples", "1bcu")
    need = [os.path.join(ig, "models", "saved_model.pth"), os.path.join(s, "1bcu_protein_atom_noHETATM.pdb"),
            os.path.join(s, "1bcu_ligand.sdf"), os.path.join(s, "1bcu_decoys.sdf"),
            os.path.join(cx, "1a30_protein.pdb"), os.path.join(cx, "1a30_ligand.mol2")]
    for f in need:
        if not os.path.isfile(f):
            sys.exit("ERROR: file not found: " + f)

    print("Loading model ...")
    net = W.load(ig, "ref")
    ok = True

    df = W.score_poses(net, need[1], need[3], ref_file=need[2])
    diffs = []
    for _, r in df.iterrows():
        idx = int(r.pose.rsplit("-", 1)[1])
        rr, rp = REF_1BCU[idx]
        diffs.append(max(abs(r.pred_rmsd - rr), abs(r.pred_pkd - rp)))
    d = max(diffs) if len(diffs) == 10 else float("inf")
    good = d <= TOL_1BCU
    ok = ok and good
    print("\n[1] Authors' example 1bcu: %d poses scored (authors 10), max difference %.6f" % (len(df), d))
    print("    PASS - matches the authors' notebook" if good else
          "    FAIL - check the PyTorch, DGL, RDKit and Open Babel versions (environment.yml)")

    df = W.score_poses(net, need[4], need[5], ref_file=need[5])
    p = float(df.pred_pkd.iloc[0])
    good = abs(p - REF_1A30) <= TOL_1A30
    ok = ok and good
    print("\n[2] Predicted pKd 1a30: %.4f (reference %.4f, experimental %.2f; predicted RMSD %.2f A)"
          % (p, REF_1A30, EXPERIMENTAL_PKD, df.pred_rmsd.iloc[0]))
    print("    PASS" if good else "    FAIL - the CASF-2016 pipeline gives a different value")
    print("\nRESULT: %s" % ("PASS" if ok else "FAIL"))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
