"""HAC-Net installation test with complex 1a30 (HIV-1 protease).

  [1] The installed HACNet package is the official 1.4.3 and the four parameter files
      of the repository have the expected MD5.
  [2] CASF-2016 complex 1a30 must give pKd 4.9114. This value is ours (Linux,
      21/10/2026), with the pocket charges computed by ChargeFW2 3.0.0 (EqEq, the
      program behind the ACC2 web service). Neither the authors nor Eaves et al.
      publish per-complex values. The experimental value of 1a30 is 4.30.
      With --charges acc2 (default on Windows) the charges come from the ACC2 web
      service; if it runs another ChargeFW2 version the value can differ slightly,
      so the tolerance is 0.05.

Usage (inside the hacnet environment)
  python test_1a30.py --hacnet-dir <HAC-Net folder> --complex <...\\coreset\\1a30> [--charges acc2|chargefw2]

Exit code 0 = PASS, 1 = FAIL.
"""
import argparse
import hashlib
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import predict_hacnet as W  # noqa: E402

REF_1A30 = 4.9114
EXPERIMENTAL_PKD = 4.30
TOL = 0.05
MD5 = {"CNN_parameters.pt": "7a16badb6abcdbf9075aea5f69b5acdf",
       "GCN0_parameters.pt": "dd12042a2b43aef2ba047e04116a9b07",
       "GCN1_parameters.pt": "04f8f791e2c14e667ca09ba292cca390",
       "MLP_parameters.pt": "91df31324dd88524d5278d017f57e2dd"}


def md5(path):
    h = hashlib.md5()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--hacnet-dir", required=True, help="HAC-Net folder (contains HACNet/parameter_files)")
    ap.add_argument("--complex", required=True, help="CASF-2016 folder of complex 1a30")
    ap.add_argument("--charges", choices=sorted(W.CHARGES), default="acc2",
                    help="acc2 = ACC2 web service (default, needs internet); chargefw2 = local ChargeFW2")
    a = ap.parse_args()
    hd = os.path.abspath(a.hacnet_dir)
    cx = os.path.abspath(a.complex)
    par = os.path.join(hd, "HACNet", "parameter_files")
    need = [os.path.join(par, f) for f in MD5] + [os.path.join(hd, "HACNet", "element_features.xml"),
                                                    os.path.join(cx, "1a30_protein.pdb"), os.path.join(cx, "1a30_ligand.mol2")]
    for f in need:
        if not os.path.isfile(f):
            sys.exit("ERROR: file not found: " + f)

    ok = True
    try:
        from importlib.metadata import version
        v = version("HACNet")
    except Exception:                                   # noqa: BLE001
        v = "not installed"
    bad = [f for f, m in MD5.items() if md5(os.path.join(par, f)) != m]
    good = v == "1.4.3" and not bad
    ok = ok and good
    print("[1] HACNet package %s (expected 1.4.3); parameter files: %s" % (v, "MD5 OK" if not bad else "WRONG MD5: " + ", ".join(bad)))
    print("    PASS" if good else "    FAIL - pip install --no-deps HACNet==1.4.3, and use the repository's parameter files")

    print("\nScoring 1a30 (pocket charges: %s) ..." % a.charges)
    try:
        p = W.predict_one(hd, need[5], need[6], a.charges)
    except Exception as e:                              # noqa: BLE001
        print("\n[2] ERROR: %s" % e)
        if a.charges == "acc2":
            print("    The ACC2 web service (https://acc2.ncbr.muni.cz) could not be reached or failed.")
            print("    Check the internet connection, or use --charges chargefw2 (Docker image, INSTALL.md section B).")
        print("\nRESULT: FAIL")
        return 1
    good = abs(p - REF_1A30) <= TOL
    ok = ok and good
    print("\n[2] Predicted pKd 1a30: %.4f (reference %.4f with ChargeFW2, experimental %.2f; difference %.4f)"
          % (p, REF_1A30, EXPERIMENTAL_PKD, p - REF_1A30))
    print("    PASS" if good else "    FAIL - check the package version, PyG and Open Babel (environment.yml)")
    print("\nRESULT: %s" % ("PASS" if ok else "FAIL"))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
