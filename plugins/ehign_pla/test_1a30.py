"""EHIGN-PLA installation test with complex 1a30 (HIV-1 protease).

What it checks
  1. Pocket and ligand preparation (PyMOL + Open Babel + RDKit) gives the
     expected heterograph: 26 ligand + 160 pocket atoms; 50 ligand-bond,
     298 pocket-bond and 265 + 265 ligand<->pocket contact edges. The
     preparation is the same as in GIGN, whose graph of 1a30 we checked is
     identical to the authors' prepared one.
  2. The three trained models of the repository give pKd 5.5024, 5.8087 and
     5.0898 (mean 5.4670), the values the authors' own scripts give for 1a30
     (preprocess_complex.py -> graph_constructor.py -> test.py, with the DGL fix).
The experimental value is 4.30.

Usage (inside the gign environment)
  python test_1a30.py --ehign-dir <EHIGN_PLA repository folder> --complex <...\\coreset\\1a30>

Exit code 0 = PASS, 1 = FAIL.
"""
import argparse
import os
import shutil
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import predict_ehign_pla as W  # noqa: E402

REF_SIZE = (26, 160, 50, 298, 265, 265)
REF_MODELS = (5.5024, 5.8087, 5.0898)
EXPERIMENTAL_PKD = 4.30
TOL = 0.01


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--ehign-dir", required=True, help="EHIGN_PLA repository folder (contains EHIGN.py)")
    ap.add_argument("--complex", required=True, help="CASF-2016 folder of complex 1a30")
    args = ap.parse_args()

    casf = os.path.abspath(args.complex)
    prot, lig = os.path.join(casf, "1a30_protein.pdb"), os.path.join(casf, "1a30_ligand.mol2")
    for f in (prot, lig):
        if not os.path.isfile(f):
            sys.exit("ERROR: file not found: " + f)

    torch, nets, gc = W.load(args.ehign_dir)
    work = tempfile.mkdtemp(prefix="ehign_test_")
    ok = True

    ligand, pocket = W.prepare(prot, lig, work)
    preds = W.score(torch, nets, gc, ligand, pocket, work)
    g, _ = torch.load(os.path.join(work, "graph.dgl"))
    size = (g.num_nodes("ligand"), g.num_nodes("pocket"), g.num_edges("intra_l"), g.num_edges("intra_p"),
            g.num_edges("inter_l2p"), g.num_edges("inter_p2l"))
    good = size == REF_SIZE
    ok = ok and good
    print("[1] Graph of 1a30: %d ligand + %d pocket atoms; edges %d ligand, %d pocket, %d l->p, %d p->l" % size)
    print("    PASS - matches the reference" if good
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
