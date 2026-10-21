"""Predict binding affinity (pKd) with DEAttentionDTA (2024) for many complexes.

DEAttentionDTA is a sequence-only model: it reads the protein amino-acid
sequence, the positions of the binding-pocket residues inside that sequence,
and the ligand SMILES string. No 3D coordinates reach the network. The
prediction is the average of the 10 cross-validation models (Fold 1..10) the
authors ship in src/model/ (version 1, "with active-site information", the one
evaluated on CASF-2016).

The authors' test.py only runs on their own pre-processed CSV files. This wrapper
builds the three inputs from a PDBbind-style folder, one complex per sub-folder:
  ligand SMILES     <code>_ligand.smi (first word) or, if missing,
                    <code>_ligand.mol2 converted with Open Babel (as the authors'
                    pre-code/sdf_to_smi.py does)
  protein sequence  <code>_protein.pdb (standard residues of ATOM records)
  pocket positions  residues of <code>_pocket.pdb mapped onto that sequence
The PDB parsing uses fixed PDB columns, as in the corrected version by Eaves et
al. (github.com/jeavesj/DEAttentionDTA); the authors' original split() parsing
breaks when a residue number touches the chain ID or the chain ID is missing.
CASF-2016 pocket files have no chain IDs; see pocket_positions().

Usage (inside the deattentiondta environment)
  python predict_deattentiondta.py --dea-dir <DEAttentionDTA folder> -d <complexes folder> [-o predictions.csv]
"""
import argparse
import os
import sys
import warnings

import pandas as pd

AA = {'ALA': 'A', 'CYS': 'C', 'ASP': 'D', 'GLU': 'E', 'PHE': 'F', 'GLY': 'G', 'HIS': 'H', 'ILE': 'I',
      'LYS': 'K', 'LEU': 'L', 'MET': 'M', 'ASN': 'N', 'PRO': 'P', 'GLN': 'Q', 'ARG': 'R', 'SER': 'S',
      'THR': 'T', 'VAL': 'V', 'TYR': 'Y', 'TRP': 'W'}
MAX_SEQ_LEN = 1024
MAX_SMI_LEN = 256
N_FOLDS = 10


def load(dea_dir, version="src"):
    """Import the authors' model and encoders and load the 10 fold models (CPU)."""
    src = os.path.join(os.path.abspath(dea_dir), version)
    if not os.path.isfile(os.path.join(src, "bestmodel.py")):
        sys.exit("ERROR: %s does not look like the DEAttentionDTA folder (%s/bestmodel.py missing)" % (dea_dir, version))
    warnings.filterwarnings("ignore")
    sys.path.insert(0, src)
    import torch
    import bestmodel
    import Dataset as D
    models = []
    for i in range(1, N_FOLDS + 1):
        m = bestmodel.MyModule()
        m.load_state_dict(torch.load(os.path.join(src, "model", "Fold %d best_model.ckpt" % i), map_location="cpu"))
        m.eval()
        models.append(m)
    return torch, models, D


def protein_sequence(protein_pdb):
    """Sequence of standard residues and the residue list [(chain, resnum, resname)] in sequence order.

    Fixed PDB columns are used (chain = column 22, residue number = 23-26), as in
    the corrected version by Eaves et al.
    """
    seq, residues, seen = "", [], set()
    for line in open(protein_pdb):
        if line.startswith("ATOM"):
            res, chain, num = line[17:20].strip(), line[21].strip(), line[22:26].strip()
            if res in AA and (chain, num) not in seen:
                seen.add((chain, num))
                residues.append((chain, num, res))
                seq += AA[res]
    return seq, residues


def pocket_positions(pocket_pdb, residues):
    """1-based positions of the pocket residues inside the protein sequence.

    CASF-2016 pocket files have NO chain IDs, and in multi-chain proteins the same
    residue number appears once per chain (1a30: chains A and B of HIV-1
    protease). A residue with a chain ID is matched by (chain, number); one
    without is matched to an unused protein residue with the same number and
    name, preferring the first one after the previous pocket residue (pocket
    files list chain A first, then chain B).
    """
    by_key = {(c, n): i + 1 for i, (c, n, r) in enumerate(residues)}
    used, pos, last = set(), [], None
    for line in open(pocket_pdb):
        if not line.startswith("ATOM"):
            continue
        res, chain, num = line[17:20].strip(), line[21].strip(), line[22:26].strip()
        if res not in AA or (chain, num) == last:
            continue
        last = (chain, num)
        idx = by_key.get((chain, num)) if chain else None
        if idx is None:
            cands = [i + 1 for i, (c, n, r) in enumerate(residues) if n == num and r == res and i + 1 not in used]
            if not cands:
                cands = [i + 1 for i, (c, n, r) in enumerate(residues) if n == num and i + 1 not in used]
            if not cands:
                raise ValueError("pocket residue %s %s not found in the protein" % (res, num))
            prev = pos[-1] if pos else 0
            after = [i for i in cands if i > prev]
            idx = after[0] if after else cands[0]
        used.add(idx)
        pos.append(idx)
    return pos


def ligand_smiles(folder, code):
    """Return (SMILES, source file): .smi if present, else Open Babel conversion of the .mol2."""
    smi = os.path.join(folder, code + "_ligand.smi")
    if os.path.isfile(smi):
        with open(smi) as f:
            words = f.read().split()
        if words:
            return words[0], smi
    mol2 = os.path.join(folder, code + "_ligand.mol2")
    if os.path.isfile(mol2):
        from openbabel import pybel
        pybel.ob.obErrorLog.SetOutputLevel(0)
        mol = next(pybel.readfile("mol2", mol2), None)
        if mol is not None:
            return mol.write("smi").split()[0], mol2
    return None, None


def score(torch, models, D, smiles, sequence, positions):
    """Average pKd of the 10 fold models for one complex."""
    smi = torch.tensor(D.label_smiles(smiles, MAX_SMI_LEN)).long().unsqueeze(0)
    seq = torch.tensor(D.label_seq(sequence, MAX_SEQ_LEN)).long().unsqueeze(0)
    poc = torch.tensor(D.label_seq(D.position_seq(sequence, positions), MAX_SEQ_LEN)).long().unsqueeze(0)
    with torch.no_grad():
        preds = [float(m(seq, smi, poc).reshape(-1)[0]) for m in models]
    return sum(preds) / len(preds), preds


def prepare(folder, code):
    """(SMILES, smiles source, sequence, pocket positions) for one complex folder."""
    smi, src = ligand_smiles(folder, code)
    if smi is None:
        raise ValueError("no readable ligand (.smi or .mol2)")
    seq, residues = protein_sequence(os.path.join(folder, code + "_protein.pdb"))
    pos = pocket_positions(os.path.join(folder, code + "_pocket.pdb"), residues)
    return smi, src, seq, pos


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dea-dir", required=True, help="DEAttentionDTA folder (with src/bestmodel.py and src/model)")
    ap.add_argument("-d", "--directory", required=True, help="folder with one sub-folder per complex")
    ap.add_argument("-o", "--output", default="predictions.csv", help="output CSV (default: predictions.csv)")
    args = ap.parse_args()

    torch, models, D = load(args.dea_dir)
    rows = []
    for code in sorted(os.listdir(args.directory)):
        folder = os.path.join(args.directory, code)
        if not (os.path.isfile(os.path.join(folder, code + "_protein.pdb")) and
                os.path.isfile(os.path.join(folder, code + "_pocket.pdb"))):
            continue
        try:
            smi, src, seq, pos = prepare(folder, code)
            pred, folds = score(torch, models, D, smi, seq, pos)
        except Exception as e:  # e.g. a SMILES character outside the model's vocabulary
            print("Skipping %s: %s: %s" % (code, type(e).__name__, e))
            continue
        note = "sequence truncated to 1024" if len(seq) > MAX_SEQ_LEN else ""
        if len(smi) > MAX_SMI_LEN:
            note = (note + "; " if note else "") + "SMILES truncated to 256"
        rows.append([code, round(pred, 4)] + [round(p, 4) for p in folds] + [len(seq), len(pos), os.path.basename(src), smi, note])
        print("%s\t%.4f" % (code, pred))
    if not rows:
        sys.exit("ERROR: no complexes scored in " + args.directory)
    cols = ["pdbid", "pKd_predicted"] + ["fold%d" % i for i in range(1, N_FOLDS + 1)] + \
           ["seq_len", "pocket_residues", "ligand_source", "smiles", "note"]
    pd.DataFrame(rows, columns=cols).to_csv(args.output, index=False)
    print("Done: %d complexes -> %s" % (len(rows), os.path.abspath(args.output)))


if __name__ == "__main__":
    main()
