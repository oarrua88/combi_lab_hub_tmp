"""Predict binding affinity (pKd) with egGNN (Jiao et al., IEEE BIBM 2021) for many complexes.

egGNN (edge-gated graph neural network) builds two graphs: the ligand's 2D
molecular graph, made from a SMILES string, and a residue graph of the protein
binding pocket (residue centres closer than 11 A are connected). It does not use
the ligand's 3D pose.

The authors' run_egGNN.py scores one SMILES + one .pdb at a time and appends the
result to a file called "eggnn". This wrapper scores a folder of complexes, one
protein-ligand pair per sub-folder, with the authors' graph builder
(egGNN/feat.py) and trained checkpoint, and writes a CSV.

Usage (inside the eggnn environment)
  python predict_eggnn.py --eggnn-dir <egGNN folder> -d <complexes folder> [-o predictions.csv]

Each complex needs:
  protein  <code>_pocket.pdb   (default; --protein-file protein uses <code>_protein.pdb)
  ligand   <code>_ligand.smi   (first word = SMILES) or, if missing,
           <code>_ligand.mol2 / <code>_ligand.sdf, converted to SMILES with RDKit

Use the POCKET file. The authors' README says "--protein **.pdb", but with the
full protein egGNN gives PCC 0.071 on CASF-2016; with the pocket, 0.669
(Eaves et al. 2026, github.com/jeavesj/egGNN). See INSTALL.md.
"""
import argparse
import os
import pickle
import sys
import types
import warnings

import pandas as pd

DEFAULT_CHECKPOINT = "16-8596.sav"  # the one used by the authors' egGNN_pipeline.py


class _Unpickler(pickle.Unpickler):
    def find_class(self, module, name):
        if module == "__main__":
            module = "egGNN.model"
        return super().find_class(module, name)


_PickleFromModel = types.ModuleType("_pickle_from_egGNN_model")
_PickleFromModel.__dict__.update({k: getattr(pickle, k) for k in dir(pickle) if not k.startswith("__")})
_PickleFromModel.Unpickler = _Unpickler


def load(eggnn_dir, checkpoint=DEFAULT_CHECKPOINT):
    """Import the authors' code and load the trained model (CPU)."""
    eggnn_dir = os.path.abspath(eggnn_dir)
    if not os.path.isfile(os.path.join(eggnn_dir, "egGNN", "model.py")):
        sys.exit("ERROR: %s does not look like the egGNN folder (egGNN/model.py missing)" % eggnn_dir)
    sys.path.insert(0, eggnn_dir)
    warnings.filterwarnings("ignore")
    os.environ.setdefault("DGLBACKEND", "pytorch")
    import torch
    from rdkit import RDLogger
    RDLogger.DisableLog("rdApp.*")
    import egGNN.model  # noqa: F401  (needed to unpickle the checkpoint)
    from egGNN.feat import ConstructGraph
    from dgllife.utils import load_molecule

    path = checkpoint if os.path.isfile(checkpoint) else os.path.join(eggnn_dir, "egGNN", "checkpoint", checkpoint)
    # The authors pickled the whole model from their training script, so the
    # classes are stored as "__main__.EGG", "__main__.GraphBlock", ... The
    # authors' run_egGNN.py works only because it does "from egGNN.model import *".
    # Here we redirect those names to egGNN.model instead.
    model = torch.load(path, map_location="cpu", pickle_module=_PickleFromModel)
    # The checkpoint is a whole pickled model saved with an old PyTorch (2021).
    # Newer PyTorch expects two attributes that did not exist then
    # (same fix as Eaves et al., github.com/jeavesj/egGNN).
    for m in model.modules():
        if isinstance(m, torch.nn.GELU) and not hasattr(m, "approximate"):
            m.approximate = "none"
        if isinstance(m, torch.nn.ParameterList) and not hasattr(m, "_size"):
            m._size = len(m._parameters)
    model.eval()
    return torch, model, ConstructGraph(), load_molecule


def ligand_smiles(folder, code):
    """Return (SMILES, source file) for the ligand of one complex."""
    from rdkit import Chem
    smi = os.path.join(folder, code + "_ligand.smi")
    if os.path.isfile(smi):
        with open(smi) as f:
            words = f.read().split()
        if words:
            return words[0], smi
    for ext, reader in ((".mol2", lambda p: Chem.MolFromMol2File(p)),
                        (".sdf", lambda p: Chem.MolFromMolFile(p))):
        p = os.path.join(folder, code + "_ligand" + ext)
        if os.path.isfile(p):
            mol = reader(p)
            if mol is not None:
                return Chem.MolToSmiles(mol), p
    return None, None


def score(torch, model, constructor, load_molecule, smiles, protein_pdb):
    """egGNN affinity for one SMILES against one pocket/protein .pdb."""
    from rdkit import Chem
    lig = Chem.MolFromSmiles(smiles)
    if lig is None:
        raise ValueError("RDKit cannot parse the SMILES " + smiles)
    pro, coords = load_molecule(protein_pdb)
    if pro is None:
        raise ValueError("RDKit cannot read " + protein_pdb)
    g_lig = constructor.construct_ligand_graph(lig, add_self_loop=False, num_virtual_nodes=0)
    g_pro = constructor.construct_pocket_graph(pro, coords, cutoff=11)
    with torch.no_grad():
        return float(model((g_lig, g_pro), torch.device("cpu"))[0].item())


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--eggnn-dir", required=True, help="egGNN folder (with run_egGNN.py and egGNN/checkpoint)")
    ap.add_argument("-d", "--directory", required=True, help="folder with one sub-folder per complex")
    ap.add_argument("-o", "--output", default="predictions.csv", help="output CSV (default: predictions.csv)")
    ap.add_argument("--protein-file", choices=("pocket", "protein"), default="pocket",
                    help="use <code>_pocket.pdb (default, recommended) or <code>_protein.pdb")
    ap.add_argument("--checkpoint", default=DEFAULT_CHECKPOINT,
                    help="checkpoint name in egGNN/checkpoint or a path (default: %s)" % DEFAULT_CHECKPOINT)
    args = ap.parse_args()

    torch, model, cons, loadm = load(args.eggnn_dir, args.checkpoint)
    rows = []
    for code in sorted(os.listdir(args.directory)):
        folder = os.path.join(args.directory, code)
        protein = os.path.join(folder, "%s_%s.pdb" % (code, args.protein_file))
        if not os.path.isfile(protein):
            continue
        smi, src = ligand_smiles(folder, code)
        if smi is None:
            print("Skipping %s: no readable ligand (.smi, .mol2 or .sdf)" % code)
            continue
        try:
            pred = score(torch, model, cons, loadm, smi, protein)
        except Exception as e:  # keep going with the other complexes
            print("Skipping %s: %s" % (code, e))
            continue
        rows.append((code, round(pred, 4), os.path.basename(src), smi))
        print("%s\t%.4f\t(SMILES from %s)" % (code, pred, os.path.basename(src)))
    if not rows:
        sys.exit("ERROR: no complexes scored in " + args.directory)
    pd.DataFrame(rows, columns=["pdbid", "pKd_predicted", "ligand_source", "smiles"]).to_csv(args.output, index=False)
    print("Done: %d complexes -> %s" % (len(rows), os.path.abspath(args.output)))


if __name__ == "__main__":
    main()
