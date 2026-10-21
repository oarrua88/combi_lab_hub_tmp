"""DeepBindGCN_RG - affinity prediction for a folder of protein-ligand complexes (CPU).

DeepBindGCN (Zhang et al., 2023) does not use the 3D pose of the ligand: it combines a
GCN on the ligand's 2D graph (from a SMILES string, 78 atom features) with a GCN on a
residue graph of the pocket (C-alpha atoms closer than 5 A, 30-dimensional residue
vectors from aa_vec_dic.npy). DeepBindGCN_RG is the regression model (pKd).

This wrapper reproduces the authors' pipeline of DeepBindGCN_RG_example:
  1. pocket = residues with any atom within 8 A of any ligand atom
     (pocket/extract_pocket.py; the ligand from <code>_ligand.mol2);
  2. pocket graph and node features (read_smi_protein_nnn_usage.py: pdb_graph);
  3. ligand graph from SMILES (all_file/read_smi_protein_nnn.py: smile_to_graph); the
     SMILES comes from <code>_ligand.smi if present, else from the .mol2 with RDKit;
  4. the trained model full_model_out2000_RG.model (GitHub release v1.0.0; it was saved
     in training mode, and the authors' script switches it to eval mode, as here).
The authors' functions are re-implemented line by line (their scripts work on fixed
folders and file names, and read every input with glob); see INSTALL.md.

The model is a whole pickled GCNNet from PyTorch Geometric 1.x. Its weights are loaded
into the authors' models/gcn.py GCNNet, with every GCNConv replaced by OldGCNConv,
an exact copy of the PyG 1.x layer: x @ W, self-loops, normalisation by the degree of
the *source* node (current PyG uses the target node; the pocket graph is directed, so
this matters: for 1a30, 4.4640 with the original layer vs 6.4782 with the current
one), sum aggregation, + bias.

Usage (inside the deepbindgcn environment)
  python predict_deepbindgcn.py --dbg-dir <DeepBindGCN folder> --model <full_model_out2000_RG.model>
                                -d <complexes folder> [-o predictions.csv]
"""
import argparse
import os
import sys
import warnings

warnings.filterwarnings("ignore")

import numpy as np

RG = "DeepBindGCN_RG_example"


# ---------------------------------------------------------------- PyG 1.x GCNConv
def old_gcn_conv_class():
    import torch

    class OldGCNConv(torch.nn.Module):
        """GCNConv of PyTorch Geometric 1.x (improved=False, cached=False, normalize=True)."""

        def __init__(self, weight, bias):
            super().__init__()
            self.weight = torch.nn.Parameter(weight.clone())     # (in, out)
            self.bias = torch.nn.Parameter(bias.clone())

        def forward(self, x, edge_index):
            n = x.size(0)
            x = x @ self.weight
            ei = edge_index
            w = torch.ones(ei.size(1), dtype=x.dtype)
            # add_remaining_self_loops(fill_value=1)
            mask = ei[0] != ei[1]
            loop = torch.arange(n, dtype=ei.dtype)
            ei = torch.cat([ei[:, mask], torch.stack([loop, loop])], dim=1)
            w = torch.cat([w[mask], torch.ones(n, dtype=x.dtype)])
            row, col = ei
            deg = torch.zeros(n, dtype=x.dtype).index_add_(0, row, w)
            dis = deg.pow(-0.5)
            dis[torch.isinf(dis)] = 0
            norm = dis[row] * w * dis[col]
            out = torch.zeros_like(x).index_add_(0, col, norm.view(-1, 1) * x[row])
            return out + self.bias

    return OldGCNConv


def load_model(dbg_dir, model_path):
    import torch
    ex = os.path.join(dbg_dir, RG)
    if ex not in sys.path:
        sys.path.insert(0, ex)
    try:
        old = torch.load(model_path, map_location="cpu", weights_only=False)
    except TypeError:
        old = torch.load(model_path, map_location="cpu")
    sd = old.state_dict()
    from models.gcn import GCNNet                    # authors' architecture
    import contextlib, io
    with contextlib.redirect_stdout(io.StringIO()):  # GCNNet prints during __init__
        net = GCNNet()
    Old = old_gcn_conv_class()
    for name in ("conv1", "conv2", "conv3", "conv4", "conv1_xt", "conv2_xt", "conv3_xt", "conv4_xt"):
        setattr(net, name, Old(sd[name + ".weight"], sd[name + ".bias"]))
    rest = {k: v for k, v in sd.items() if not k.startswith("conv")}
    missing = net.load_state_dict(rest, strict=False)
    left = [k for k in missing.missing_keys if not k.startswith("conv")]
    if left or missing.unexpected_keys:
        raise RuntimeError("model parameters do not match: %s %s" % (left, missing.unexpected_keys))
    net.eval()
    return net


# ---------------------------------------------------------------- authors' featurisation
LIG_SYMBOLS = ['C', 'N', 'O', 'S', 'F', 'Si', 'P', 'Cl', 'Br', 'Mg', 'Na', 'Ca', 'Fe', 'As', 'Al', 'I', 'B', 'V',
               'K', 'Tl', 'Yb', 'Sb', 'Sn', 'Ag', 'Pd', 'Co', 'Se', 'Ti', 'Zn', 'H', 'Li', 'Ge', 'Cu', 'Au', 'Ni',
               'Cd', 'In', 'Mn', 'Zr', 'Cr', 'Pt', 'Hg', 'Pb', 'Unknown']
R11 = list(range(11))


def _onek(x, allowed):
    if x not in allowed:
        raise ValueError("input {0} not in allowable set{1}:".format(x, allowed))
    return [x == s for s in allowed]


def _onek_unk(x, allowed):
    if x not in allowed:
        x = allowed[-1]
    return [x == s for s in allowed]


def atom_features(atom):
    return np.array(_onek_unk(atom.GetSymbol(), LIG_SYMBOLS) + _onek(atom.GetDegree(), R11) +
                    _onek_unk(atom.GetTotalNumHs(), R11) + _onek_unk(atom.GetImplicitValence(), R11) +
                    [atom.GetIsAromatic()])


def smile_to_graph(smile):
    import networkx as nx
    from rdkit import Chem, RDLogger
    RDLogger.DisableLog("rdApp.*")      # GetImplicitValence() deprecation messages
    mol = Chem.MolFromSmiles(smile)
    if mol is None:
        raise ValueError("RDKit cannot read the SMILES %s" % smile)
    feats = []
    for atom in mol.GetAtoms():
        f = atom_features(atom)
        feats.append(f / sum(f))
    edges = [[b.GetBeginAtomIdx(), b.GetEndAtomIdx()] for b in mol.GetBonds()]
    g = nx.Graph(edges).to_directed()
    return mol.GetNumAtoms(), feats, [[e1, e2] for e1, e2 in g.edges]


def ligand_smiles(folder, code):
    smi = os.path.join(folder, code + "_ligand.smi")
    if os.path.isfile(smi):
        return open(smi).read().split()[0], "smi"
    from rdkit import Chem
    m = Chem.MolFromMol2File(os.path.join(folder, code + "_ligand.mol2"))
    if m is None:
        raise ValueError("RDKit cannot read %s_ligand.mol2" % code)
    return Chem.MolToSmiles(m), "mol2"


def _clean(line):
    # authors: blank the alternate-location column and skip altloc B
    alt = line[16] if len(line) > 16 else " "
    if len(line) > 16:
        line = line[:16] + " " + line[17:]
    return line, alt


def extract_pocket(protein_pdb, ligand_mol2, cutoff=8.0):
    """pocket/extract_pocket.py: lines of residues with any atom < 8 A from any ligand atom."""
    atoms, keys, coords = [], [], []
    for line in open(protein_pdb):
        line, alt = _clean(line)
        p = line.split()
        if p and p[0] == "ATOM" and alt != "B" and len(p) > 3 and p[3] != "UNK":
            keys.append(p[3] + line[22:26].replace(" ", "") + line[21:22])
            coords.append([float(line[30:38]), float(line[38:46]), float(line[46:54])])
            atoms.append(line)
    lig, inside = [], False
    for line in open(ligand_mol2):
        s = line.strip()
        if s == "@<TRIPOS>ATOM":
            inside = True
            continue
        if s.startswith("@<TRIPOS>"):
            inside = False
        if inside and s:
            q = s.split()
            lig.append([float(q[2]), float(q[3]), float(q[4])])
    a, b = np.array(coords), np.array(lig)
    d = np.sqrt(((a[:, None, :] - b[None, :, :]) ** 2).sum(-1))
    close = {keys[i] for i in np.where((d < cutoff).any(1))[0]}
    return [ln for ln, k in zip(atoms, keys) if k in close]


def pdb_graph(pocket_lines, aa_dict, cutoff=5.0):
    """read_smi_protein_nnn_usage.py: pdb_graph() on the pocket lines."""
    pos, name = {}, {}
    for line in pocket_lines:
        line, alt = _clean(line)
        p = line.split()
        if p and p[0] == "ATOM" and alt != "B" and line.find(" HOH ") == -1 and p[2] == "CA" and p[3] != "UNK":
            key = line[4:11] + line[21:22]
            pos[key] = np.array([float(line[30:38]), float(line[38:46]), float(line[46:54])])
            name[key] = line[17:26]
    pairs, uniq = [], []
    for k1, v1 in pos.items():
        for k2, v2 in pos.items():
            if k2 > k1 and np.sqrt(((v1 - v2) ** 2).sum()) < cutoff:
                pairs.append([name[k1], name[k2]])
                uniq += [name[k1], name[k2]]
    uniq = sorted(set(uniq))          # authors: list(set(...)), arbitrary order; the model is order-invariant
    idx = {u: i for i, u in enumerate(uniq)}
    edges = [[idx[a], idx[b]] for a, b in pairs]
    feats = [aa_dict[u[0:3]] for u in uniq]
    return len(uniq), feats, edges


def predict_complex(net, aa_dict, protein_pdb, ligand_mol2, smiles):
    import torch
    from torch_geometric.data import Data, Batch
    c, f, e = smile_to_graph(smiles)
    pocket = extract_pocket(protein_pdb, ligand_mol2)
    cp, fp, ep = pdb_graph(pocket, aa_dict)
    if cp == 0:
        raise ValueError("empty pocket graph")
    lig = Batch.from_data_list([Data(x=torch.Tensor(np.array(f, dtype=np.float32)),
                                     edge_index=torch.LongTensor(e).reshape(-1, 2).t().contiguous())])
    poc = Batch.from_data_list([Data(x=torch.Tensor(np.array(fp, dtype=np.float32)),
                                     edge_index=torch.LongTensor(ep).reshape(-1, 2).t().contiguous())])
    from torch_geometric.nn import global_max_pool as gmp
    with torch.no_grad():
        # GCNNet.forward() of models/gcn.py, for one complex (its pocket DataLoader loop
        # only batches data.target; dropout is off in eval mode)
        x = lig.x
        for conv in (net.conv1, net.conv2, net.conv3, net.conv4):
            x = net.relu(conv(x, lig.edge_index))
        x = gmp(x, lig.batch)
        x = net.dropout(net.fc_g2(net.relu(net.fc_g1(x))))
        xt = poc.x
        for conv in (net.conv1_xt, net.conv2_xt, net.conv3_xt, net.conv4_xt):
            xt = net.relu(conv(xt, poc.edge_index))
        xt = gmp(xt, poc.batch)
        xt = net.dropout(net.fc_g2_xt(net.relu(net.fc_g1_xt(xt))))
        xc = torch.cat((x, xt), 1)
        xc = net.relu(net.fc1(xc))
        xc = net.dropout(net.relu(net.fc2(xc)))
        return float(net.out(xc).reshape(-1)[0]), cp, len(pocket)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dbg-dir", required=True, help="DeepBindGCN folder (contains DeepBindGCN_RG_example/)")
    ap.add_argument("--model", required=True, help="full_model_out2000_RG.model (GitHub release v1.0.0)")
    ap.add_argument("-d", "--directory", required=True, help="folder with one sub-folder per complex")
    ap.add_argument("-o", "--output", default="predictions.csv", help="output CSV (default: predictions.csv)")
    a = ap.parse_args()
    import pandas as pd
    dd = os.path.abspath(a.dbg_dir)
    net = load_model(dd, os.path.abspath(a.model))
    aa = np.load(os.path.join(dd, RG, "aa_vec_dic.npy"), allow_pickle=True).item()
    root = os.path.abspath(a.directory)
    codes = sorted(d for d in os.listdir(root) if os.path.isdir(os.path.join(root, d)))
    rows = []
    for n, code in enumerate(codes, 1):
        f = os.path.join(root, code)
        try:
            smi, src = ligand_smiles(f, code)
            p, nres, _ = predict_complex(net, aa, os.path.join(f, code + "_protein.pdb"),
                                         os.path.join(f, code + "_ligand.mol2"), smi)
            rows.append((code, round(p, 4), nres, src, smi, ""))
            print("[%d/%d] %s  pKd %.4f" % (n, len(codes), code, p))
        except Exception as e:                           # noqa: BLE001
            rows.append((code, None, None, "", "", str(e).splitlines()[0][:200]))
            print("[%d/%d] %s  ERROR: %s" % (n, len(codes), code, rows[-1][-1]))
    out = pd.DataFrame(rows, columns=["pdbid", "pKd_predicted", "pocket_residues", "ligand_source", "smiles", "error"])
    os.makedirs(os.path.dirname(os.path.abspath(a.output)), exist_ok=True)
    out.to_csv(a.output, index=False)
    print("Done: %d complexes (%d errors) -> %s" % (len(out), out.pKd_predicted.isna().sum(), a.output))


if __name__ == "__main__":
    main()
