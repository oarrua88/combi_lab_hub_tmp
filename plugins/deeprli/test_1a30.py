"""DeepRLI installation test with complex 1a30 (HIV-1 protease).

What it checks
  1. The trained model has the expected MD5 (334ada64...0f29, GitHub release v1.0.2;
     the same file is attached to v1.0.0, v1.0.1 and v1.0.2).
  2. The authors' preprocessing builds the complex graph for 1a30 from
     1a30_protein.pdb + the ligand. RDKit cannot read 1a30_ligand.sdf, so DeepRLI
     falls back to 1a30_ligand.mol2 (the authors' own file order: sdf, then mol2).
  3. The prediction is a finite number and is repeated exactly in a second run.
  4. pKd matches the CombiLabHUB reference value REF_PKD (own value: neither the
     authors nor Eaves et al. 2026 publish a DeepRLI prediction for 1a30).
     Recorded on 23/10/2026: pKd 4.1986 (DeltaG -5.7279 kcal/mol), identical with
     Windows conda (PyTorch 2.2.2) and Docker (PyTorch 2.3.1).
The experimental value is pKd 4.30.

Usage (inside the deeprli environment)
  python test_1a30.py --deeprli-dir <DeepRLI repo> --complex <...\\coreset\\1a30>
                      [--model <trained_model.state_dict.pth>]

Exit code 0 = PASS, 1 = FAIL.
"""
import argparse
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import predict_deeprli as W  # noqa: E402

REF_PKD = 4.1986        # CombiLabHUB reference: 23/10/2026, lab PC, Windows conda AND Docker (DeltaG -5.7279 kcal/mol)
EXPERIMENTAL_PKD = 4.30
TOL = 0.01


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--deeprli-dir", required=True, help="DeepRLI repository (with src/deeprli)")
    ap.add_argument("--model", help="trained_model.state_dict.pth (default: <deeprli-dir>/trained_model.state_dict.pth)")
    ap.add_argument("--complex", required=True, help="CASF-2016 folder of complex 1a30")
    args = ap.parse_args()

    casf = os.path.abspath(args.complex)
    for f in ("1a30_protein.pdb", "1a30_ligand.mol2"):
        if not os.path.isfile(os.path.join(casf, f)):
            sys.exit("ERROR: file not found: " + os.path.join(casf, f))
    model_path = args.model or os.path.join(args.deeprli_dir, "trained_model.state_dict.pth")
    ok = True

    good = os.path.isfile(model_path) and W.md5(model_path) == W.MODEL_MD5
    print("[1] Model %s\n    %s" % (model_path, "PASS - MD5 " + W.MODEL_MD5 if good else "FAIL - wrong MD5 or file missing"))
    if not good:
        print("\nRESULT: FAIL")
        sys.exit(1)

    torch, model = W.load(args.deeprli_dir, model_path, check_md5=False)
    ligs = {ext: os.path.join(casf, "1a30_ligand." + ext) for ext in W.LIGAND_TYPES}
    ligs = {k: v for k, v in ligs.items() if os.path.isfile(v)}
    complexes = [("1a30", os.path.join(casf, "1a30_protein.pdb"), ligs)]

    res1, missing = W.score_complexes(torch, model, complexes)
    good = not missing and len(res1) == 1
    ok = ok and good
    lig = res1[0]["ligand_file"] if res1 else "-"
    print("\n[2] Complex graph built from 1a30_protein.pdb + %s" % lig)
    print("    PASS" if good else "    FAIL - DeepRLI could not process 1a30")
    if not good:
        print("\nRESULT: FAIL")
        sys.exit(1)

    r = res1[0]
    res2, _ = W.score_complexes(torch, model, complexes)
    same = res2 and abs(res2[0]["DeltaG_predicted"] - r["DeltaG_predicted"]) < 1e-6
    good = math.isfinite(r["pKd_predicted"]) and same
    ok = ok and good
    print("\n[3] Prediction: DeltaG %.4f kcal/mol -> pKd %.4f (experimental %.2f)"
          % (r["DeltaG_predicted"], r["pKd_predicted"], EXPERIMENTAL_PKD))
    print("    docking score %.4f | screening score %.4f" % (r["docking_score"], r["screening_score"]))
    print("    PASS - finite and identical in a second run" if good else "    FAIL - not finite or not repeatable")

    if REF_PKD is None:
        print("\n[4] No reference value recorded yet.")
        print("    Record REF_PKD = %.4f in test_1a30.py after checking the run." % r["pKd_predicted"])
    else:
        good = abs(r["pKd_predicted"] - REF_PKD) <= TOL
        ok = ok and good
        print("\n[4] pKd %.4f vs CombiLabHUB reference %.4f" % (r["pKd_predicted"], REF_PKD))
        print("    PASS - matches the reference" if good else "    FAIL - check the package versions (environment.yml)")

    print("\nRESULT:", ("PASS" if ok else "FAIL") + (" (no reference value yet)" if ok and REF_PKD is None else ""))
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
