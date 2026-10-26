"""MMPD-DTA (Wang et al., J. Chem. Inf. Model. 2025) - prediction for CombiLabHUB.

The authors publish the model (result/best/best_model.pt) and their test sets already
converted to graphs (data/processed/data.zip), but not the script that builds the
inputs of a new complex. This wrapper rebuilds them from the raw files with the
featuriser of the same authors (create_data.py of DeepTGIN, removed from that
repository on 24/01/2025) plus the rules recovered from the authors' test2016.pt.
For complex 1a30 the rebuilt inputs are IDENTICAL to the authors' ones (node
features, edges and edge order, protein sequence); test_1a30.py checks it.

Inputs of the model (one complex):
  1. protein  - full sequence: one letter per residue of <code>_protein.pdb (ATOM
                records, chains in file order; non-standard residues -> X), encoded
                with the authors' dictionary "ABCDEFGHIKLMNOPQRSTUVWXYZ" -> 1..25,
                padded/truncated to 1000.
  2. ligand   - 2D graph of <code>_ligand.mol2 read by RDKit (hydrogens removed):
                108 atom features divided by their sum, bonds in both directions.
  3. complex  - "pocket-drug graph": heavy atoms of <code>_pocket.pdb without
                waters (RDKit), followed by the ligand atoms. Edges: covalent bonds
                of both molecules (both directions) + one edge pocket atom -> ligand
                atom for every pair closer than 6.0 A.

Output CSV columns: pdbid, pKd_predicted

Usage (inside the mmpd_dta environment):
  python predict_mmpd_dta.py --mmpd-dir <MMPD-DTA repo> -d <folder of complexes> -o predictions.csv
"""
import argparse
import hashlib
import os
import sys
import time

import numpy as np

MODEL_MD5 = "366d95ccc2f7fdf87ae70746cb03ce39"   # result/best/best_model.pt, commit 6992636
SEQ_VOC = "ABCDEFGHIKLMNOPQRSTUVWXYZ"
SEQ_DICT = {v: i + 1 for i, v in enumerate(SEQ_VOC)}
MAX_SEQ_LEN = 1000
CUTOFF = 6.0
THREE = {"ALA": "A", "ARG": "R", "ASN": "N", "ASP": "D", "CYS": "C", "GLN": "Q", "GLU": "E", "GLY": "G",
         "HIS": "H", "ILE": "I", "LEU": "L", "LYS": "K", "MET": "M", "PHE": "F", "PRO": "P", "SER": "S",
         "THR": "T", "TRP": "W", "TYR": "Y", "VAL": "V"}
SYMBOLS = ['C', 'N', 'O', 'S', 'F', 'Si', 'P', 'Cl', 'Br', 'Mg', 'Na', 'Ca', 'Fe', 'As', 'Al', 'I', 'B', 'V', 'K',
           'Tl', 'Yb', 'Sb', 'Sn', 'Ag', 'Pd', 'Co', 'Se', 'Ti', 'Zn', 'H', 'Li', 'Ge', 'Cu', 'Au', 'Ni', 'Cd', 'In',
           'Mn', 'Zr', 'Cr', 'Pt', 'Hg', 'Pb', 'Unknown']


def md5(path):
    h = hashlib.md5()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


# ---------------------------------------------------------------- featuriser
# Same as atom_features() in the authors' create_data.py (DeepTGIN repository).
def _ook(x, allowable):
    if x not in allowable:
        raise Exception("input {0} not in allowable set{1}:".format(x, allowable))
    return [x == s for s in allowable]


def _ook_unk(x, allowable):
    if x not in allowable:
        x = allowable[-1]
    return [x == s for s in allowable]


def atom_features(atom):
    f = (_ook_unk(atom.GetSymbol(), SYMBOLS)
         + _ook(atom.GetDegree(), list(range(11)))
         + _ook_unk(atom.GetTotalNumHs(), list(range(11)))
         + _ook_unk(atom.GetImplicitValence(), list(range(11)))
         + _ook_unk(str(atom.GetChiralTag()), ['CHI_UNSPECIFIED', 'CHI_TETRAHEDRAL_CW', 'CHI_TETRAHEDRAL_CCW',
                                              'CHI_OTHER', 'misc'])
         + _ook_unk(atom.GetFormalCharge(), [-5, -4, -3, -2, -1, 0, 1, 2, 3, 4, 5, 'misc'])
         + _ook_unk(atom.GetNumRadicalElectrons(), [0, 1, 2, 3, 4, 'misc'])
         + _ook_unk(str(atom.GetHybridization()), ['SP', 'SP2', 'SP3', 'SP3D', 'SP3D2', 'misc'])
         + [atom.IsInRing()] + [atom.GetIsAromatic()])
    f = np.array(f, dtype=float)
    return f / f.sum()


def _directed_edges(bond_pairs):
    import networkx as nx
    return [[a, b] for a, b in nx.Graph(bond_pairs).to_directed().edges]


def protein_sequence(protein_pdb):
    seen, seq = set(), []
    with open(protein_pdb) as f:
        for line in f:
            if line.startswith("ATOM"):
                key = (line[21], line[22:27])
                if key not in seen:
                    seen.add(key)
                    seq.append(THREE.get(line[17:20], "X"))
    return "".join(seq)


def encode_sequence(seq):
    x = np.zeros(MAX_SEQ_LEN, dtype=np.int64)
    for i, ch in enumerate(seq[:MAX_SEQ_LEN]):
        x[i] = SEQ_DICT[ch]
    return x


def build_inputs(protein_pdb, pocket_pdb, ligand_mol2):
    """Rebuild the three inputs of MMPD-DTA for one complex. Returns a dict of numpy arrays."""
    from rdkit import Chem, RDLogger
    RDLogger.DisableLog("rdApp.*")

    lig = Chem.MolFromMol2File(ligand_mol2)
    if lig is None:
        raise ValueError("RDKit cannot read " + ligand_mol2)
    with open(pocket_pdb) as f:
        block = "".join(l for l in f if not (l.startswith(("ATOM", "HETATM")) and l[17:20] == "HOH"))
    poc = Chem.MolFromPDBBlock(block)
    if poc is None:
        raise ValueError("RDKit cannot read " + pocket_pdb)

    xt = np.array([atom_features(a) for a in lig.GetAtoms()], dtype=np.float32)
    et = _directed_edges([[b.GetBeginAtomIdx(), b.GetEndAtomIdx()] for b in lig.GetBonds()])

    n = poc.GetNumAtoms()
    xp = np.array([atom_features(a) for a in poc.GetAtoms()], dtype=np.float32)
    xs = np.vstack([xp, xt])
    cm = Chem.CombineMols(poc, lig)
    es = _directed_edges([[b.GetBeginAtomIdx(), b.GetEndAtomIdx()] for b in cm.GetBonds()])
    pp = poc.GetConformer().GetPositions()
    lp = lig.GetConformer().GetPositions()
    d = np.linalg.norm(pp[:, None, :] - lp[None, :, :], axis=2)
    es += [[i, j + n] for i in range(n) for j in range(lig.GetNumAtoms()) if d[i, j] < CUTOFF]

    seq = protein_sequence(protein_pdb)
    return {"x_s": xs, "edge_index_s": np.array(es, dtype=np.int64).T,
            "x_t": xt, "edge_index_t": np.array(et, dtype=np.int64).T,
            "protein": encode_sequence(seq), "sequence": seq}


# ---------------------------------------------------------------- authors' graphs
def authors_inputs(test_pt, code):
    """Read one complex from the authors' test2016.pt/test2013.pt WITHOUT unpickling
    (pickletools for the names, raw little-endian storages for the tensors)."""
    import pickletools
    import zipfile
    z = zipfile.ZipFile(test_pt)
    pref = z.namelist()[0].split("/")[0]
    pkl = z.read(pref + "/data.pkl")
    toks = [str(a) for op, a, _ in pickletools.genops(pkl) if a is not None and
            op.name not in ("BINPUT", "LONG_BINPUT", "MEMOIZE", "BINGET", "LONG_BINGET")]
    i = toks.index("name")
    raw = lambda k, dt: np.frombuffer(z.read("%s/data/%d" % (pref, k)), dtype=dt)
    ns = len(raw(6, "<i8")) - 1
    names = toks[i + 1:i + 1 + ns]
    if code not in names:
        return None
    j = names.index(code)
    sl = [raw(k, "<i8") for k in range(6, 13)]   # edge_index_s, x_s, edge_index_t, x_t, y_s, protein, name
    ei_s, x_s, ei_t, x_t = raw(0, "<i8").reshape(2, -1), raw(1, "<f4").reshape(-1, 108), \
        raw(2, "<i8").reshape(2, -1), raw(3, "<f4").reshape(-1, 108)
    return {"x_s": x_s[sl[1][j]:sl[1][j + 1]], "edge_index_s": ei_s[:, sl[0][j]:sl[0][j + 1]],
            "x_t": x_t[sl[3][j]:sl[3][j + 1]], "edge_index_t": ei_t[:, sl[2][j]:sl[2][j + 1]],
            "protein": raw(5, "<i8").reshape(-1, MAX_SEQ_LEN)[j], "y": float(raw(4, "<f4")[j])}


# ---------------------------------------------------------------- model
def load(mmpd_dir, model_path=None, check_md5=True):
    mmpd_dir = os.path.abspath(mmpd_dir)
    if not os.path.isfile(os.path.join(mmpd_dir, "model.py")):
        sys.exit("ERROR: %s does not look like the MMPD-DTA repository (no model.py)" % mmpd_dir)
    model_path = model_path or os.path.join(mmpd_dir, "result", "best", "best_model.pt")
    if not os.path.isfile(model_path):
        sys.exit("ERROR: model not found: " + model_path)
    if check_md5 and md5(model_path) != MODEL_MD5:
        sys.exit("ERROR: MD5 of %s is not %s" % (model_path, MODEL_MD5))
    if mmpd_dir not in sys.path:
        sys.path.insert(0, mmpd_dir)
    import torch
    from model import MMPD_DTA   # authors' model.py
    model = MMPD_DTA()
    model.load_state_dict(torch.load(model_path, map_location="cpu", weights_only=True))
    model.eval()
    return torch, model


def predict(torch, model, inp):
    """Score one complex (inputs from build_inputs or authors_inputs)."""
    from types import SimpleNamespace
    xs = torch.tensor(np.asarray(inp["x_s"], dtype=np.float32))
    xt = torch.tensor(np.asarray(inp["x_t"], dtype=np.float32))
    data = SimpleNamespace(
        x_s=xs, edge_index_s=torch.tensor(np.asarray(inp["edge_index_s"], dtype=np.int64)),
        x_t=xt, edge_index_t=torch.tensor(np.asarray(inp["edge_index_t"], dtype=np.int64)),
        x_s_batch=torch.zeros(xs.shape[0], dtype=torch.long),
        x_t_batch=torch.zeros(xt.shape[0], dtype=torch.long),
        protein=torch.tensor(np.asarray(inp["protein"], dtype=np.int64)).reshape(1, -1))
    with torch.no_grad():
        return float(model(data).reshape(-1)[0])


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--mmpd-dir", required=True, help="MMPD-DTA repository (with model.py and result/best/best_model.pt)")
    ap.add_argument("-d", "--dir", required=True, help="folder with one sub-folder per complex")
    ap.add_argument("-o", "--out", default="predictions.csv")
    args = ap.parse_args()

    torch, model = load(args.mmpd_dir)
    rows, skipped = [], []
    t0 = time.time()
    for code in sorted(os.listdir(args.dir)):
        d = os.path.join(args.dir, code)
        files = [os.path.join(d, code + s) for s in ("_protein.pdb", "_pocket.pdb", "_ligand.mol2")]
        if not all(os.path.isfile(f) for f in files):
            continue
        try:
            rows.append((code, predict(torch, model, build_inputs(*files))))
        except Exception as e:   # noqa: BLE001
            skipped.append("%s (%s)" % (code, e))
    import csv
    os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
    with open(args.out, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["pdbid", "pKd_predicted"])
        w.writerows([(c, "%.6f" % p) for c, p in rows])
    print("Scored %d complexes in %.1f s -> %s" % (len(rows), time.time() - t0, args.out))
    if skipped:
        print("WARNING: skipped %d: %s" % (len(skipped), "; ".join(skipped)))


if __name__ == "__main__":
    main()
