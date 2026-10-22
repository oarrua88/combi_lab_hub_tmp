"""PIGNet2 installation test with complex 1a30 (HIV-1 protease).

What it checks
  1. Our preparation of 1a30 from the CASF-2016 files (ligand .mol2 with its
     hydrogens, pocket with the authors' generate_data.extract) gives the same
     molecules as the authors' own prepared 1a30 (CASF-2016_scoring.tar.xz,
     Zenodo 10.5281/zenodo.8091220): ligand of 26 heavy atoms with formal
     charge -2 and a pocket of 160 heavy atoms. We checked that the pocket atoms,
     charges and coordinates are identical, not only the counts.
  2. The four trained models of the repository (src/ckpt/pda_0..3.pt) give the
     energies -2.865, -2.897, -3.068 and -2.637 kcal/mol, the same values the
     authors' test.py gives with their prepared 1a30. pKd = energy / -1.36:
     2.1063, 2.1299, 2.2557, 1.9390 (mean 2.1077). The experimental value is 4.30.
     (With the authors' 285 prepared complexes the 4-model mean gives PCC 0.7467,
     the 0.747 of the paper.)

Usage (inside the pignet2 environment)
  python test_1a30.py --pignet2-dir <PIGNet2 repository folder> --complex <...\\coreset\\1a30>

Exit code 0 = PASS, 1 = FAIL.
"""
import argparse
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import predict_pignet2 as W  # noqa: E402

REF_SIZE = (26, -2, 160)
REF_ENERGY = (-2.865, -2.897, -3.068, -2.637)
EXPERIMENTAL_PKD = 4.30
TOL = 0.005  # kcal/mol (the authors print 3 decimals)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--pignet2-dir", required=True, help="PIGNet2 repository folder (contains src/ckpt)")
    ap.add_argument("--complex", required=True, help="CASF-2016 folder of complex 1a30")
    args = ap.parse_args()

    casf = os.path.abspath(args.complex)
    prot, lig = os.path.join(casf, "1a30_protein.pdb"), os.path.join(casf, "1a30_ligand.mol2")
    for f in (prot, lig):
        if not os.path.isfile(f):
            sys.exit("ERROR: file not found: " + f)

    from rdkit import Chem
    torch, nets = W.load(args.pignet2_dir)
    ok = True

    ligand, pocket = W.prepare(prot, lig)
    size = (ligand.GetNumHeavyAtoms(), Chem.GetFormalCharge(ligand), pocket.GetNumHeavyAtoms())
    good = size == REF_SIZE
    ok = ok and good
    print("[1] 1a30: ligand %d heavy atoms (charge %+d), pocket %d heavy atoms" % size)
    print("    PASS - same as the authors' prepared 1a30" if good
          else "    FAIL - expected ligand %d (charge %+d), pocket %d (check RDKit / PyMOL)" % REF_SIZE)

    res = W.score(torch, nets, ligand, pocket, "1a30")
    print("\n[2] Trained models (experimental pKd %.2f):" % EXPERIMENTAL_PKD)
    for i, ((e, p), r) in enumerate(zip(res, REF_ENERGY)):
        good = abs(e - r) <= TOL
        ok = ok and good
        print("    model pda_%d: %.3f kcal/mol (reference %.3f) -> pKd %.4f %s"
              % (i, e, r, p, "PASS" if good else "FAIL"))
    mean = sum(p for _, p in res) / len(res)
    print("    mean       : pKd %.4f (reference %.4f)" % (mean, sum(REF_ENERGY) / len(REF_ENERGY) / W.KCAL_PER_PKD))

    print("\nRESULT:", "PASS" if ok else "FAIL")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
