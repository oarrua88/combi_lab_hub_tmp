"""DeltaVinaRF20 (Wang & Zhang, J. Comput. Chem. 2017) for CombiLabHUB.

pKd = Vina score (in pKd units) + Random Forest correction on 20 features:
  vina, F1-F10  Vina score and 10 Vina terms of the vina4dv program (MGLTools pdbqt files, "-U nphs")
  F11-F20       buried SASA of the complex by pharmacophore type (P, N, DA, D, A, AR, H, PL, HA, total), MSMS
The features come from the authors' code (deltavina/features/featureVina.py and featureSASA.py) and the
prediction from their trained model deltavina/models/rffit.rda with the formula of their DVRF20.R:
  pred = predict(rffit, newdata = df[3:22]) + df$vina

Two modes
  A. --features input.csv   predicts from a features table with the authors' columns
                            (pdb, vina, F1..F20). Any OS: only needs R + randomForest.
  B. -d <folder> | --complex <folder>
                            computes the features with the authors' code and predicts.
                            Linux (Docker image): Python 2.7, Open Babel 2.4.1, MGLTools 1.5.7,
                            vina4dv, MSMS. Needs VINADIR, MGLPY and MGLUTIL (set in the image).

Input folder (mode B): one sub-folder per complex, named with its code, with <code>_protein.pdb and
<code>_ligand.mol2 (CASF-2016 / PDBbind layout).

Output CSV: pdbid, pKd_predicted, pKd_rounded (2 decimals, as the authors and CASF-2016), vina_pKd
The features of mode B are also written next to the output (<output>_features.csv).

Usage
  python predict_deltavinarf20.py --dv-dir <deltavina repo> --features input.csv -o predictions.csv
  python predict_deltavinarf20.py --dv-dir <deltavina repo> -d <folder of complexes> -o predictions.csv
"""
from __future__ import print_function

import argparse
import csv
import hashlib
import os
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
MODEL = os.path.join("deltavina", "models", "rffit.rda")
MODEL_MD5 = "944e70f5ded661296aa29f1470e372cc"
FEATURES = ["vina"] + ["F%d" % i for i in range(1, 21)]

R_SCRIPT = r"""
suppressMessages(library(randomForest))
args <- commandArgs(trailingOnly = TRUE)
load(args[1])                                   # rffit
df <- read.table(args[2], header = T, stringsAsFactors = F, sep = ',')
feats <- df[3:22]                               # F1..F20, as in the authors' DVRF20.R
pred <- predict(rffit, newdata = feats) + df$vina
out <- data.frame(pdb = df$pdb, pred = sprintf('%.6f', pred), pred2 = sprintf('%.2f', round(pred, 2)),
                  vina = sprintf('%.6f', df$vina))
write.table(out, args[3], sep = ',', row.names = F, quote = F)
cat(R.version.string, '| randomForest', as.character(packageVersion('randomForest')), '\n')
"""


def which(name):
    for d in os.environ.get("PATH", "").split(os.pathsep):
        for ext in ("", ".exe"):
            p = os.path.join(d, name + ext)
            if os.path.isfile(p) and os.access(p, os.X_OK):
                return p
    return None


def md5(path):
    h = hashlib.md5()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def find_rscript():
    pre = os.environ.get("CONDA_PREFIX") or sys.prefix
    cands = [os.environ.get("RSCRIPT"), which("Rscript")]
    for base in (pre, sys.prefix):
        cands += [os.path.join(base, "Lib", "R", "bin", "x64", "Rscript.exe"), os.path.join(base, "Lib", "R", "bin", "Rscript.exe"),
                  os.path.join(base, "Scripts", "Rscript.exe"), os.path.join(base, "bin", "Rscript")]
    for c in cands:
        if c and os.path.isfile(c):
            return c
    raise RuntimeError("Rscript not found: install R (environment.yml) or set RSCRIPT")


def r_predict(dv_dir, features_csv, check_md5=True):
    """Runs the authors' model on a features CSV (columns pdb, vina, F1..F20). Returns a list of
    (pdb, pred, pred_2_decimals, vina) and the R version line."""
    model = os.path.join(dv_dir, MODEL)
    if not os.path.isfile(model):
        raise IOError("trained model not found: " + model)
    if check_md5 and md5(model) != MODEL_MD5:
        raise RuntimeError("wrong MD5 for %s (expected %s)" % (model, MODEL_MD5))
    work = tempfile.mkdtemp(prefix="dvrf20_r_")
    try:
        script = os.path.join(work, "predict.R")
        out = os.path.join(work, "output.csv")
        with open(script, "w") as f:
            f.write(R_SCRIPT)
        p = subprocess.Popen([find_rscript(), "--vanilla", script, model, os.path.abspath(features_csv), out],
                             stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True)
        log = p.communicate()[0]
        if p.returncode != 0 or not os.path.isfile(out):
            raise RuntimeError("R failed:\n" + log[-2000:])
        with open(out) as f:
            rows = [(r["pdb"], float(r["pred"]), r["pred2"], float(r["vina"])) for r in csv.DictReader(f)]
        version = [l for l in log.splitlines() if l.startswith("R version")]
        return rows, (version[0] if version else "")
    finally:
        shutil.rmtree(work, ignore_errors=True)


# ----------------------------------------------------------------------------- mode B (Linux)
def setup_pipeline(dv_dir, tools_dir):
    """Checks the programs and puts the authors' modules on sys.path. MSMS's pdb_to_xyzr is a Python
    copy of the original awk script (pdb_to_xyzr.py) with the atmtypenumbers table of MSMS 2.6.1."""
    if sys.version_info[0] != 2:
        sys.exit("ERROR: the feature pipeline runs the authors' Python 2 code: use the deltavinarf20 "
                 "environment of environment_pipeline.yml (Docker image)")
    missing = [v for v in ("VINADIR", "MGLPY", "MGLUTIL") if not os.environ.get(v)]
    if missing:
        sys.exit("ERROR: set " + ", ".join(missing) + " (see INSTALL.md)")
    if not os.path.isfile(os.path.join(os.environ["VINADIR"], "vina")):
        sys.exit("ERROR: vina4dv not found in VINADIR=" + os.environ["VINADIR"])
    if not which("msms"):
        sys.exit("ERROR: msms not found on PATH")
    numfile = os.path.join(tools_dir, "atmtypenumbers")
    if not os.path.isfile(numfile):
        sys.exit("ERROR: atmtypenumbers (MSMS 2.6.1) not found in " + tools_dir)
    bindir = tempfile.mkdtemp(prefix="dvrf20_bin_")
    shim = os.path.join(bindir, "pdb_to_xyzr")
    with open(shim, "w") as f:
        f.write('#!/bin/sh\nexec "%s" "%s" --numfile "%s" "$@"\n'
                % (sys.executable, os.path.join(tools_dir, "pdb_to_xyzr.py"), numfile))
    os.chmod(shim, 0o755)
    os.environ["PATH"] = bindir + os.pathsep + os.environ["PATH"]
    for p in (os.path.join(dv_dir, "deltavina", "features"), dv_dir):
        if p not in sys.path:
            sys.path.insert(0, p)
    return bindir


def featurize(code, folder):
    """Features of one complex with the authors' functions, in a temporary folder (their code writes
    *.tmp files and a tmp/ folder in the current directory, and MGLTools' prepare_ligand4.py only finds
    the ligand when it runs in the ligand's folder)."""
    from deltavina.features import featureVina, featureSASA
    prot = os.path.abspath(os.path.join(folder, code + "_protein.pdb"))
    lig = os.path.abspath(os.path.join(folder, code + "_ligand.mol2"))
    for f in (prot, lig):
        if not os.path.isfile(f):
            raise IOError("file not found: " + f)
    old = os.getcwd()
    work = tempfile.mkdtemp(prefix="dvrf20_" + code + "_")
    try:
        shutil.copy(prot, os.path.join(work, code + "_protein.pdb"))
        shutil.copy(lig, os.path.join(work, code + "_ligand.mol2"))
        os.chdir(work)
        vina = featureVina.vina(code + "_protein.pdb", code + "_ligand.mol2")
        sasa = featureSASA.sasa(code + "_protein.pdb", code + "_ligand.mol2")
        feat = [vina.vinaScore] + vina.features(10) + list(sasa.sasalist)
    finally:
        os.chdir(old)
        shutil.rmtree(work, ignore_errors=True)
    if len(feat) != 21:
        raise RuntimeError("expected 21 features, got %d" % len(feat))
    return feat


def write_features(path, rows):
    with open(path, "w") as f:
        f.write("pdb," + ",".join(FEATURES) + "\n")
        for code, feat in rows:
            f.write(code + "," + ",".join(str(x) for x in feat) + "\n")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dv-dir", required=True, help="deltavina repository (with deltavina/models/rffit.rda)")
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--features", help="mode A: features CSV (pdb, vina, F1..F20)")
    g.add_argument("-d", "--dir", help="mode B: folder with one sub-folder per complex")
    g.add_argument("--complex", help="mode B: a single complex folder (its name is the code)")
    ap.add_argument("-o", "--out", default="predictions.csv")
    ap.add_argument("--tools-dir", default=HERE, help="folder with pdb_to_xyzr.py and atmtypenumbers (mode B)")
    args = ap.parse_args()

    feats_csv = args.features
    if not feats_csv:
        setup_pipeline(args.dv_dir, args.tools_dir)
        if args.complex:
            jobs = [(os.path.basename(os.path.normpath(args.complex)), args.complex)]
        else:
            jobs = [(c, os.path.join(args.dir, c)) for c in sorted(os.listdir(args.dir))
                    if os.path.isdir(os.path.join(args.dir, c))]
        rows, failed = [], []
        for i, (code, folder) in enumerate(jobs, 1):
            try:
                rows.append((code, featurize(code, folder)))
                print("[%d/%d] %s  features OK" % (i, len(jobs), code))
            except Exception as e:                  # keep going with the other complexes
                failed.append(code)
                print("[%d/%d] %s  FAILED: %s" % (i, len(jobs), code, e))
        if not rows:
            sys.exit("ERROR: no complex could be featurized")
        feats_csv = os.path.splitext(args.out)[0] + "_features.csv"
        write_features(feats_csv, rows)
        print("Features: %s (%d complexes, %d failed%s)" % (feats_csv, len(rows), len(failed),
                                                           ": " + " ".join(failed) if failed else ""))
    preds, rver = r_predict(args.dv_dir, feats_csv)
    with open(args.out, "w") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(["pdbid", "pKd_predicted", "pKd_rounded", "vina_pKd"])
        for code, pred, pred2, vina in preds:
            w.writerow([code, "%.4f" % pred, pred2, "%.4f" % vina])
            print("%s  pKd %.4f (%s)  Vina part %.4f" % (code, pred, pred2, vina))
    print("%s\nWrote %s (%d complexes)" % (rver, args.out, len(preds)))


if __name__ == "__main__":
    main()
