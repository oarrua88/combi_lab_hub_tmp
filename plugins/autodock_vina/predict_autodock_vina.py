"""AutoDock Vina (score only) for CombiLabHUB: scores the crystal pose of every complex of a folder.

Two engines, both rescoring the given pose (no docking, no minimisation):

  1.1.2  Vina 1.1.2 + MGLTools 1.5.7 (prepare_receptor4.py / prepare_ligand4.py, default options).
         This is the protocol of CASF-2016 (Su et al. 2019, "AutoDock Vina 1.1.2"): for 1a30 it gives
         -4.99866 kcal/mol, the value in CASF-2016/power_scoring/examples/AutodockVina.dat.
         Linux (or Docker) only, because MGLTools and Vina 1.1.2 have no conda build for Windows.
  1.2.5  Official Vina 1.2.5 binary + Open Babel 3.1.1 pdbqt files (obabel -xr for the receptor).
         Runs on Windows. Vina 1.2 needs a grid box even with --score_only: --autobox (ligand box).
         For 1a30 it gives -4.999 kcal/mol (Vina 1.2 prints 3 decimals).

The engine is chosen from `vina --version` unless --engine is given.

Input folder: one sub-folder per complex, named with its code, with <code>_protein.pdb and
<code>_ligand.mol2 (CASF-2016 / PDBbind layout). --complex scores a single complex folder.

Output CSV: pdbid, pKd_predicted, vina_kcal_mol, engine
pKd_predicted = -0.73349 * Vina score, the kcal/mol -> pKd factor of the Vina terms in DeltaVinaRF20
(Wang & Zhang 2017, featureVina.py). CASF-2016 evaluates the raw Vina score; the PCC is the same.

Usage
  python predict_autodock_vina.py -d <folder of complexes> -o predictions.csv --vina <vina binary>
         [--engine 1.1.2|1.2.5] [--mgl-python <python2 of MGLTools> --mgl-util <.../Utilities24>]
"""
from __future__ import print_function

import argparse
import csv
import os
import re
import shutil
import subprocess
import sys
import tempfile

KCAL_TO_PKD = -0.73349          # DeltaVinaRF20, featureVina.py: c = -0.73349


def vina_version(vina):
    out = subprocess.run([vina, "--version"], stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                         universal_newlines=True).stdout
    m = re.search(r"AutoDock Vina v?(\d+\.\d+\.\d+)", out)
    return m.group(1) if m else None


def find_mgltools(args):
    py = args.mgl_python or os.environ.get("MGLPY")
    util = args.mgl_util or os.environ.get("MGLUTIL")
    if py and not util:
        util = os.path.join(os.path.dirname(os.path.dirname(py)), "MGLToolsPckgs", "AutoDockTools", "Utilities24")
    if not (py and util and os.path.isfile(os.path.join(util, "prepare_receptor4.py"))):
        sys.exit("ERROR: engine 1.1.2 needs MGLTools: give --mgl-python and --mgl-util (or MGLPY / MGLUTIL)")
    return py, util


def run(cmd, cwd):
    p = subprocess.run(cmd, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True)
    return p.returncode, p.stdout


def prepare_mgltools(prot, lig, work, mgl):
    """Default options of prepare_receptor4.py / prepare_ligand4.py. prepare_ligand4.py only finds the
    ligand when it runs in the ligand's folder, so both files are copied into the work folder first."""
    py, util = mgl
    shutil.copy(prot, os.path.join(work, "protein.pdb"))
    shutil.copy(lig, os.path.join(work, "ligand.mol2"))
    run([py, os.path.join(util, "prepare_receptor4.py"), "-r", "protein.pdb", "-o", "protein.pdbqt"], work)
    run([py, os.path.join(util, "prepare_ligand4.py"), "-l", "ligand.mol2", "-o", "ligand.pdbqt"], work)


def prepare_openbabel(prot, lig, work, obabel):
    run([obabel, prot, "-xr", "-O", os.path.join(work, "protein.pdbqt")], work)
    run([obabel, lig, "-O", os.path.join(work, "ligand.pdbqt")], work)


def score(vina, engine, work):
    cmd = [vina, "--receptor", "protein.pdbqt", "--ligand", "ligand.pdbqt", "--score_only"]
    if engine != "1.1.2":
        cmd.append("--autobox")
    rc, out = run(cmd, work)
    pat = r"Affinity:\s+(-?\d+\.\d+)" if engine == "1.1.2" else r"Estimated Free Energy of Binding\s*:\s*(-?\d+\.\d+)"
    m = re.search(pat, out)
    if not m:
        raise RuntimeError("Vina gave no score (exit %d):\n%s" % (rc, out[-1500:]))
    return float(m.group(1))


def score_complex(code, folder, vina, engine, mgl, obabel, keep=None):
    prot = os.path.join(folder, code + "_protein.pdb")
    lig = os.path.join(folder, code + "_ligand.mol2")
    for f in (prot, lig):
        if not os.path.isfile(f):
            raise IOError("file not found: " + f)
    work = tempfile.mkdtemp(prefix="vina_" + code + "_")
    try:
        if engine == "1.1.2":
            prepare_mgltools(os.path.abspath(prot), os.path.abspath(lig), work, mgl)
        else:
            prepare_openbabel(os.path.abspath(prot), os.path.abspath(lig), work, obabel)
        for f in ("protein.pdbqt", "ligand.pdbqt"):
            if not os.path.isfile(os.path.join(work, f)) or os.path.getsize(os.path.join(work, f)) == 0:
                raise RuntimeError("could not write %s for %s" % (f, code))
        kcal = score(vina, engine, work)
        if keep:
            for f in ("protein.pdbqt", "ligand.pdbqt"):
                shutil.copy(os.path.join(work, f), os.path.join(keep, "%s_%s" % (code, f)))
    finally:
        shutil.rmtree(work, ignore_errors=True)
    return kcal


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("-d", "--dir", help="folder with one sub-folder per complex")
    g.add_argument("--complex", help="a single complex folder (its name is the code)")
    ap.add_argument("-o", "--out", default="predictions.csv")
    ap.add_argument("--vina", default="vina", help="Vina executable (default: vina on PATH)")
    ap.add_argument("--engine", choices=("1.1.2", "1.2.5"), help="default: from `vina --version`")
    ap.add_argument("--mgl-python", help="python of MGLTools 1.5.7 (engine 1.1.2)")
    ap.add_argument("--mgl-util", help="MGLToolsPckgs/AutoDockTools/Utilities24 (engine 1.1.2)")
    ap.add_argument("--keep-pdbqt", help="folder where the pdbqt files are kept")
    args = ap.parse_args()

    vina = shutil.which(args.vina) or args.vina
    if not os.path.isfile(vina):
        sys.exit("ERROR: Vina executable not found: " + args.vina)
    ver = vina_version(vina)
    engine = args.engine or ("1.1.2" if ver == "1.1.2" else "1.2.5")
    if ver and not ver.startswith(engine[:3]):
        sys.exit("ERROR: --engine %s but %s is Vina %s" % (engine, vina, ver))
    mgl = find_mgltools(args) if engine == "1.1.2" else None
    obabel = None
    if engine != "1.1.2":
        obabel = shutil.which("obabel")
        if not obabel:
            sys.exit("ERROR: obabel (Open Babel 3.1.1) not found on PATH: activate the autodock_vina environment")
    print("Vina %s (%s), engine %s" % (ver, vina, engine))
    if args.keep_pdbqt and not os.path.isdir(args.keep_pdbqt):
        os.makedirs(args.keep_pdbqt)

    if args.complex:
        jobs = [(os.path.basename(os.path.normpath(args.complex)), args.complex)]
    else:
        jobs = [(c, os.path.join(args.dir, c)) for c in sorted(os.listdir(args.dir))
                if os.path.isdir(os.path.join(args.dir, c))]
    rows, failed = [], []
    for i, (code, folder) in enumerate(jobs, 1):
        try:
            kcal = score_complex(code, folder, vina, engine, mgl, obabel, args.keep_pdbqt)
            rows.append([code, "%.4f" % (KCAL_TO_PKD * kcal), "%.5f" % kcal, engine])
            print("[%d/%d] %s  Vina %.5f kcal/mol  pKd %.4f" % (i, len(jobs), code, kcal, KCAL_TO_PKD * kcal))
        except Exception as e:                      # keep going with the other complexes
            failed.append(code)
            print("[%d/%d] %s  FAILED: %s" % (i, len(jobs), code, e))
    with open(args.out, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["pdbid", "pKd_predicted", "vina_kcal_mol", "engine"])
        w.writerows(rows)
    print("Wrote %s (%d complexes, %d failed%s)" % (args.out, len(rows), len(failed),
                                                     ": " + " ".join(failed) if failed else ""))
    return rows


if __name__ == "__main__":
    main()
