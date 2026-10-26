"""DTITR (Monteiro et al., Comput. Biol. Med. 2022) - prediction for CombiLabHUB.

DTITR is a sequence-only model: it does NOT use the 3D structure of the complex.
Inputs of the model (one protein-ligand pair):
  1. protein - full amino-acid sequence, encoded with the authors' protein subword
               dictionary (BPE, dictionary/protein_codes_uniprot.txt +
               subword_units_map_uniprot.csv), truncated/padded to 556 tokens, plus the
               regression token Rp in front.
  2. ligand  - SMILES, encoded character by character with the authors' Davis
               dictionary (26 symbols, two-letter Br and Cl), padded to 72, plus the
               regression token Rs in front.

The trained model in the repository (model/dtitr_model) was trained ONLY on the Davis
kinase dataset (kinases x 68 inhibitors, pKd 5.0-10.8). On PDBbind/CASF-2016
complexes it is used outside its training domain.

How CombiLabHUB builds the inputs from a CASF-2016 complex folder
  - sequence: one letter per standard residue of <code>_protein.pdb (ATOM records,
    all chains in file order, concatenated). Non-standard residues are skipped
    (with them the authors' BPE lookup would fail and zero the whole sequence).
  - SMILES:   <code>_ligand.mol2 (or .sdf if the mol2 cannot be read) read by RDKit,
    hydrogens removed, charges neutralised (RDKit Uncharger: the 69 Davis SMILES are
    all neutral, PDBbind mol2 files carry ionised groups such as [NH3+] and [O-]),
    written as canonical SMILES WITHOUT stereochemistry, as in the authors'
    davis_dataset_processed.csv (no '@', '/', '\\').
  - Same encoding code as the authors' dataset_builder (data_conversion and
    encoding_bpe), with two fixes for molecules outside Davis, where the authors'
    code would stop with an error:
      * SMILES symbols not in the Davis dictionary (e.g. P, +, B, '.') -> token 0
        (padding), reported in the column 'notes';
      * SMILES longer than 72 symbols -> truncated to 72, reported in 'notes'.

Output CSV columns: pdbid, pKd_predicted (and a second file *_notes.csv with the
sequence length, SMILES and warnings of every complex).

Usage (inside the dtitr environment):
  python predict_dtitr.py --dtitr-dir <DTITR repo> -d <folder of complexes> -o predictions.csv
"""
import argparse
import codecs
import csv
import hashlib
import json
import os
import re
import sys
import time

os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "2")
import numpy as np  # noqa: E402

MODEL_MD5 = {".data-00000-of-00001": "69c9aca0c415bb54c63a1c01c3a8da4e",
             ".index": "a30a97cc47db04b22f908191a329e298"}   # model/dtitr_model, commit e8d5361
PROT_BPE_LEN = 556          # argument_parser.py defaults used by the authors' Evaluation
PROT_DICT_BPE_LEN = 16693
SMILES_LEN = 72
SMILES_DICT_LEN = 26
THREE = {"ALA": "A", "ARG": "R", "ASN": "N", "ASP": "D", "CYS": "C", "GLN": "Q", "GLU": "E", "GLY": "G",
         "HIS": "H", "ILE": "I", "LEU": "L", "LYS": "K", "MET": "M", "PHE": "F", "PRO": "P", "SER": "S",
         "THR": "T", "TRP": "W", "TYR": "Y", "VAL": "V"}


def md5(path):
    h = hashlib.md5()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def check_model(dtitr_dir):
    d = os.path.join(dtitr_dir, "model", "dtitr_model")
    bad = [n for n, h in MODEL_MD5.items() if not os.path.isfile(os.path.join(d, n)) or md5(os.path.join(d, n)) != h]
    return d, bad


# ---------------------------------------------------------------- inputs from files
def protein_sequence(pdb_path):
    """One letter per standard residue (ATOM records, chains in file order)."""
    seq, skipped, last = [], 0, None
    with open(pdb_path) as f:
        for line in f:
            if not line.startswith("ATOM"):
                continue
            key = (line[21], line[22:27])          # chain, residue number + insertion code
            if key == last:
                continue
            last = key
            aa = THREE.get(line[17:20].strip())
            if aa is None:
                skipped += 1
            else:
                seq.append(aa)
    return "".join(seq), skipped


def ligand_smiles(folder, code):
    from rdkit import Chem, RDLogger
    RDLogger.DisableLog("rdApp.*")
    mol = None
    for ext, reader in ((".mol2", Chem.MolFromMol2File), (".sdf", lambda p: Chem.MolFromMolFile(p))):
        p = os.path.join(folder, code + "_ligand" + ext)
        if os.path.isfile(p):
            mol = reader(p)
            if mol is not None:
                break
    if mol is None:
        return None, False
    from rdkit.Chem.MolStandardize import rdMolStandardize
    mol = Chem.RemoveHs(mol)
    charged = any(a.GetFormalCharge() for a in mol.GetAtoms())
    mol = rdMolStandardize.Uncharger().uncharge(mol)       # Davis SMILES are all neutral
    return Chem.MolToSmiles(mol, isomericSmiles=False), charged


# ---------------------------------------------------------------- authors' encoding
class Encoder:
    def __init__(self, dtitr_dir):
        dic = os.path.join(dtitr_dir, "dictionary")
        self.smiles_dict = json.load(open(os.path.join(dic, "davis_smiles_dictionary.txt")))
        self.multi = [k for k in self.smiles_dict if len(k) > 1]          # Br, Cl
        from subword_nmt.apply_bpe import BPE
        import pandas as pd
        self.bpe = BPE(codecs.open(os.path.join(dic, "protein_codes_uniprot.txt")), merges=-1, separator="")
        idx2word = pd.read_csv(os.path.join(dic, "subword_units_map_uniprot.csv"))["index"].values
        self.words2idx = dict(zip(idx2word, range(len(idx2word))))

    def protein(self, seq):
        """encoding_bpe() of the authors + add_reg_token (Rp = dict_len + 1 in front)."""
        words = self.bpe.process_line(seq).split()
        try:
            ids = np.asarray([self.words2idx[w] + 1 for w in words])
            unknown = False
        except KeyError:                                  # authors' behaviour: whole sequence -> [0]
            ids, unknown = np.array([0]), True
        n = len(ids)
        ids = np.pad(ids, (0, PROT_BPE_LEN - n)) if n < PROT_BPE_LEN else ids[:PROT_BPE_LEN]
        return np.concatenate([[PROT_DICT_BPE_LEN + 1], ids]).astype("int32"), n, unknown

    def smiles_tokens(self, smi):
        """Tokenisation of data_conversion(): two-letter keys (Br, Cl) found with re.finditer."""
        pos = sorted((m.start(), m.end() - m.start()) for k in self.multi for m in re.finditer(k, smi))
        starts = {p: l for p, l in pos}
        out, j = [], 0
        while j < len(smi):
            if j in starts:
                out.append(smi[j] + smi[j + starts[j] - 1])
                j += starts[j]
            else:
                out.append(smi[j])
                j += 1
        return out

    def smiles(self, smi):
        toks = self.smiles_tokens(smi)
        unknown = sorted({t for t in toks if t not in self.smiles_dict})
        ids = [self.smiles_dict.get(t, 0) for t in toks]
        n = len(ids)
        ids = (ids + [0] * (SMILES_LEN - n)) if n < SMILES_LEN else ids[:SMILES_LEN]
        return np.asarray([SMILES_DICT_LEN + 1] + ids, dtype="int32"), n, unknown


def build_inputs(enc, folder, code):
    notes = []
    seq, skipped = protein_sequence(os.path.join(folder, code + "_protein.pdb"))
    if skipped:
        notes.append("%d non-standard residues skipped" % skipped)
    smi, charged = ligand_smiles(folder, code)
    if charged:
        notes.append("ligand neutralised")
    if smi is None:
        raise ValueError("RDKit cannot read the ligand of " + code)
    p, n_p, unk_p = enc.protein(seq)
    if unk_p:
        notes.append("protein subword not in dictionary: sequence zeroed (authors' behaviour)")
    if n_p > PROT_BPE_LEN:
        notes.append("protein %d subwords truncated to %d" % (n_p, PROT_BPE_LEN))
    s, n_s, unk_s = enc.smiles(smi)
    if unk_s:
        notes.append("SMILES symbols not in Davis dictionary -> 0: " + " ".join(unk_s))
    if n_s > SMILES_LEN:
        notes.append("SMILES %d symbols truncated to %d" % (n_s, SMILES_LEN))
    return {"protein": p, "smiles": s, "sequence": seq, "smiles_str": smi, "notes": "; ".join(notes)}


# ---------------------------------------------------------------- model
def load(dtitr_dir):
    src = os.path.join(os.path.abspath(dtitr_dir), "source")
    sys.path.insert(0, src)
    import tensorflow as tf
    import tensorflow_addons as tfa
    import argument_parser
    import dtitr_model as M
    argv, sys.argv = sys.argv, [sys.argv[0]]
    FLAGS = argument_parser.argparser()
    sys.argv = argv
    opt = tfa.optimizers.RectifiedAdam(learning_rate=1e-04, beta_1=0.9, beta_2=0.999, epsilon=1e-08, weight_decay=1e-05)
    # same call as run_evaluation_model() of the authors
    model = M.build_dtitr_model(FLAGS, 3, 3, 1, 4, 4, 4, '', '', 512, 512, 128, 0.1, 'gelu', 3, [512, 512, 512], opt)
    model.load_weights(os.path.join(os.path.abspath(dtitr_dir), "model", "dtitr_model") + os.sep).expect_partial()
    return tf, model


def predict(tf, model, items, batch=32):
    P = np.stack([i["protein"] for i in items])
    S = np.stack([i["smiles"] for i in items])
    return model.predict([tf.constant(P), tf.constant(S)], batch_size=batch, verbose=0)[:, 0].astype(float)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dtitr-dir", required=True, help="DTITR repository (code, dictionary, model)")
    ap.add_argument("-d", "--data", required=True, help="folder with one sub-folder per complex")
    ap.add_argument("-o", "--output", default="predictions.csv")
    args = ap.parse_args()

    _, bad = check_model(args.dtitr_dir)
    if bad:
        sys.exit("ERROR: model files missing or with wrong MD5: " + ", ".join(bad))
    enc = Encoder(args.dtitr_dir)
    codes = sorted(c for c in os.listdir(args.data) if os.path.isdir(os.path.join(args.data, c)))
    items, ok_codes, failed = [], [], []
    for c in codes:
        try:
            items.append(build_inputs(enc, os.path.join(args.data, c), c))
            ok_codes.append(c)
        except Exception as e:  # noqa: BLE001
            failed.append((c, str(e)))
    if not items:
        sys.exit("ERROR: no complex could be prepared")
    t0 = time.time()
    tf, model = load(args.dtitr_dir)
    preds = predict(tf, model, items)
    os.makedirs(os.path.dirname(os.path.abspath(args.output)), exist_ok=True)
    with open(args.output, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["pdbid", "pKd_predicted"])
        for c, p in zip(ok_codes, preds):
            w.writerow([c, "%.4f" % p])
    notes_path = os.path.splitext(args.output)[0] + "_notes.csv"
    with open(notes_path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["pdbid", "sequence_length", "smiles", "notes"])
        for c, i in zip(ok_codes, items):
            w.writerow([c, len(i["sequence"]), i["smiles_str"], i["notes"]])
        for c, e in failed:
            w.writerow([c, "", "", "FAILED: " + e])
    print("DTITR: %d complexes scored in %.1f s -> %s (notes: %s)" % (len(ok_codes), time.time() - t0, args.output, notes_path))
    if failed:
        print("  %d failed (see the notes file)" % len(failed))


if __name__ == "__main__":
    main()
