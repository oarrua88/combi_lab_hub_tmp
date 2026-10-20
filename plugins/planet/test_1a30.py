"""PLANET installation test with complex 1a30 (HIV-1 protease).

What it checks
  1. The authors' prepared CASF-2016 complex 1a30 (core/1a30 inside core.tar.bz2
     in the PLANET repository) gives pKd 5.8930.
  2. The CASF-2016 files from PDBbind (protein .pdb, pocket from the .sdf,
     ligand graph from the .mol2, because RDKit cannot sanitize the CASF .sdf of
     1a30) give pKd 5.6216.
The difference between 1 and 2 comes only from how the ligand graph is read
(same SMILES, same pocket). The experimental value is 4.30.

Usage (inside the planet environment)
  python test_1a30.py --planet-dir <PLANET folder> --complex <...\\coreset\\1a30>

Exit code 0 = PASS, 1 = FAIL.
"""
import argparse
import os
import sys
import tarfile
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import predict_planet as W  # noqa: E402

REF_AUTHORS_FILES = 5.8930
REF_CASF_FILES = 5.6216
EXPERIMENTAL_PKD = 4.30
TOL = 0.01


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--planet-dir", required=True, help="PLANET folder (with PLANET_run.py, PLANET.param and core.tar.bz2)")
    ap.add_argument("--complex", required=True, help="CASF-2016 folder of complex 1a30")
    args = ap.parse_args()

    pdir = os.path.abspath(args.planet_dir)
    casf = os.path.abspath(args.complex)
    for f in (os.path.join(pdir, "PLANET.param"), os.path.join(pdir, "core.tar.bz2"),
              os.path.join(casf, "1a30_protein.pdb"), os.path.join(casf, "1a30_ligand.sdf"), os.path.join(casf, "1a30_ligand.mol2")):
        if not os.path.isfile(f):
            sys.exit("ERROR: file not found: " + f)

    work = tempfile.mkdtemp(prefix="planet_test_")
    with tarfile.open(os.path.join(pdir, "core.tar.bz2")) as tar:
        members = [m for m in tar.getmembers() if m.name.startswith("core/1a30/")]
        tar.extractall(work, members=members)
    auth = os.path.join(work, "core", "1a30")
    print("Working folder:", work)

    torch, R, g = W.load(pdir)
    ok = True

    mol, _ = W.read_ligand(auth, "1a30")
    p1 = W.score(torch, R, g, os.path.join(auth, "1a30_protein.pdb"), os.path.join(auth, "1a30_ligand.sdf"), mol)
    mol, src = W.read_ligand(casf, "1a30")
    p2 = W.score(torch, R, g, os.path.join(casf, "1a30_protein.pdb"), os.path.join(casf, "1a30_ligand.sdf"), mol)

    for label, pred, ref in (("[1] Authors' prepared 1a30 (core.tar.bz2)", p1, REF_AUTHORS_FILES),
                             ("[2] CASF-2016 1a30 (ligand from %s)" % os.path.basename(src), p2, REF_CASF_FILES)):
        good = abs(pred - ref) <= TOL
        ok = ok and good
        print("\n%s: pKd %.4f (reference %.4f, experimental %.2f)" % (label, pred, ref, EXPERIMENTAL_PKD))
        print("    PASS - matches the reference" if good else "    FAIL - check the package versions (environment.yml)")

    print("\nRESULT:", "PASS" if ok else "FAIL")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
