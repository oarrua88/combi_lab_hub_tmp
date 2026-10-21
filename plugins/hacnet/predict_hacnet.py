"""HAC-Net - batch prediction for a folder of protein-ligand complexes (CPU).

HAC-Net (Kyro, Brent & Batista, J. Chem. Inf. Model. 2023) averages a 3D-CNN with
channel attention and two attention-based GCNs. The function predict_pkd() of the
official package (PyPI HACNet 1.4.3, HACNet/functions.py) runs the whole pipeline for
one complex: pocket = residues (+ waters) within 8 A of the ligand -> PyMOL adds H to
waters -> EqEq partial charges on the pocket -> tfbio featurizer -> voxels and graphs
-> the three models. The trained parameters and element_features.xml come from the
GitHub repository (they are not in the PyPI package).

This wrapper runs that predict_pkd() unchanged except for these points, applied to its
source code when it is loaded:
  1. '/content/' (Google Colab) paths -> a temporary folder per complex;
  2. the pocket charges: the package posts the pocket to the ACC2 web service at
     http://78.128.250.156, which no longer answers. --charges chooses:
       acc2       the Atomic Charge Calculator web API (https://acc.biodata.ceitec.cz,
                  successor of ACC2), EqEq method, same settings as the Eaves et al.
                  fork (default; needs internet)
       chargefw2  EqEq computed locally with ChargeFW2, the program that ACC2 runs,
                  with the same settings (offline; used by the Docker image)
  3. it returns the full-precision pKd instead of round(pKd, 3);
  4. GatedGraphConv(..., aggregation=self.attn_aggr) -> GatedGraphConv(...). Old PyG
     ignored the unknown 'aggregation' argument, so the GCNs were trained with the
     default 'add' aggregation (the saved GCN parameters have no aggregation module
     inside the gated layer, and they load with strict=True only this way). PyG >= 2.3
     rejects the argument; 'aggr=self.attn_aggr', used by the Colab notebook, would
     change the model.
  5. torch_geometric.nn.DataParallel -> a CPU stand-in: recent PyG versions require
     CUDA for DataParallel. On a single device it only batches the graphs.

Do NOT use HACNet/functions.py of the GitHub repository: its predict_pkd() uses
undefined classes. The Colab notebook (and the Eaves et al. fork, based on it) imports
CNN.py, whose attention layers are named se_block, while the parameter file has
SE_block, and loads it with strict=False: those layers keep random weights.

Each complex folder must contain <code>_protein.pdb and <code>_ligand.mol2.

Usage (inside the hacnet environment)
  python predict_hacnet.py --hacnet-dir <HAC-Net folder> -d <complexes folder> [-o predictions.csv] [--charges acc2|chargefw2]
"""
import argparse
import contextlib
import io
import os
import shutil
import subprocess
import sys
import tempfile
import time
import types
import warnings
import zipfile

warnings.filterwarnings("ignore")

# Atomic Charge Calculator III public API (the ACC2 service moved here in 2026; the old
# ACC2 address https://acc2.ncbr.muni.cz/api/v1 now answers 405). Override with $ACC_API.
ACC2 = os.environ.get("ACC_API", "https://acc.biodata.ceitec.cz/api/v1")
_MOD = None


def _mol2_with_charges(pocket_mol2, charges, out_mol2):
    """Copy pocket_mol2 replacing the charge column of every atom (same atom order)."""
    lines = open(pocket_mol2).read().splitlines()
    out, inside, k = [], False, 0
    for ln in lines:
        s = ln.strip()
        if s.startswith("@<TRIPOS>"):
            inside = s == "@<TRIPOS>ATOM"
            out.append(ln)
            continue
        if inside and s:
            p = s.split()
            if k >= len(charges):
                raise RuntimeError("ACC returned %d charges for more atoms" % len(charges))
            p = p[:8] + ["%.4f" % charges[k]] if len(p) >= 9 else p + ["%.4f" % charges[k]]
            out.append("%7s %-8s %10s %10s %10s %-8s %4s %-8s %10s" % tuple(p[:9]))
            k += 1
        else:
            out.append(ln)
    if k != len(charges):
        raise RuntimeError("ACC returned %d charges for %d atoms" % (len(charges), k))
    with open(out_mol2, "w") as f:
        f.write("\n".join(out) + "\n")


def charges_acc2(pocket_mol2, out_mol2):
    """EqEq charges from the Atomic Charge Calculator web service (ChargeFW2 behind it).

    Same settings as the Eaves et al. fork: read HETATM, ignore water, permissive types.
    Workflow of the current API: POST /files/upload -> POST /charges/calculate ->
    GET /files/download/computation/<id> (zip with the charged .mol2). If the zip has no
    .mol2, the charges returned by /charges/calculate are written into the pocket .mol2.
    """
    import requests
    with open(pocket_mol2, "rb") as fh:
        up = requests.post(ACC2 + "/files/upload",
                           files={"files": (os.path.basename(pocket_mol2), fh, "chemical/x-mol2")}, timeout=120)
    if up.status_code >= 400:
        raise RuntimeError("ACC upload %d: %s" % (up.status_code, up.text[:300]))
    hashes = [d.get("fileHash") for d in up.json()["data"] if isinstance(d, dict)]
    if not hashes:
        raise RuntimeError("ACC upload returned no fileHash")
    calc = requests.post(ACC2 + "/charges/calculate", timeout=600,
                         json={"configs": [{"method": "eqeq", "parameters": None}], "fileHashes": hashes,
                               "settings": {"readHetatm": True, "ignoreWater": True, "permissiveTypes": True}})
    if calc.status_code >= 400:
        raise RuntimeError("ACC calculate %d: %s" % (calc.status_code, calc.text[:300]))
    data = calc.json().get("data") or {}
    comp = data.get("computationId")
    charges = None
    for res in data.get("results", []):
        for c in res.get("calculations", []):
            mols = list((c.get("charges") or {}).values())
            if mols:
                charges = mols[0]
    if comp:
        for _ in range(60):
            dl = requests.get(ACC2 + "/files/download/computation/" + comp, timeout=120)
            if dl.status_code == 200 and dl.content[:2] == b"PK":
                with zipfile.ZipFile(io.BytesIO(dl.content)) as zf:
                    names = [n for n in zf.namelist() if n.lower().endswith(".mol2")]
                    if names:
                        with open(out_mol2, "wb") as fo:
                            fo.write(zf.read(names[0]))
                        return
                break
            time.sleep(1.0)
    if charges is None:
        raise RuntimeError("ACC returned no charges: %s" % calc.text[:300])
    _mol2_with_charges(pocket_mol2, charges, out_mol2)


def charges_chargefw2(pocket_mol2, out_mol2):
    """EqEq charges computed locally with ChargeFW2, the program behind ACC2 (same settings).

    The chargefw2 executable is taken from the CHARGEFW2 environment variable, or from PATH.
    """
    exe = os.environ.get("CHARGEFW2") or shutil.which("chargefw2")
    if not exe:
        raise RuntimeError("chargefw2 not found: set CHARGEFW2 to the executable or use --charges acc2")
    out_dir = tempfile.mkdtemp(prefix="cfw2_")
    try:
        r = subprocess.run([exe, "--mode", "charges", "--input-file", pocket_mol2, "--chg-out-dir", out_dir,
                            "--method", "eqeq", "--read-hetatm", "--ignore-water", "--permissive-types"],
                           capture_output=True, text=True)
        res = os.path.join(out_dir, os.path.basename(pocket_mol2) + ".mol2")
        if r.returncode != 0 or not os.path.isfile(res):
            raise RuntimeError("chargefw2 failed: " + (r.stderr or r.stdout)[-300:])
        shutil.copy(res, out_mol2)
    finally:
        shutil.rmtree(out_dir, ignore_errors=True)


CHARGES = {"acc2": charges_acc2, "chargefw2": charges_chargefw2}


def _cpu_data_parallel():
    """Stand-in for torch_geometric.nn.DataParallel on a computer without GPU.

    Keeps the wrapped model as .module (so the saved 'module.*' parameter names load)
    and, like DataParallel on one device, batches the list of graphs and calls it.
    """
    import torch
    from torch_geometric.data import Batch

    class CPUDataParallel(torch.nn.Module):
        def __init__(self, module):
            super().__init__()
            self.module = module

        def forward(self, data_list):
            return self.module(Batch.from_data_list(data_list))

    return CPUDataParallel


def load():
    """Load predict_pkd() from the installed HACNet package (PyPI 1.4.3) with the changes
    listed in the module docstring. The package's functions.py is self-contained: it
    defines its own CNN (SE_block layers, loaded with strict=True), MP_GCN and Model_Linear.
    """
    global _MOD
    if _MOD is not None:
        return _MOD
    import importlib.util
    spec = importlib.util.find_spec("HACNet")
    if spec is None:
        raise RuntimeError("the HACNet package is not installed: pip install --no-deps HACNet==1.4.3")
    path = os.path.join(list(spec.submodule_search_locations)[0], "functions.py")
    src = open(path, encoding="utf-8").read()
    changes = [("add_mol2_charges('/content/pocket.mol2')",
                "_COMBILAB_CHARGES('pocket.mol2', 'charged_pocket.mol2')"),
               ("return round(pkd, 3)", "return pkd"),
               ("/content/", ""),
               # see docstring, point 4
               ("GatedGraphConv(in_channels, prop_iter, aggregation=self.attn_aggr)",
                "GatedGraphConv(in_channels, prop_iter)"),
               # see docstring, point 5
               ("= GeometricDataParallel(MP_GCN(", "= _CPUDataParallel(MP_GCN(")]
    for old, new in changes:
        if old not in src:
            raise RuntimeError("%s is not HACNet 1.4.3 (missing %r)" % (path, old))
        src = src.replace(old, new)
    mod = types.ModuleType("hacnet_functions")
    mod.__file__ = path
    mod._CPUDataParallel = _cpu_data_parallel()
    exec(compile(src, path, "exec"), mod.__dict__)
    _MOD = mod
    return mod


def predict_one(hacnet_dir, protein, ligand, charges="acc2"):
    """pKd of one complex."""
    hacnet_dir = os.path.abspath(hacnet_dir)
    mod = load()
    mod._COMBILAB_CHARGES = CHARGES[charges]
    pkg = os.path.join(hacnet_dir, "HACNet")
    par = os.path.join(pkg, "parameter_files")
    protein, ligand = os.path.abspath(protein), os.path.abspath(ligand)
    work = tempfile.mkdtemp(prefix="hacnet_")
    old = os.getcwd()
    try:
        os.chdir(work)
        with contextlib.redirect_stdout(io.StringIO()):
            pkd = mod.predict_pkd(protein, ligand, os.path.join(pkg, "element_features.xml"),
                                  os.path.join(par, "CNN_parameters.pt"), os.path.join(par, "GCN0_parameters.pt"),
                                  os.path.join(par, "GCN1_parameters.pt"), os.path.join(par, "MLP_parameters.pt"),
                                  verbose=False)
        return float(pkd)
    finally:
        os.chdir(old)
        shutil.rmtree(work, ignore_errors=True)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--hacnet-dir", required=True, help="HAC-Net folder (contains the HACNet package folder)")
    ap.add_argument("-d", "--directory", required=True, help="folder with one sub-folder per complex")
    ap.add_argument("-o", "--output", default="predictions.csv", help="output CSV (default: predictions.csv)")
    ap.add_argument("--charges", choices=sorted(CHARGES), default="acc2",
                    help="pocket charges: acc2 = ACC2 web service, as the authors (default); chargefw2 = local ChargeFW2, offline")
    a = ap.parse_args()
    import pandas as pd
    hd = os.path.abspath(a.hacnet_dir)
    root = os.path.abspath(a.directory)
    codes = sorted(d for d in os.listdir(root) if os.path.isdir(os.path.join(root, d)))
    rows = []
    for n, code in enumerate(codes, 1):
        f = os.path.join(root, code)
        try:
            p = predict_one(hd, os.path.join(f, code + "_protein.pdb"), os.path.join(f, code + "_ligand.mol2"), a.charges)
            rows.append((code, round(p, 4), a.charges, ""))
            print("[%d/%d] %s  pKd %.4f" % (n, len(codes), code, p))
        except Exception as e:                       # noqa: BLE001
            rows.append((code, None, a.charges, str(e).splitlines()[0][:200]))
            print("[%d/%d] %s  ERROR: %s" % (n, len(codes), code, rows[-1][3]))
    out = pd.DataFrame(rows, columns=["pdbid", "pKd_predicted", "charges", "error"])
    os.makedirs(os.path.dirname(os.path.abspath(a.output)), exist_ok=True)
    out.to_csv(a.output, index=False)
    print("Done: %d complexes (%d errors) -> %s" % (len(out), out.pKd_predicted.isna().sum(), a.output))


if __name__ == "__main__":
    main()
