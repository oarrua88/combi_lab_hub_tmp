"""DTITR installation test with complex 1a30 (HIV-1 protease).

What it checks
  1. The trained model files model/dtitr_model/.data-00000-of-00001 and .index have
     the expected MD5.
  2. The encoding of CombiLabHUB (predict_dtitr.Encoder) is IDENTICAL to the authors'
     dataset_builder + add_reg_token for all 29,187 protein-SMILES pairs of the Davis
     dataset shipped in the repository (protein BPE 557 tokens, SMILES 73 tokens).
  3. The model loads correctly: predictions for the first 5 pairs of the authors' Davis
     test set match CombiLabHUB reference values (recorded 24/10/2026). With --full-davis
     it also runs the authors' whole Davis test set (~5,000 pairs, a few minutes on CPU)
     and prints MSE / CI / R2 / Spearman; recorded on 24/10/2026: MSE 0.1920,
     RMSE 0.4382, CI 0.9065, R2 0.7712, Spearman 0.7122.
  4. 1a30 from the CASF-2016 files: inputs (198 residues of the two chains, neutral
     SMILES) and pKd against the CombiLabHUB reference REF_PKD (own value: the authors
     never evaluated PDBbind). Note: DTITR was trained only on Davis kinases, where
     non-binders have pKd 5.0; the 1a30 prediction (~5.00) is the model saying
     "no binding", not an installation error.

Usage (inside the dtitr environment)
  python test_1a30.py --dtitr-dir <DTITR repo> --complex <...\\coreset\\1a30> [--full-davis]

Exit code 0 = PASS, 1 = FAIL.
"""
import argparse
import glob
import math
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import predict_dtitr as W  # noqa: E402

DAVIS_REF = [5.3902, 5.0025, 6.1794, 5.0338, 5.0109]   # first 5 pairs of test_cluster.csv, 24/10/2026
REF_SEQ_LEN = 198
REF_SMILES = "CC(C)CC(NC(=O)C(CC(=O)O)NC(=O)C(N)CCC(=O)O)C(=O)O"
REF_PKD = 5.0047        # CombiLabHUB reference, 24/10/2026 (Linux, TF 2.6.0 CPU)
EXPERIMENTAL_PKD = 4.30
TOL = 0.01


def authors_encoding(dtitr_dir):
    """Run the authors' own dataset_builder on the Davis data (as run_evaluation_model)."""
    src = os.path.join(dtitr_dir, "source")
    sys.path.insert(0, src)
    from dataset_builder_util import dataset_builder
    from layers_utils import add_reg_token
    j = lambda *p: os.path.join(dtitr_dir, *p)  # noqa: E731
    dp = {"data": j("data", "davis", "dataset", "davis_dataset_processed.csv"),
          "prot_dic": j("dictionary", "davis_prot_dictionary.txt"),
          "smiles_dic": j("dictionary", "davis_smiles_dictionary.txt"),
          "clusters": glob.glob(j("data", "davis", "clusters", "*")),
          "prot_bpe": [j("dictionary", "protein_codes_uniprot.txt"), j("dictionary", "subword_units_map_uniprot.csv")],
          "smiles_bpe": [j("dictionary", "drug_codes_chembl.txt"), j("dictionary", "subword_units_map_chembl.csv")]}
    P, S, K = dataset_builder(dp).transform_dataset(True, False, "Sequence", "SMILES", "Kd",
                                                    W.PROT_BPE_LEN, 1400, 0, W.SMILES_LEN)
    P = add_reg_token(P, W.PROT_DICT_BPE_LEN).numpy()
    S = add_reg_token(S, W.SMILES_DICT_LEN).numpy()
    test = [c for c in dp["clusters"] if "test" in os.path.basename(c)][0]
    import pandas as pd
    return dp["data"], P, S, np.asarray(K, dtype=float), pd.read_csv(test, header=None).iloc[:, 0].values


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dtitr-dir", required=True, help="DTITR repository")
    ap.add_argument("--complex", required=True, help="CASF-2016 folder of complex 1a30")
    ap.add_argument("--full-davis", action="store_true", help="also evaluate the whole Davis test set")
    args = ap.parse_args()
    dtitr = os.path.abspath(args.dtitr_dir)
    casf = os.path.abspath(args.complex)
    for s in ("_protein.pdb", "_ligand.mol2"):
        if not os.path.isfile(os.path.join(casf, "1a30" + s)):
            sys.exit("ERROR: file not found: " + os.path.join(casf, "1a30" + s))
    ok = True

    d, bad = W.check_model(dtitr)
    print("[1] Model %s\n    %s" % (d, "FAIL - missing or wrong MD5: " + ", ".join(bad) if bad else
                                    "PASS - MD5 " + ", ".join(W.MODEL_MD5.values())))
    if bad:
        print("\nRESULT: FAIL")
        sys.exit(1)

    import pandas as pd
    enc = W.Encoder(dtitr)
    data_csv, P, S, K, test_idx = authors_encoding(dtitr)
    davis = pd.read_csv(data_csv)
    pm = {s: enc.protein(s)[0] for s in davis.Sequence.unique()}
    sm = {s: enc.smiles(s)[0] for s in davis.SMILES.unique()}
    mp = np.stack([pm[s] for s in davis.Sequence])
    ms = np.stack([sm[s] for s in davis.SMILES])
    same = np.array_equal(mp, P) and np.array_equal(ms, S)
    ok = ok and same
    print("\n[2] Encoding of the %d Davis pairs (protein %d, SMILES %d tokens) vs the authors' dataset_builder\n    %s"
          % (len(davis), P.shape[1], S.shape[1], "PASS - identical" if same else "FAIL - differs (check subword_nmt / pandas)"))

    tf, model = W.load(dtitr)
    idx = test_idx[:5]
    p5 = W.predict(tf, model, [{"protein": P[i], "smiles": S[i]} for i in idx])
    good = np.allclose(p5, DAVIS_REF, atol=TOL)
    ok = ok and good
    print("\n[3] Davis test set, first 5 pairs: predicted %s\n    reference %s, experimental %s\n    %s"
          % (np.round(p5, 4).tolist(), DAVIS_REF, np.round(K[idx], 4).tolist(),
             "PASS - model loads and matches the reference" if good else "FAIL - check TensorFlow 2.6 (environment.yml)"))
    if args.full_davis:
        from scipy import stats
        from sklearn.metrics import mean_squared_error, r2_score
        sys.path.insert(0, os.path.join(dtitr, "source"))
        from utils import c_index
        pt = W.predict(tf, model, [{"protein": P[i], "smiles": S[i]} for i in test_idx])
        kt = K[test_idx]
        print("    whole Davis test set (%d pairs): MSE %.4f  RMSE %.4f  CI %.4f  R2 %.4f  Spearman %.4f"
              % (len(test_idx), mean_squared_error(kt, pt), math.sqrt(mean_squared_error(kt, pt)),
                 float(c_index(tf.constant(kt, tf.float32), tf.constant(pt, tf.float32))), r2_score(kt, pt),
                 stats.spearmanr(kt, pt)[0]))
        print("    CombiLabHUB 24/10/2026: MSE 0.1920  RMSE 0.4382  CI 0.9065  R2 0.7712  Spearman 0.7122")

    inp = W.build_inputs(enc, casf, "1a30")
    good = len(inp["sequence"]) == REF_SEQ_LEN and inp["smiles_str"] == REF_SMILES
    print("\n[4] 1a30 from the CASF-2016 files: sequence %d residues, SMILES %s\n    notes: %s\n    inputs %s"
          % (len(inp["sequence"]), inp["smiles_str"], inp["notes"] or "-", "PASS" if good else "FAIL - differ from the reference"))
    p = float(W.predict(tf, model, [inp])[0])
    good = good and math.isfinite(p) and abs(p - REF_PKD) <= TOL
    ok = ok and good
    print("    pKd %.4f (experimental %.2f) vs CombiLabHUB reference %.4f\n    %s"
          % (p, EXPERIMENTAL_PKD, REF_PKD, "PASS - matches the reference" if good else "FAIL - check the package versions"))
    print("    (DTITR was trained only on Davis kinases; ~5.0 is its 'non-binder' value)")

    print("\nRESULT:", "PASS" if ok else "FAIL")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
