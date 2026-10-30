"""DeltaVinaRF20 installation test with complex 1a30 (HIV-1 protease).

What it checks
  1. The trained model deltavina/models/rffit.rda has the expected MD5 (944e70f5...72cc).
  2. The model reproduces the authors' example: examples/input.csv (complex 1a42, their features)
     gives 7.55, the value of the authors' examples/output.csv.
  3. pKd of 1a30 matches CASF-2016 (power_scoring/examples/deltaVinaRF20.dat, 1a30: 4.78, 2 decimals):
     - full pipeline (Linux / Docker, Python 2.7 environment): features computed from the CASF-2016
       files with the authors' code, then compared with features_1a30.csv;
     - otherwise (Windows conda): the features of 1a30 stored in features_1a30.csv
       (computed with the full pipeline on 30/10/2026).
     CombiLabHUB value before rounding: 4.7758; Vina part 3.6665 (= -0.73349 x -4.99866 kcal/mol).
The experimental value is pKd 4.30.

Usage
  python test_1a30.py --dv-dir <deltavina repo> --complex <...\\coreset\\1a30> [--model-only]

Exit code 0 = PASS, 1 = FAIL.
"""
from __future__ import print_function

import argparse
import csv
import os
import shutil
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import predict_deltavinarf20 as W  # noqa: E402

CASF_REF = "4.78"            # CASF-2016 power_scoring/examples/deltaVinaRF20.dat
REF_PKD = 4.7758             # CombiLabHUB, 30/10/2026, before rounding
REF_VINA = 3.6665
AUTHORS_EXAMPLE = "7.55"     # deltavina examples/output.csv (complex 1a42)
FEAT_TOL = 0.001
EXPERIMENTAL_PKD = 4.30


def read_features(path):
    with open(path) as f:
        r = next(csv.DictReader(f))
    return [float(r[k]) for k in W.FEATURES]


def pipeline_available():
    return (sys.version_info[0] == 2 and all(os.environ.get(v) for v in ("VINADIR", "MGLPY", "MGLUTIL"))
            and W.which("msms") is not None)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dv-dir", required=True, help="deltavina repository")
    ap.add_argument("--complex", help="CASF-2016 folder of complex 1a30 (needed for the full pipeline)")
    ap.add_argument("--model-only", action="store_true", help="use features_1a30.csv even if the pipeline is available")
    ap.add_argument("--tools-dir", default=HERE)
    args = ap.parse_args()
    ok = True

    model = os.path.join(args.dv_dir, W.MODEL)
    good = os.path.isfile(model) and W.md5(model) == W.MODEL_MD5
    print("[1] Model %s\n    %s" % (model, "PASS - MD5 " + W.MODEL_MD5 if good else "FAIL - wrong MD5 or file missing"))
    if not good:
        print("\nRESULT: FAIL")
        sys.exit(1)

    example = os.path.join(args.dv_dir, "examples", "input.csv")
    try:
        rows, rver = W.r_predict(args.dv_dir, example, check_md5=False)
        pred2 = rows[0][2]
        good = pred2 == AUTHORS_EXAMPLE
        print("[2] Authors' example (1a42, examples/input.csv): %s (%.4f), authors %s\n    %s\n    %s"
              % (pred2, rows[0][1], AUTHORS_EXAMPLE, rver, "PASS" if good else "FAIL"))
    except Exception as e:
        good = False
        print("[2] Authors' example\n    FAIL - %s" % e)
    ok = ok and good

    stored = os.path.join(HERE, "features_1a30.csv")
    full = pipeline_available() and not args.model_only
    work = tempfile.mkdtemp(prefix="dvrf20_test_")
    try:
        if full:
            if not args.complex:
                sys.exit("ERROR: --complex is needed for the full pipeline")
            W.setup_pipeline(args.dv_dir, args.tools_dir)
            feat = W.featurize("1a30", args.complex)
            ref = read_features(stored)
            diff = max(abs(a - b) for a, b in zip(feat, ref))
            good = diff <= FEAT_TOL
            print("[3a] Features of 1a30 computed with the authors' code (Vina terms, buried SASA)\n"
                  "     largest difference with features_1a30.csv: %.6f (tolerance %.3f)\n     %s"
                  % (diff, FEAT_TOL, "PASS" if good else "FAIL"))
            ok = ok and good
            feats_csv = os.path.join(work, "features.csv")
            W.write_features(feats_csv, [("1a30", feat)])
        else:
            print("[3a] Full feature pipeline not available here (it needs the Python 2.7 environment of the\n"
                  "     Docker image): using the stored features of 1a30 (features_1a30.csv)")
            feats_csv = stored
        rows, _ = W.r_predict(args.dv_dir, feats_csv, check_md5=False)
        code, pred, pred2, vina = rows[0]
        good = pred2 == CASF_REF and abs(pred - REF_PKD) < 0.0005 and abs(vina - REF_VINA) < 0.0005
        print("[3b] pKd of 1a30: %.4f -> %s (Vina part %.4f)\n     CASF-2016 reference %s, CombiLabHUB %.4f\n     %s"
              % (pred, pred2, vina, CASF_REF, REF_PKD, "PASS" if good else "FAIL"))
        ok = ok and good
    except SystemExit:
        raise
    except Exception as e:
        ok = False
        print("[3] pKd of 1a30\n    FAIL - %s" % e)
    finally:
        shutil.rmtree(work, ignore_errors=True)
    print("    (experimental pKd of 1a30: %.2f)" % EXPERIMENTAL_PKD)
    print("\nRESULT: %s" % ("PASS" if ok else "FAIL"))
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
