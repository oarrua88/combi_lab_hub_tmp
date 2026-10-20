"""OnionNet-2 installation test with complex 1a30 (HIV-1 protease).

What it checks
  1. Features: the 10,416 OnionNet-2 features (62 shells x 21 residue types x
     8 ligand element types) for the CASF-2016 complex 1a30, with the ligand
     converted from .mol2 by Open Babel, are identical to the CombiLabHUB
     reference (reference/1a30_features_nonzero.csv).
  2. With the model (62shell_saved-model.h5):
     a. the authors' own sample complex (OnionNet-2/samples/1a30, PDBbind files
        with crystallographic waters) gives pKd 5.4568, the same as the authors'
        scoring/predict.py;
     b. the CASF-2016 complex 1a30 (no waters) gives pKd 5.8866.
     The experimental value is 4.30.

Usage (inside the onionnet2 environment)
  python test_1a30.py --on-dir <OnionNet-2 folder> --complex <...\\coreset\\1a30> [--model <62shell_saved-model.h5>]

Exit code 0 = PASS, 1 = FAIL.
"""
import argparse
import os
import shutil
import sys
import tempfile

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import predict_onionnet2 as W  # noqa: E402

REF_FEATURES = os.path.join(HERE, "reference", "1a30_features_nonzero.csv")
REF_SAMPLE = 5.4568   # authors' samples/1a30 (PDBbind files, with waters)
REF_CASF = 5.8866     # CASF-2016 coreset/1a30 (no waters), ligand converted from .mol2
EXPERIMENTAL_PKD = 4.30
TOL = 0.01


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--on-dir", required=True, help="OnionNet-2 folder (with scoring/, models/ and samples/)")
    ap.add_argument("--complex", required=True, help="CASF-2016 folder of complex 1a30")
    ap.add_argument("--model", help="62shell_saved-model.h5 (optional: without it only features are tested)")
    args = ap.parse_args()

    on_dir = os.path.abspath(args.on_dir)
    src = os.path.abspath(args.complex)
    protein = os.path.join(src, "1a30_protein.pdb")
    ligand = os.path.join(src, "1a30_ligand.mol2")
    scaler = os.path.join(on_dir, "models", "train_scaler.scaler")
    sample = os.path.join(on_dir, "samples", "1a30")
    for f in (os.path.join(on_dir, "scoring", "predict.py"), scaler, protein, ligand,
              os.path.join(sample, "1a30_protein.pdb"), os.path.join(sample, "1a30_ligand.pdb")):
        if not os.path.isfile(f):
            sys.exit("ERROR: file not found: " + f)
    if args.model and not os.path.isfile(args.model):
        sys.exit("ERROR: model not found: " + args.model)

    work = tempfile.mkdtemp(prefix="onionnet2_test_")
    cdir = os.path.join(work, "casf", "1a30")
    os.makedirs(cdir)
    shutil.copy(protein, cdir)
    shutil.copy(ligand, cdir)
    print("Working folder:", work)

    ok = True
    P = W.load_upstream(on_dir)

    # 1) features of the CASF complex
    print("Converting the ligand with Open Babel and computing features ...")
    lig_pdb = W.ligand_as_pdb(cdir, "1a30", work)
    f_casf = W.compute_features(P, os.path.join(cdir, "1a30_protein.pdb"), lig_pdb)
    names = ["s%02d_%s" % (sh + 1, k) for sh in range(W.SHELLS) for k in P.keys]
    mine = pd.Series(f_casf, index=names)
    ref = pd.read_csv(REF_FEATURES, index_col=0)["value"].reindex(names).fillna(0)
    diff = (mine - ref).abs()
    print("\n[1] Features: %d non-zero (reference %d), max difference %.4f"
          % ((mine != 0).sum(), (ref != 0).sum(), diff.max()))
    if (diff > TOL).any():
        ok = False
        print("    FAIL - %d features differ" % int((diff > TOL).sum()))
    else:
        print("    PASS - identical to the CombiLabHUB reference")

    # 2) predictions
    if args.model:
        import joblib
        import tensorflow as tf
        f_sample = W.compute_features(P, os.path.join(sample, "1a30_protein.pdb"), os.path.join(sample, "1a30_ligand.pdb"))
        sc = joblib.load(scaler)
        x = sc.transform(np.array([f_sample, f_casf])).reshape([-1] + W.SHAPE)
        print("\nLoading model (885 MB, takes a moment) ...")
        model = tf.keras.models.load_model(args.model, custom_objects={"RMSE": P.RMSE, "PCC": P.PCC, "PCC_RMSE": P.PCC_RMSE})
        p_sample, p_casf = model.predict(x).ravel()
        for label, pred, refv in (("[2a] Authors' sample 1a30 (with waters)", p_sample, REF_SAMPLE),
                                  ("[2b] CASF-2016 1a30 (no waters)       ", p_casf, REF_CASF)):
            good = abs(pred - refv) <= TOL
            ok = ok and good
            print("\n%s: pKd %.4f (reference %.4f, experimental %.2f)" % (label, pred, refv, EXPERIMENTAL_PKD))
            print("    PASS - matches the reference" if good else "    FAIL - check that the package versions match environment.yml")
    else:
        print("\n[2] Prediction skipped (use --model 62shell_saved-model.h5)")

    print("\nRESULT:", "PASS" if ok else "FAIL")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
