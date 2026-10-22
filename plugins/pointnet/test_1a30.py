"""PointNet / PointTransformer (Wang et al. 2022) installation test with complex 1a30 (HIV-1 protease).

What it checks
  1. Point cloud of 1a30 (Linux or Docker only; skipped on Windows, where the
     authors' POINTNET program does not run): Open Babel + POINTNET make the
     same 1024-point cloud as our reference (ref_1a30_cloud.txt, MD5
     1c158b184e9df27a31f24ac920e40d32: 993 protein + 31 ligand points).
  2. The authors' example cloud (example/5c2h_11.09) with the 5 PointTransformer
     and the 5 PointNet models, 5 rotations each, seed 0: pKd 7.4829 and 7.5160.
     The authors publish no value for it; these are our own reference values
     (Linux, PyTorch 2.3.1 CPU).
  3. The 1a30 cloud with the 5 PointTransformer models: pKd 4.6973 (PointNet:
     4.7429). The experimental value is 4.30. The authors publish no value for
     1a30.

Usage
  python test_1a30.py --pointnet-dir <Point-Cloud repository folder> --complex <...\\coreset\\1a30>

Exit code 0 = PASS, 1 = FAIL.
"""
import argparse
import hashlib
import os
import shutil
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import predict_pointnet as W  # noqa: E402

REF_CLOUD = os.path.join(HERE, "ref_1a30_cloud.txt")
REF_CLOUD_MD5 = "1c158b184e9df27a31f24ac920e40d32"
REF_EXAMPLE = {"PointTransformer": 7.4829, "PointNet": 7.5160}
REF_1A30 = {"PointTransformer": 4.6973, "PointNet": 4.7429}
EXPERIMENTAL_PKD = 4.30
TOL = 0.01


def md5(path):
    with open(path, "rb") as f:
        return hashlib.md5(f.read()).hexdigest()


def same_cloud(a, b, tol=1e-4):
    import numpy as np
    x, y = np.loadtxt(a), np.loadtxt(b)
    return x.shape == y.shape and np.allclose(x, y, atol=tol)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--pointnet-dir", required=True, help="Point-Cloud repository folder (contains POINTNET and Model/)")
    ap.add_argument("--complex", required=True, help="CASF-2016 folder of complex 1a30")
    args = ap.parse_args()

    casf = os.path.abspath(args.complex)
    prot, lig = os.path.join(casf, "1a30_protein.pdb"), os.path.join(casf, "1a30_ligand.mol2")
    for f in (prot, lig):
        if not os.path.isfile(f):
            sys.exit("ERROR: file not found: " + f)
    ok = True

    print("[1] Point cloud of 1a30 (Open Babel + POINTNET):")
    cloud = REF_CLOUD
    if os.name == "nt":
        print("    SKIPPED - POINTNET is a Linux program. Use docker_pointnet.bat for this step.")
        print("    Steps 2 and 3 use the reference cloud of this folder.")
    else:
        work = tempfile.mkdtemp(prefix="pointnet_test_")
        try:
            mine = W.make_cloud(args.pointnet_dir, prot, lig, work, os.path.join(work, "1a30_cloud.txt"))
            good = md5(mine) == REF_CLOUD_MD5 or same_cloud(mine, REF_CLOUD)
            if good:
                shutil.copyfile(mine, os.path.join(work, "keep.txt"))
                cloud = os.path.join(work, "keep.txt")
            print("    PASS - same 1024 points as the reference cloud" if good
                  else "    FAIL - different cloud (check Open Babel 3.1.1)")
        except Exception as e:
            good = False
            print("    FAIL - " + str(e))
        ok = ok and good

    print("\n[2] Authors' example cloud 5c2h (5 models x 5 rotations, seed 0):")
    example = os.path.join(os.path.abspath(args.pointnet_dir), "example", "5c2h_11.09")
    for kind in ("PointTransformer", "PointNet"):
        torch, nets, _ = W.load(args.pointnet_dir, kind)
        p, _ = W.score_cloud(torch, nets, example, kind)
        good = abs(p - REF_EXAMPLE[kind]) <= TOL
        ok = ok and good
        print("    %-16s pKd %.4f (reference %.4f) %s" % (kind, p, REF_EXAMPLE[kind], "PASS" if good else "FAIL"))

    print("\n[3] 1a30 (experimental pKd %.2f):" % EXPERIMENTAL_PKD)
    for kind in ("PointTransformer", "PointNet"):
        torch, nets, _ = W.load(args.pointnet_dir, kind)
        p, per = W.score_cloud(torch, nets, cloud, kind)
        good = abs(p - REF_1A30[kind]) <= TOL
        ok = ok and good
        print("    %-16s pKd %.4f (reference %.4f) %s   models: %s"
              % (kind, p, REF_1A30[kind], "PASS" if good else "FAIL", " ".join("%.2f" % x for x in per)))

    if cloud != REF_CLOUD:
        shutil.rmtree(os.path.dirname(cloud), ignore_errors=True)
    print("\nRESULT:", "PASS" if ok else "FAIL")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
