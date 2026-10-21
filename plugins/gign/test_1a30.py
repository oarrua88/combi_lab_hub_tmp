"""GIGN installation test with complex 1a30 (HIV-1 protease).

What it checks
  1. Pocket and ligand preparation (PyMOL + Open Babel + RDKit) gives the same
     graph size as the authors' own prepared graph of 1a30 (test2016 set of
     GIGN_data.zip, Zenodo 10.5281/zenodo.7490623): 26 ligand + 160 pocket atoms,
     348 covalent and 530 non-covalent edges. We checked that the full graph
     (features, edges and coordinates) is identical, not only its size.
  2. The three trained models of the repository give pKd 4.3883, 6.3427 and
     6.4380 (mean 5.7230), the values the authors' own scripts give for 1a30.
The experimental value is 4.30.

Usage (inside the gign environment)
  python test_1a30.py --gign-dir <GIGN repository folder> --complex <...\\coreset\\1a30>

Exit code 0 = PASS, 1 = FAIL.
"""
import argparse
import os
import shutil
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import predict_gign as W  # noqa: E402

REF_SIZE = (26, 160, 348, 530)
REF_MODELS = (4.3883, 6.3427, 6.4380)
EXPERIMENTAL_PKD = 4.30
TOL = 0.01


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--gign-dir", required=True, help="GIGN repository folder (contains GIGN/GIGN.py)")
    ap.add_argument("--complex", required=True, help="CASF-2016 folder of complex 1a30")
    args = ap.parse_args()

    casf = os.path.abspath(args.complex)
    prot, lig = os.path.join(casf, "1a30_protein.pdb"), os.path.join(casf, "1a30_ligand.mol2")
    for f in (prot, lig):
        if not os.path.isfile(f):
            sys.exit("ERROR: file not found: " + f)

    torch, nets, ds = W.load(args.gign_dir)
    work = tempfile.mkdtemp(prefix="gign_test_")
    ok = True

    ligand, pocket = W.prepare(prot, lig, work)
    preds = W.score(torch, nets, ds, ligand, pocket, work)
    g = torch.load(os.path.join(work, "graph.pyg"))
    size = (ligand.GetNumAtoms(), pocket.GetNumAtoms(), g.edge_index_intra.shape[1], g.edge_index_inter.shape[1])
    good = size == REF_SIZE
    ok = ok and good
    print("[1] Graph of 1a30: %d ligand + %d pocket atoms, %d covalent + %d non-covalent edges" % size)
    print("    PASS - same as the authors' prepared graph" if good
          else "    FAIL - expected %s (check PyMOL / Open Babel / RDKit)" % (REF_SIZE,))

    print("\n[2] Trained models (experimental pKd %.2f):" % EXPERIMENTAL_PKD)
    for i, (p, r) in enumerate(zip(preds, REF_MODELS)):
        good = abs(p - r) <= TOL
        ok = ok and good
        print("    model %d: pKd %.4f (reference %.4f) %s" % (i, p, r, "PASS" if good else "FAIL"))
    print("    mean   : pKd %.4f (reference %.4f)" % (sum(preds) / 3, sum(REF_MODELS) / 3))

    shutil.rmtree(work, ignore_errors=True)
    print("\nRESULT:", "PASS" if ok else "FAIL")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
