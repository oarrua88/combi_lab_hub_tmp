"""Predict binding affinity (pKd) with PLANET (ComputArtCMCG, 2023) for many complexes.

PLANET scores a ligand from its 2D molecular graph plus the 3D binding pocket of
the protein (residues around the crystal ligand). The authors' PLANET_run.py is
built for virtual screening (one protein, many molecules). This wrapper scores a
folder of complexes, one protein-ligand pair per sub-folder, with the authors'
classes (PlanetEstimator, mol_batch_to_graph) and the trained PLANET.param.

Usage (inside the planet environment)
  python predict_planet.py --planet-dir <PLANET folder> -d <complexes folder> [-o predictions.csv]

Each complex needs <code>_protein.pdb and <code>_ligand.sdf (the pocket is the set
of residues around this ligand). If RDKit cannot sanitize the .sdf, the ligand
graph is read from <code>_ligand.mol2 instead.

For CASF-2016 use the authors' prepared core set (core.tar.bz2 in the PLANET
repository): several CASF-2016 .sdf files (1a30 among them) fail RDKit
sanitization, and the input format changes the prediction (see INSTALL.md).
"""
import argparse
import os
import sys

import pandas as pd


def load(planet_dir):
    planet_dir = os.path.abspath(planet_dir)
    sys.path.insert(0, planet_dir)
    import torch
    from rdkit import RDLogger
    RDLogger.DisableLog("rdApp.*")
    import PLANET_run as R
    from chemutils import mol_batch_to_graph
    return torch, R, mol_batch_to_graph


def read_ligand(folder, code):
    """Return (RDKit mol, source file) for the ligand graph."""
    from rdkit import Chem
    sdf = os.path.join(folder, code + "_ligand.sdf")
    if os.path.isfile(sdf):
        mol = Chem.SDMolSupplier(sdf, removeHs=False, sanitize=True)[0]
        if mol is not None:
            return mol, sdf
    mol2 = os.path.join(folder, code + "_ligand.mol2")
    if os.path.isfile(mol2):
        mol = Chem.MolFromMol2File(mol2, removeHs=False, sanitize=True)
        if mol is not None:
            return mol, mol2
    return None, None


def score(torch, R, mol_batch_to_graph, protein_pdb, pocket_sdf, mol):
    """PLANET affinity for one ligand in the pocket defined by pocket_sdf."""
    from rdkit import Chem
    est = R.PlanetEstimator(torch.device("cpu"))
    est.set_pocket_from_ligand(protein_pdb, pocket_sdf)
    graph = mol_batch_to_graph([Chem.AddHs(mol)])
    with torch.no_grad():
        fres, scope = est.model.cal_res_features(est.res_features, 1)
        return float(est.model.screening(fres, scope, graph).view(-1)[0])


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--planet-dir", required=True, help="PLANET folder (with PLANET_run.py and PLANET.param)")
    ap.add_argument("-d", "--directory", required=True, help="folder with one sub-folder per complex")
    ap.add_argument("-o", "--output", default="predictions.csv", help="output CSV (default: predictions.csv)")
    args = ap.parse_args()

    torch, R, g = load(args.planet_dir)
    rows = []
    for code in sorted(os.listdir(args.directory)):
        folder = os.path.join(args.directory, code)
        protein = os.path.join(folder, code + "_protein.pdb")
        pocket = os.path.join(folder, code + "_ligand.sdf")
        if not (os.path.isfile(protein) and os.path.isfile(pocket)):
            continue
        mol, src = read_ligand(folder, code)
        if mol is None:
            print("Skipping %s: RDKit cannot read the ligand" % code)
            continue
        pred = score(torch, R, g, protein, pocket, mol)
        rows.append((code, round(pred, 4), os.path.basename(src)))
        print("%s\t%.4f\t(ligand graph from %s)" % (code, pred, os.path.basename(src)))
    if not rows:
        sys.exit("ERROR: no complexes found in " + args.directory)
    pd.DataFrame(rows, columns=["pdbid", "pKd_predicted", "ligand_source"]).to_csv(args.output, index=False)
    print("Done: %d complexes -> %s" % (len(rows), os.path.abspath(args.output)))


if __name__ == "__main__":
    main()
