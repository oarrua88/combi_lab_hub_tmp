"""DEAttentionDTA installation test with complex 1a30 (HIV-1 protease).

What it checks
  1. The authors' pre-processed 1a30 (row of data/seq_data_core.csv in the
     DEAttentionDTA repository) gives pKd 6.3185, the value in the authors'
     src/kfold_result.csv (6.3184166). This checks the 10 fold models and PyTorch.
  2. The CASF-2016 files from PDBbind (SMILES from 1a30_ligand.mol2 with Open
     Babel, sequence from 1a30_protein.pdb, pocket from 1a30_pocket.pdb) give the
     same SMILES and protein sequence as the authors, and pKd 6.2026. The small
     difference comes from the pocket: the CASF-2016 pocket file has 51 residues,
     the authors' pocket (from PDBbind v2020) 56.
The experimental value is 4.30.

Usage (inside the deattentiondta environment)
  python test_1a30.py --dea-dir <DEAttentionDTA folder> --complex <...\\coreset\\1a30>

Exit code 0 = PASS, 1 = FAIL.
"""
import argparse
import ast
import os
import sys

import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import predict_deattentiondta as W  # noqa: E402

REF_AUTHORS_FILES = 6.3185
REF_CASF_FILES = 6.2026
EXPERIMENTAL_PKD = 4.30
TOL = 0.01


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dea-dir", required=True, help="DEAttentionDTA folder (with src/ and data/)")
    ap.add_argument("--complex", required=True, help="CASF-2016 folder of complex 1a30")
    args = ap.parse_args()

    dea = os.path.abspath(args.dea_dir)
    casf = os.path.abspath(args.complex)
    for f in (os.path.join(dea, "data", "seq_data_core.csv"),
              os.path.join(casf, "1a30_protein.pdb"), os.path.join(casf, "1a30_pocket.pdb"), os.path.join(casf, "1a30_ligand.mol2")):
        if not os.path.isfile(f):
            sys.exit("ERROR: file not found: " + f)

    torch, models, D = W.load(dea)
    row = pd.read_csv(os.path.join(dea, "data", "seq_data_core.csv")).set_index("PDBname").loc["1a30"]
    ok = True

    p1, _ = W.score(torch, models, D, row["Smile"], row["Sequence"], ast.literal_eval(row["Position"]))
    smi, src, seq, pos = W.prepare(casf, "1a30")
    p2, _ = W.score(torch, models, D, smi, seq, pos)

    same_smi, same_seq = smi == row["Smile"], seq == row["Sequence"]
    print("Inputs built from the CASF-2016 files:")
    print("    SMILES (Open Babel, from %s): %s" % (os.path.basename(src), "same as the authors" if same_smi else "DIFFERENT from the authors"))
    print("    protein sequence (%d residues): %s" % (len(seq), "same as the authors" if same_seq else "DIFFERENT from the authors"))
    print("    pocket residues: %d (authors: %d)" % (len(pos), len(ast.literal_eval(row["Position"]))))
    ok = ok and same_smi and same_seq

    for label, pred, ref in (("[1] Authors' pre-processed 1a30 (data/seq_data_core.csv)", p1, REF_AUTHORS_FILES),
                             ("[2] CASF-2016 1a30 (mol2 + protein.pdb + pocket.pdb)", p2, REF_CASF_FILES)):
        good = abs(pred - ref) <= TOL
        ok = ok and good
        print("\n%s: pKd %.4f (reference %.4f, experimental %.2f)" % (label, pred, ref, EXPERIMENTAL_PKD))
        print("    PASS - matches the reference" if good else "    FAIL - check the package versions (environment.yml)")

    print("\nRESULT:", "PASS" if ok else "FAIL")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
