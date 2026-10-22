"""Predict binding affinity (pKd) with the point-cloud models of Wang et al. 2022 (PointNet / PointTransformer).

The method turns a protein-ligand complex into a point cloud of 1024 atoms
(x, y, z, two atom features and a protein/ligand flag) with the authors' program
POINTNET, and scores the cloud with a point-cloud network. The repository
(github.com/wyji001/Point-Cloud) has 5 trained PointNet and 5 trained
PointTransformer models ("(B)" folders). The authors' pred.py averages the 5
models over 5 random rotations of the cloud (25 predictions).

Steps for each complex (one sub-folder per complex), as in the authors' README:
  1. Protein: ATOM records of <code>_protein.pdb (no waters, metals or ions),
     hydrogens removed and polar hydrogens added with Open Babel (--AddPolarH).
  2. Ligand: <code>_ligand.mol2 -> .pdb, same hydrogen treatment.
  3. POINTNET <protein.pdb> <ligand.pdb> <cloud>  (Linux x86-64 program, so this
     step runs on Linux or in the Docker image, not in Windows conda).
  4. 5 models x 5 rotations -> mean pKd. The authors' rotations are random; here
     the random generator is seeded (--seed, default 0) so results repeat.

Usage
  python predict_pointnet.py --pointnet-dir <Point-Cloud repository folder> -d <complexes folder> [-o predictions.csv]
  python predict_pointnet.py --pointnet-dir <...> --cloud <point cloud file>   (score one ready cloud)

--model PointTransformer (default, the best models of the repository) or PointNet.
"""
import argparse
import os
import shutil
import subprocess
import sys
import tempfile
import warnings

MODEL_DIRS = {"PointNet": "PointNet（B）", "PointTransformer": "PointTransformer（B）"}


def load(pointnet_dir, kind="PointTransformer"):
    """Import the authors' network code and load the 5 trained models (CPU)."""
    root = os.path.abspath(pointnet_dir)
    if not os.path.isfile(os.path.join(root, "pointmodel.py")):
        sys.exit("ERROR: %s does not look like the Point-Cloud repository (pointmodel.py missing)" % pointnet_dir)
    if root not in sys.path:
        sys.path.insert(0, root)
    warnings.filterwarnings("ignore")
    import torch
    torch.set_default_tensor_type(torch.DoubleTensor)  # as in the authors' pred.py
    from pointmodel import get_model
    from pointtransform import PointTransformerCls, arg
    mdir = os.path.join(root, "Model", MODEL_DIRS[kind])
    files = sorted(f for f in os.listdir(mdir) if f.endswith(".pth")) if os.path.isdir(mdir) else []
    if len(files) != 5:
        sys.exit("ERROR: expected 5 .pth files in %s, found %d" % (mdir, len(files)))
    nets = []
    for f in files:
        net = get_model() if kind == "PointNet" else PointTransformerCls(arg())
        net.load_state_dict(torch.load(os.path.join(mdir, f), map_location="cpu"))
        net.eval()
        nets.append(net)
    return torch, nets, files


def _rotate(points, rng):
    """The authors' random rotation (pred.py): three planar rotations."""
    import numpy as np
    p = points.copy()
    for a, b in ((0, 1), (0, 2), (1, 2)):
        t = rng.uniform(0, np.pi * 2)
        m = np.array([[np.cos(t), -np.sin(t)], [np.sin(t), np.cos(t)]])
        p[:, [a, b]] = p[:, [a, b]].dot(m)
    return p


def score_cloud(torch, nets, cloud_file, kind="PointTransformer", rotations=5, seed=0):
    """Mean pKd and the per-model means (over the rotations)."""
    import numpy as np
    points = np.loadtxt(cloud_file).astype(np.float64)
    rng = np.random.RandomState(seed)
    torch.manual_seed(seed)  # PointTransformer's farthest-point sampling starts at a random point
    per_model = [[] for _ in nets]
    for _ in range(max(1, rotations)):
        p = _rotate(points, rng) if rotations > 0 else points
        x = torch.tensor(np.expand_dims(p, 0))
        if kind == "PointNet":
            x = x.transpose(2, 1)
        with torch.no_grad():
            for i, net in enumerate(nets):
                per_model[i].append(float(net(x)[0][0]))
    means = [sum(v) / len(v) for v in per_model]
    return sum(means) / len(means), means


def _obabel(args):
    r = subprocess.run(["obabel"] + args, capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError("Open Babel failed: " + (r.stderr or "").strip())


def make_cloud(pointnet_dir, protein_pdb, ligand_mol2, work, out_cloud):
    """Authors' preparation + POINTNET -> point cloud file."""
    exe = os.path.join(os.path.abspath(pointnet_dir), "POINTNET")
    if os.name == "nt":
        raise RuntimeError("POINTNET is a Linux program: make the point clouds with Docker (see INSTALL.md)")
    if not os.path.isfile(exe):
        raise RuntimeError("POINTNET not found in " + pointnet_dir)
    if not os.access(exe, os.X_OK):
        os.chmod(exe, 0o755)
    os.makedirs(work, exist_ok=True)
    prot_atoms = os.path.join(work, "protein_atoms.pdb")
    with open(protein_pdb) as fi, open(prot_atoms, "w") as fo:
        for line in fi:
            if line.startswith("ATOM"):
                fo.write(line)
        fo.write("END\n")
    prot_noh, prot_h = os.path.join(work, "protein_noH.pdb"), os.path.join(work, "protein.pdb")
    lig_noh, lig_h = os.path.join(work, "ligand_noH.pdb"), os.path.join(work, "ligand.pdb")
    _obabel([prot_atoms, "-O", prot_noh, "-d"])
    _obabel([prot_noh, "-O", prot_h, "--AddPolarH"])
    _obabel([ligand_mol2, "-O", lig_noh, "-d"])
    _obabel([lig_noh, "-O", lig_h, "--AddPolarH"])
    r = subprocess.run([exe, prot_h, lig_h, out_cloud], capture_output=True, text=True)
    if r.returncode != 0 or not os.path.isfile(out_cloud):
        raise RuntimeError("POINTNET failed: " + ((r.stderr or r.stdout or "").strip() or "no output"))
    return out_cloud


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--pointnet-dir", required=True, help="Point-Cloud repository folder (contains POINTNET and Model/)")
    src = ap.add_mutually_exclusive_group(required=True)
    src.add_argument("-d", "--directory", help="folder with one sub-folder per complex")
    src.add_argument("--cloud", help="score one point cloud file that is already made")
    ap.add_argument("-o", "--output", default="predictions.csv", help="output CSV (default: predictions.csv)")
    ap.add_argument("--model", choices=sorted(MODEL_DIRS), default="PointTransformer")
    ap.add_argument("--rotations", type=int, default=5, help="random rotations per model (authors: 5; 0 = none)")
    ap.add_argument("--seed", type=int, default=0, help="seed of the random rotations (default 0)")
    ap.add_argument("--keep-clouds", help="folder where the point clouds are saved")
    args = ap.parse_args()

    torch, nets, _ = load(args.pointnet_dir, args.model)
    if args.cloud:
        mean, per = score_cloud(torch, nets, args.cloud, args.model, args.rotations, args.seed)
        print("pKd %.4f  (models: %s)" % (mean, " ".join("%.4f" % p for p in per)))
        return

    import pandas as pd
    tmp = tempfile.mkdtemp(prefix="pointnet_")
    if args.keep_clouds:
        os.makedirs(args.keep_clouds, exist_ok=True)
    rows = []
    for code in sorted(os.listdir(args.directory)):
        folder = os.path.join(args.directory, code)
        prot = os.path.join(folder, code + "_protein.pdb")
        lig = os.path.join(folder, code + "_ligand.mol2")
        if not (os.path.isfile(prot) and os.path.isfile(lig)):
            continue
        try:
            cloud = os.path.join(args.keep_clouds or tmp, code + "_cloud.txt")
            make_cloud(args.pointnet_dir, prot, lig, os.path.join(tmp, code), cloud)
            mean, per = score_cloud(torch, nets, cloud, args.model, args.rotations, args.seed)
        except Exception as e:  # keep going with the other complexes
            print("Skipping %s: %s" % (code, e))
            continue
        rows.append([code, round(mean, 4)] + [round(p, 4) for p in per])
        print("%s\t%.4f\t%s" % (code, mean, " ".join("%.4f" % p for p in per)))
    shutil.rmtree(tmp, ignore_errors=True)
    if not rows:
        sys.exit("ERROR: no complexes scored in " + args.directory)
    cols = ["pdbid", "pKd_predicted"] + ["pKd_model%d" % i for i in range(len(nets))]
    pd.DataFrame(rows, columns=cols).to_csv(args.output, index=False)
    print("Done: %d complexes (%s) -> %s" % (len(rows), args.model, os.path.abspath(args.output)))


if __name__ == "__main__":
    main()
