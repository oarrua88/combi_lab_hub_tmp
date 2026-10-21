"""egGNN installation test with complex 1a30 (HIV-1 protease).

What it checks
  1. The ligand SMILES is read from the CASF-2016 1a30_ligand.mol2 with RDKit
     and is the same one Eaves et al. used in their reproduction.
  2. SMILES + 1a30_pocket.pdb (recommended input) gives pKd 5.1040, the same
     value Eaves et al. obtained (casf2016_egGNN_preds_and_times.csv in
     github.com/jeavesj/egGNN).
  3. SMILES + 1a30_protein.pdb (full protein, as the authors' README suggests)
     gives pKd 6.5326. Shown to make the input effect visible.
The experimental value is 4.30.

Usage (inside the eggnn environment)
  python test_1a30.py --eggnn-dir <egGNN folder> --complex <...\\coreset\\1a30>

Exit code 0 = PASS, 1 = FAIL.
"""
import argparse
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import predict_eggnn as W  # noqa: E402

REF_SMILES = "CC(C)C[C@H](NC(=O)[C@H](CC(=O)[O-])NC(=O)[C@@H]([NH3+])CCC(=O)[O-])C(=O)[O-]"
REF_POCKET = 5.1040
REF_PROTEIN = 6.5326
EXPERIMENTAL_PKD = 4.30
TOL = 0.01


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--eggnn-dir", required=True, help="egGNN folder (with run_egGNN.py and egGNN/checkpoint)")
    ap.add_argument("--complex", required=True, help="CASF-2016 folder of complex 1a30")
    args = ap.parse_args()

    casf = os.path.abspath(args.complex)
    for f in ("1a30_pocket.pdb", "1a30_protein.pdb", "1a30_ligand.mol2"):
        if not os.path.isfile(os.path.join(casf, f)):
            sys.exit("ERROR: file not found: " + os.path.join(casf, f))

    torch, model, cons, loadm = W.load(args.eggnn_dir)
    ok = True

    smi, src = W.ligand_smiles(casf, "1a30")
    good = smi == REF_SMILES
    ok = ok and good
    print("[1] Ligand SMILES from %s:\n    %s" % (os.path.basename(src), smi))
    print("    PASS - same SMILES as Eaves et al." if good else "    FAIL - different SMILES (check the RDKit version)")

    for label, pdb, ref in (("[2] SMILES + 1a30_pocket.pdb (recommended)", "1a30_pocket.pdb", REF_POCKET),
                            ("[3] SMILES + 1a30_protein.pdb (full protein)", "1a30_protein.pdb", REF_PROTEIN)):
        pred = W.score(torch, model, cons, loadm, smi, os.path.join(casf, pdb))
        good = abs(pred - ref) <= TOL
        ok = ok and good
        print("\n%s: pKd %.4f (reference %.4f, experimental %.2f)" % (label, pred, ref, EXPERIMENTAL_PKD))
        print("    PASS - matches the reference" if good else "    FAIL - check the package versions (environment.yml)")

    print("\nRESULT:", "PASS" if ok else "FAIL")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
