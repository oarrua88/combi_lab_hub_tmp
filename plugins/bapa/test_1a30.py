"""BAPA installation test: the authors' example complex 10gs and CASF-2016 complex 1a30.

What it checks
  1. Authors' example (data/complexes/10gs_* in the repository), the whole
     pipeline from the .pdb/.mol2 files:
       - Open Babel 2.4.1 .pdbqt + rf-extract give the six Vina terms of the
         authors' data/dataset/Vina_terms.pkl (111.8976, 1374.5154, 5.2593,
         39.6612, 7.0350, 0.0690);
       - the descriptor counts equal the authors' data/dataset/dataset.pkl;
       - the trained network gives pKd 4.91, the value in the authors'
         result/result.csv.
  2. 1a30 (HIV-1 protease): Vina terms 85.6817, 1306.8164, 4.7111, 30.4484,
     3.5947, 0.0741 and pKd 5.5433 with the CASF-2016 1a30_protein.mol2. The
     authors publish no value for 1a30; this is our own reference (Linux,
     TensorFlow 1.12). The experimental value is 4.30.

Usage (inside the bapa environment)
  python test_1a30.py --bapa-dir <BAPA repository folder> --complex <...\\coreset\\1a30>

Exit code 0 = PASS, 1 = FAIL.
"""
import argparse
import os
import pickle
import shutil
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import predict_bapa as W  # noqa: E402

REF_10GS_VINA = (111.8976, 1374.5154, 5.2593, 39.6612, 7.0350, 0.0690)
REF_10GS_PKD = 4.91  # authors' result/result.csv (2 decimals)
REF_1A30_VINA = (85.6817, 1306.8164, 4.7111, 30.4484, 3.5947, 0.0741)
REF_1A30_PKD = 5.5433
EXPERIMENTAL_PKD = 4.30


def close(a, b, tol):
    return all(abs(x - y) <= tol for x, y in zip(a, b))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--bapa-dir", required=True, help="BAPA repository folder (contains module/network)")
    ap.add_argument("--complex", required=True, help="CASF-2016 folder of complex 1a30")
    ap.add_argument("--rf-extract", help="path of rf-extract (default: bin/ of this folder or PATH)")
    args = ap.parse_args()

    import numpy as np
    casf = os.path.abspath(args.complex)
    files = {k: os.path.join(casf, "1a30_" + k) for k in ("protein.pdb", "ligand.mol2", "protein.mol2")}
    for f in files.values():
        if not os.path.isfile(f):
            sys.exit("ERROR: file not found: " + f)
    model = W.Bapa(args.bapa_dir, args.rf_extract)
    print("Using rf-extract: %s\nUsing Open Babel: %s" % (model.rf_extract, model.babel))
    work = tempfile.mkdtemp(prefix="bapa_test_")
    ok = True

    print("\n[1] Authors' example 10gs:")
    ex = os.path.join(model.root, "data", "complexes")
    p_qt, l_qt = model.pdbqt(os.path.join(ex, "10gs_protein.pdb"), os.path.join(ex, "10gs_ligand.mol2"),
                             os.path.join(work, "10gs"))
    v = model.vina_terms(p_qt, l_qt)
    good = close(v, REF_10GS_VINA, 1e-3)
    ok = ok and good
    print("    Vina terms  %s %s" % (" ".join("%.4f" % x for x in v), "PASS" if good else
                                     "FAIL (expected %s; Open Babel must be 2.4.1)" % " ".join("%.4f" % x for x in REF_10GS_VINA)))
    d = model.descriptors(os.path.join(ex, "10gs_protein.mol2"), os.path.join(ex, "10gs_ligand.mol2"))
    with open(os.path.join(model.root, "data", "dataset", "dataset.pkl"), "rb") as f:
        ref = list(pickle.load(f).values())[0]
    good = bool(np.array_equal(d, ref))
    ok = ok and good
    print("    Descriptors %d counts, sum %d %s" % (len(d), int(d.sum()), "PASS - same as the authors' dataset.pkl"
                                                     if good else "FAIL - differ from the authors' dataset.pkl"))
    p10 = model.predict([d], [v])[0]
    good = abs(p10 - REF_10GS_PKD) < 0.005 + 1e-6
    ok = ok and good
    print("    pKd %.4f (authors' result.csv: %.2f) %s" % (p10, REF_10GS_PKD, "PASS" if good else "FAIL"))

    print("\n[2] 1a30 (experimental pKd %.2f), protein .mol2 from CASF-2016:" % EXPERIMENTAL_PKD)
    p_qt, l_qt = model.pdbqt(files["protein.pdb"], files["ligand.mol2"], os.path.join(work, "1a30"))
    v = model.vina_terms(p_qt, l_qt)
    good = close(v, REF_1A30_VINA, 1e-3)
    ok = ok and good
    print("    Vina terms  %s %s" % (" ".join("%.4f" % x for x in v), "PASS" if good else "FAIL"))
    d = model.descriptors(files["protein.mol2"], files["ligand.mol2"])
    p = model.predict([d], [v])[0]
    good = abs(p - REF_1A30_PKD) <= 0.01
    ok = ok and good
    print("    pKd %.4f (reference %.4f) %s" % (p, REF_1A30_PKD, "PASS" if good else "FAIL"))

    shutil.rmtree(work, ignore_errors=True)
    print("\nRESULT:", "PASS" if ok else "FAIL")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
