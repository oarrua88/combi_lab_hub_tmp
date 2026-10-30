"""AutoDock Vina installation test with complex 1a30 (HIV-1 protease).

What it checks
  1. The Vina executable runs and reports version 1.1.2 or 1.2.5.
  2. The pdbqt files of 1a30 are written (MGLTools for engine 1.1.2, Open Babel for 1.2.5).
  3. The Vina score of the crystal pose matches the CASF-2016 reference value
     (CASF-2016/power_scoring/examples/AutodockVina.dat, 1a30: -4.99866 kcal/mol):
       engine 1.1.2 (CASF-2016 protocol): within 0.0005 kcal/mol (it is reproduced exactly)
       engine 1.2.5 (Windows):            within 0.002 kcal/mol (Vina 1.2 prints 3 decimals: -4.999)
The experimental value is pKd 4.30; the Vina score in pKd units is 3.6665.

Usage (inside the autodock_vina environment)
  python test_1a30.py --vina <vina binary> --complex <...\\coreset\\1a30>
                      [--mgl-python <...> --mgl-util <...>]      (engine 1.1.2 only)

Exit code 0 = PASS, 1 = FAIL.
"""
from __future__ import print_function

import argparse
import os
import shutil
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import predict_autodock_vina as W  # noqa: E402

REF_KCAL = -4.99866      # CASF-2016 power_scoring/examples/AutodockVina.dat (AutoDock Vina 1.1.2)
TOL = {"1.1.2": 0.0005, "1.2.5": 0.002}
EXPERIMENTAL_PKD = 4.30


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--vina", default="vina")
    ap.add_argument("--complex", required=True, help="CASF-2016 folder of complex 1a30")
    ap.add_argument("--mgl-python")
    ap.add_argument("--mgl-util")
    args = ap.parse_args()

    for f in ("1a30_protein.pdb", "1a30_ligand.mol2"):
        if not os.path.isfile(os.path.join(args.complex, f)):
            sys.exit("ERROR: file not found: " + os.path.join(args.complex, f))

    vina = shutil.which(args.vina) or args.vina
    ver = W.vina_version(vina) if os.path.isfile(vina) else None
    good = ver in ("1.1.2", "1.2.5")
    print("[1] Vina executable %s\n    %s" % (vina, "PASS - AutoDock Vina " + ver if good else
                                             "FAIL - not found or version %s (need 1.1.2 or 1.2.5)" % ver))
    if not good:
        print("\nRESULT: FAIL")
        sys.exit(1)
    engine = ver
    mgl = W.find_mgltools(args) if engine == "1.1.2" else None
    obabel = shutil.which("obabel")
    if engine == "1.2.5" and not obabel:
        print("[2] FAIL - obabel not found: activate the autodock_vina environment\n\nRESULT: FAIL")
        sys.exit(1)

    keep = tempfile.mkdtemp(prefix="vina_test_")
    try:
        try:
            kcal = W.score_complex("1a30", args.complex, vina, engine, mgl, obabel, keep)
            ok2 = True
        except Exception as e:
            kcal, ok2 = None, False
            print("[2] pdbqt files and Vina score\n    FAIL - %s" % e)
        if ok2:
            print("[2] pdbqt files written by %s\n    PASS" % ("MGLTools 1.5.7" if engine == "1.1.2" else "Open Babel"))
    finally:
        shutil.rmtree(keep, ignore_errors=True)
    ok = ok2
    if ok2:
        diff = abs(kcal - REF_KCAL)
        ok3 = diff <= TOL[engine]
        print("[3] Vina score of 1a30 (engine %s): %.5f kcal/mol (pKd %.4f)\n"
              "    CASF-2016 reference %.5f, difference %.5f (tolerance %.4f)\n    %s"
              % (engine, kcal, W.KCAL_TO_PKD * kcal, REF_KCAL, diff, TOL[engine], "PASS" if ok3 else "FAIL"))
        ok = ok3
    print("    (experimental pKd of 1a30: %.2f)" % EXPERIMENTAL_PKD)
    print("\nRESULT: %s" % ("PASS" if ok else "FAIL"))
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
