"""Predict binding affinity (pKd) with saCNN (Wang et al., IEEE BIBM 2021) for many complexes.

saCNN is a 3D convolutional neural network with spatial attention. Each complex
is turned into a 24 x 24 x 24 A voxel grid centred on the ligand, with 8
moleculekit channels for the protein and 8 for the ligand (16 channels). The
prediction is the mean over 24 rotations of the grid, as in the authors'
inference.py.

The authors split the work into two scripts (src/data.py writes an .h5 feature
file, src/inference.py scores it) and need Acellera's HTMD, which no longer
installs (htmd 2.0.6 requires the non-public acemd3). This wrapper does both
steps for a folder of complexes with moleculekit only, using the authors'
network (src/model.py), rotations (src/Rotations.py) and checkpoint.

Protein preparation follows the corrected version of Eaves et al. 2026
(github.com/jeavesj/saCNN, src/Preprocessing.py):
  1. prepareProteinForAtomtyping (pdb2pqr + propka), without LLP residues,
     dropping atoms left without bonds, voxelisation without validity checks;
  2. if that fails: the same without hydrogens in the input.
Eaves et al. have one more fallback in between (HTMD proteinPrepare + CHARMM
build). It needs HTMD and is NOT included here; complexes that need it are
reported as failed.

Usage (inside the sacnn environment)
  python predict_sacnn.py --sacnn-dir <saCNN folder> -d <complexes folder> [-o predictions.csv]

Each complex needs <code>_protein.pdb and <code>_ligand.mol2.
"""
import argparse
import contextlib
import io
import logging
import os
import sys
import types
import warnings

import numpy as np

BOXSIZE = [24, 24, 24]
ARGS = types.SimpleNamespace(feature_num=16, cout_dim=512, dimgroup=16, voxel_size=24, augment_num=24)


def _quiet():
    warnings.filterwarnings("ignore")
    logging.disable(logging.WARNING)  # pdb2pqr/propka/moleculekit are very verbose
    from rdkit import RDLogger
    RDLogger.DisableLog("rdApp.*")


def load(sacnn_dir):
    """Import the authors' network and load checkpoint/model.pkl on the CPU."""
    sacnn_dir = os.path.abspath(sacnn_dir)
    src = os.path.join(sacnn_dir, "src")
    ckpt = os.path.join(sacnn_dir, "checkpoint", "model.pkl")
    if not (os.path.isfile(os.path.join(src, "model.py")) and os.path.isfile(ckpt)):
        sys.exit("ERROR: %s does not look like the saCNN folder (src/model.py or checkpoint/model.pkl missing)" % sacnn_dir)
    _quiet()
    sys.path.insert(0, src)
    import torch
    from model import ConvAttention3D
    from Rotations import Rotations
    with contextlib.redirect_stdout(io.StringIO()):  # model.py prints its layer sizes
        model = ConvAttention3D(ARGS)
    # The checkpoint was saved on a GPU; map it to the CPU.
    model.load_state_dict(torch.load(ckpt, map_location="cpu"))
    model.eval()
    return torch, model, Rotations()


def _protein_voxels(prot_path, center, drop_hydrogens):
    from moleculekit.molecule import Molecule
    from moleculekit.tools import voxeldescriptors
    from moleculekit.tools.atomtyper import prepareProteinForAtomtyping
    x, y, z = center
    prot = Molecule(prot_path)
    if prot.numAtoms > 50000:  # same cropping as the authors for very large files
        f = [b * 2.5 for b in BOXSIZE]
        prot.filter("z < %s and z > %s" % (z + f[2], z - f[2]))
        prot.filter("x < %s and x > %s" % (x + f[0], x - f[0]))
        prot.filter("y < %s and y > %s" % (y + f[1], y - f[1]))
    prot.filter("protein")
    prot.filter("not resname LLP")  # LLP has no pdb2pqr topology
    if drop_hydrogens:
        prot.filter("not hydrogen")
    else:
        prot.bonds = prot._getBonds()
    prot = prepareProteinForAtomtyping(prot, verbose=False)
    prot.set(value="Se", field="element", sel="name SE")
    if not drop_hydrogens and prot.bonds.shape[0] > 0:
        bonded = np.zeros(prot.numAtoms, dtype=bool)
        bonded[prot.bonds.flatten()] = True
        prot.filter(bonded)
    kw = {} if drop_hydrogens else {"validitychecks": False}
    return voxeldescriptors.getVoxelDescriptors(prot, center=list(center), boxsize=BOXSIZE, version=2, **kw)


def featurize(protein_pdb, ligand_mol2):
    """Return (16 x 24 x 24 x 24 array, preparation used). Raises on failure."""
    from moleculekit.smallmol.smallmol import SmallMol
    from moleculekit.tools import voxeldescriptors
    sm = SmallMol(ligand_mol2, force_reading=True, fixHs=False)
    coords = sm.get("coords")
    center = [np.mean(coords[:, 0]), np.mean(coords[:, 1]), np.mean(coords[:, 2])]  # as the authors
    fs, _, ns = voxeldescriptors.getVoxelDescriptors(sm, center=center, boxsize=BOXSIZE, version=2)
    errors = []
    for prep, drop_h in (("standard", False), ("without input hydrogens", True)):
        try:
            with contextlib.redirect_stdout(io.StringIO()):
                f, _, n = _protein_voxels(protein_pdb, center, drop_h)
            break
        except Exception as e:  # try the next preparation
            errors.append("%s: %s" % (prep, e))
    else:
        raise RuntimeError("protein preparation failed (" + " | ".join(errors) + ")")
    data = np.concatenate((f.reshape(n[0], n[1], n[2], f.shape[1]),
                           fs.reshape(ns[0], ns[1], ns[2], fs.shape[1])), axis=3).transpose([3, 0, 1, 2])
    return data, prep


def score(torch, model, rotations, data):
    """Mean prediction over the 24 rotations of the grid (authors' inference.py)."""
    outs = []
    with torch.no_grad():
        for j in range(ARGS.augment_num):
            rot = rotations.rotation(data, j).copy()
            t = torch.from_numpy(rot).float().view(1, ARGS.feature_num, ARGS.voxel_size, ARGS.voxel_size, ARGS.voxel_size)
            outs.append(model(t))
    return float(torch.mean(torch.tensor(outs)))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--sacnn-dir", required=True, help="saCNN folder (with src/ and checkpoint/model.pkl)")
    ap.add_argument("-d", "--directory", required=True, help="folder with one sub-folder per complex")
    ap.add_argument("-o", "--output", default="predictions.csv", help="output CSV (default: predictions.csv)")
    args = ap.parse_args()

    import pandas as pd
    torch, model, rot = load(args.sacnn_dir)
    rows, failed = [], []
    for code in sorted(os.listdir(args.directory)):
        folder = os.path.join(args.directory, code)
        protein = os.path.join(folder, code + "_protein.pdb")
        ligand = os.path.join(folder, code + "_ligand.mol2")
        if not (os.path.isfile(protein) and os.path.isfile(ligand)):
            continue
        try:
            data, prep = featurize(protein, ligand)
        except Exception as e:
            print("Skipping %s: %s" % (code, e))
            failed.append(code)
            continue
        pred = score(torch, model, rot, data)
        rows.append((code, round(pred, 4), prep))
        print("%s\t%.4f\t(protein preparation: %s)" % (code, pred, prep))
    if not rows:
        sys.exit("ERROR: no complexes scored in " + args.directory)
    pd.DataFrame(rows, columns=["pdbid", "pKd_predicted", "protein_preparation"]).to_csv(args.output, index=False)
    print("Done: %d complexes -> %s" % (len(rows), os.path.abspath(args.output)))
    if failed:
        print("Failed (%d): %s" % (len(failed), " ".join(failed)))


if __name__ == "__main__":
    main()
