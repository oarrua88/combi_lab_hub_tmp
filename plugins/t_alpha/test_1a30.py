"""T-ALPHA installation test with complex 1a30 (HIV-1 protease).

  1. The trained model (model_parameters/CASF.ckpt) and the authors' CASF-2016 feature file
     (test_files/CASF_crystal.h5) have the expected MD5.
  2. 1a30 is in the feature file, with the experimental pKd of CASF-2016 (4.30).
  3. The authors' inference code, run on CPU, predicts 1a30 like the CombiLabHUB reference
     REF_PKD (own value, 25/10/2026: the authors publish metrics, not per-complex predictions).

T-ALPHA does not read the CASF-2016 PDB/mol2 files directly: its features (ESM2-3B embedding,
SMILES-transformer vector, graphs, surface point cloud) come already computed in CASF_crystal.h5.

usage:
  python test_1a30.py --talpha-dir <T-ALPHA repo> --data-dir <folder with model_parameters/ and test_files/>
"""
import argparse
import hashlib
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import predict_t_alpha as P  # noqa: E402

CKPT_MD5 = "704f963c2fe2f8363e4cc06fd4a2f304"   # model_parameters/CASF.ckpt (Zenodo 14510963)
HDF_MD5 = "b853bbf8dd86edfd8c8f01e95bdf08aa"    # test_files/CASF_crystal.h5 (Zenodo 14510963)
EXPERIMENTAL_PKD = 4.30
# CombiLabHUB references, 25/10/2026 (Linux, PyTorch 2.5.1 CPU). T-ALPHA predictions change a
# little with the other complexes in the batch, so the test checks two fixed situations:
REF_PKD_ALONE = 5.7758    # 1a30 scored alone (batch of 1)
REF_PKD_AUTHORS = 5.7024  # 1a30 in the authors' setting: first batch of 32 of CASF_crystal.h5
TOL = 0.01


def md5(path):
    h = hashlib.md5()
    with open(path, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--talpha-dir", required=True)
    ap.add_argument("--data-dir", required=True, help="folder that contains model_parameters/ and test_files/")
    a = ap.parse_args()

    ckpt = os.path.join(a.data_dir, "model_parameters", "CASF.ckpt")
    hdf = os.path.join(a.data_dir, "test_files", "CASF_crystal.h5")
    ok = True

    got = [md5(p) if os.path.isfile(p) else "missing" for p in (ckpt, hdf)]
    good = got == [CKPT_MD5, HDF_MD5]
    print("[1] Model %s\n    Features %s\n    %s" % (ckpt, hdf,
          "PASS - MD5 %s, %s" % tuple(got) if good else "FAIL - MD5 %s, %s (expected %s, %s)" % (*got, CKPT_MD5, HDF_MD5)))
    if not good:
        print("\nRESULT: FAIL")
        sys.exit(1)

    import h5py
    with h5py.File(hdf, "r") as f:
        n = len(f.keys())
        good = "1a30" in f and abs(float(f["1a30"]["pKi_value"][()]) - EXPERIMENTAL_PKD) < 0.005
        exp = float(f["1a30"]["pKi_value"][()]) if "1a30" in f else float("nan")
        first32 = sorted(f.keys())[:32]   # h5py lists groups in this order; the authors' loader does not shuffle
    print("\n[2] 1a30 in CASF_crystal.h5 (%d complexes): experimental pKd %.2f\n    %s"
          % (n, exp, "PASS" if good else "FAIL"))
    ok = ok and good


    df = P.predict(a.talpha_dir, ckpt, hdf, ids=["1a30"], batch_size=1, quiet=True)
    p = float(df["pKd_predicted"].iloc[0])
    good = math.isfinite(p) and abs(p - REF_PKD_ALONE) <= TOL
    print("\n[3] 1a30 alone: pKd %.4f (experimental %.2f) vs CombiLabHUB reference %.4f\n    %s"
          % (p, EXPERIMENTAL_PKD, REF_PKD_ALONE, "PASS - matches the reference" if good else "FAIL - check the package versions"))
    ok = ok and good

    df = P.predict(a.talpha_dir, ckpt, hdf, ids=first32, batch_size=32, quiet=True)
    p = float(df.loc[df["pdbid"] == "1a30", "pKd_predicted"].iloc[0])
    good = math.isfinite(p) and abs(p - REF_PKD_AUTHORS) <= TOL
    print("\n[4] 1a30 in the authors' setting (first batch of 32 complexes): pKd %.4f vs reference %.4f\n    %s"
          % (p, REF_PKD_AUTHORS, "PASS - matches the reference" if good else "FAIL - check the package versions"))
    print("    (the whole file with batches of 32 gives the paper's CASF-2016 metrics: PCC 0.869, RMSE 1.112)")
    ok = ok and good

    print("\nRESULT: %s" % ("PASS" if ok else "FAIL"))
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
