"""Predict binding affinity (pKd) with PIGNet2 (Moon et al., Digital Discovery 2024) for many complexes.

PIGNet2 is a physics-informed graph neural network. For each complex it predicts
the binding free energy (kcal/mol) as the sum of four physics-like terms
(van der Waals, hydrogen bond, metal-ligand and hydrophobic), using the ligand
and the pocket (protein residues within 5 A of the ligand). The authors convert
energy to pKd with pKd = energy / -1.36 (src/data/data.py, src/benchmark/*.py).

The repository has 4 trained models (src/ckpt/pda_0..3.pt, trained with positive
and negative data augmentation). The paper reports the 4-model ensemble.

What this wrapper does for each complex (one sub-folder per complex):
  1. Ligand: <code>_ligand.mol2 read with RDKit keeping its hydrogens.
     CASF-2016 ligands are already protonated, and the authors' prepared 1a30
     has the same molecule (same SMILES, formal charge -2). The CASF .sdf files
     do not pass RDKit sanitization, so the .mol2 is used. --protonate-ligand
     re-protonates at pH 7.4 with Dimorphite-DL, as the authors' predict.py does
     for new ligands.
  2. Pocket: the authors' generate_data.extract() (PyMOL, residues within 5 A,
     hydrogens removed), from <code>_protein.pdb.
     The authors' predict.py first re-protonates the protein with `reduce`, a
     program that has no Windows/conda package. The pocket keeps no hydrogens,
     so for CASF-2016 the result is the same with or without it (checked for
     1a30); --protonate-protein uses reduce if it is installed.
  3. The authors' complex_to_data() and model.predict_step(), on CPU.

Usage (inside the pignet2 environment)
  python predict_pignet2.py --pignet2-dir <PIGNet2 repository folder> -d <complexes folder> [-o predictions.csv]

Output: predictions.csv with pdbid, pKd_predicted (mean of the models) and
pKd_model<i> / energy_model<i> for each model.
"""
import argparse
import glob
import os
import shutil
import sys
import tempfile
import warnings

KCAL_PER_PKD = -1.36  # authors' conversion


def load(pignet2_dir, models=(0, 1, 2, 3)):
    """Import the authors' code and load the trained models (CPU)."""
    root = os.path.abspath(pignet2_dir)
    src = os.path.join(root, "src")
    pre = os.path.join(root, "dataset", "preprocess")
    if not os.path.isfile(os.path.join(src, "models", "pignet.py")):
        sys.exit("ERROR: %s does not look like the PIGNet2 repository (src/models/pignet.py missing)" % pignet2_dir)
    for p in (os.path.join(src, "exe"), pre, src):
        if p not in sys.path:
            sys.path.insert(0, p)
    warnings.filterwarnings("ignore")
    os.environ.setdefault("CUDA_VISIBLE_DEVICES", "")
    import torch
    from omegaconf import open_dict
    from rdkit import RDLogger
    RDLogger.DisableLog("rdApp.*")
    import utils  # src/exe/utils.py
    torch.set_num_threads(max(1, os.cpu_count() or 1))
    device = torch.device("cpu")
    nets = []
    for i in models:
        ckpt = os.path.join(src, "ckpt", "pda_%d.pt" % i)
        if not os.path.isfile(ckpt):
            sys.exit("ERROR: checkpoint not found: " + ckpt)
        checkpoint = torch.load(ckpt, map_location=device)
        config = utils.merge_configs(checkpoint["config"], {})
        with open_dict(config):
            config.data = {"predict": {"test_result_path": os.devnull}}
        net = utils.initialize_state(device, checkpoint, config)[0]
        net.eval()
        nets.append(net)
    return torch, nets


def read_ligand(ligand_mol2, protonate=False):
    from rdkit import Chem
    mol = Chem.MolFromMol2File(ligand_mol2, sanitize=True, removeHs=False)
    if mol is None:
        raise RuntimeError("RDKit cannot read " + os.path.basename(ligand_mol2))
    if protonate:
        from protonate import protonate_ligand
        mol = protonate_ligand(mol)
        if mol is None:
            raise RuntimeError("Dimorphite-DL protonation failed")
    return mol


def prepare(protein_pdb, ligand_mol2, protonate_ligand=False, protonate_protein=False):
    """(ligand, pocket) RDKit molecules, with the authors' pocket extraction."""
    from pathlib import Path
    from generate_data import extract_binding_pocket
    ligand = read_ligand(ligand_mol2, protonate_ligand)
    protein = Path(protein_pdb)
    tmp_protein = None
    if protonate_protein:
        if shutil.which("reduce") is None:
            raise RuntimeError("--protonate-protein needs the program 'reduce' in the PATH")
        from protonate import protonate_pdb
        tmp_protein = protonate_pdb(protein)
        protein = tmp_protein
    try:
        pocket = extract_binding_pocket(ligand, str(protein))
    finally:
        if tmp_protein is not None:
            tmp_protein.unlink()
    if pocket is None:
        raise RuntimeError("pocket extraction failed")
    return ligand, pocket


def score(torch, nets, ligand, pocket, key="complex"):
    """List of (energy kcal/mol, pKd), one per loaded model."""
    import torch_geometric.data as pyg_data
    from data.data import complex_to_data
    out = []
    for net in nets:
        datum = complex_to_data(ligand, pocket, key=key, conv_range=net.config.model.conv_range)
        batch = pyg_data.Batch.from_data_list([datum])
        net.reset_log()
        with torch.no_grad():
            net.predict_step(batch)
        energy = float(sum(net.predictions["predict"][key]))
        out.append((energy, energy / KCAL_PER_PKD))
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--pignet2-dir", required=True, help="PIGNet2 repository folder (contains src/ckpt)")
    ap.add_argument("-d", "--directory", required=True, help="folder with one sub-folder per complex")
    ap.add_argument("-o", "--output", default="predictions.csv", help="output CSV (default: predictions.csv)")
    ap.add_argument("--model", choices=("0", "1", "2", "3", "all"), default="all",
                    help="trained model: 0..3 or all (mean of the four, default)")
    ap.add_argument("--protonate-ligand", action="store_true", help="re-protonate the ligand at pH 7.4 (Dimorphite-DL)")
    ap.add_argument("--protonate-protein", action="store_true", help="re-protonate the protein with reduce")
    args = ap.parse_args()

    import pandas as pd
    models = (0, 1, 2, 3) if args.model == "all" else (int(args.model),)
    torch, nets = load(args.pignet2_dir, models)
    rows = []
    for code in sorted(os.listdir(args.directory)):
        folder = os.path.join(args.directory, code)
        prot = os.path.join(folder, code + "_protein.pdb")
        lig = os.path.join(folder, code + "_ligand.mol2")
        if not (os.path.isfile(prot) and os.path.isfile(lig)):
            continue
        try:
            ligand, pocket = prepare(prot, lig, args.protonate_ligand, args.protonate_protein)
            res = score(torch, nets, ligand, pocket, code)
        except Exception as e:  # keep going with the other complexes
            print("Skipping %s: %s" % (code, e))
            continue
        pkd = [p for _, p in res]
        mean = sum(pkd) / len(pkd)
        rows.append([code, round(mean, 4)] + [round(p, 4) for p in pkd] + [round(e, 3) for e, _ in res])
        print("%s\t%.4f\t%s" % (code, mean, " ".join("%.4f" % p for p in pkd)))
    if not rows:
        sys.exit("ERROR: no complexes scored in " + args.directory)
    cols = (["pdbid", "pKd_predicted"] + ["pKd_model%d" % i for i in models]
            + ["energy_model%d" % i for i in models])
    pd.DataFrame(rows, columns=cols).to_csv(args.output, index=False)
    print("Done: %d complexes -> %s" % (len(rows), os.path.abspath(args.output)))


if __name__ == "__main__":
    main()
