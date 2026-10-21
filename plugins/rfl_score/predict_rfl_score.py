"""RFL-Score - prediction with the trained Random Forest of the authors (combi-lab).

RFL-Score v1 (Arrua, Aderhold, Werhli & Machado, IEEE CIBCB 2024) is a Random Forest
(R package randomForest, scoring/RScript/model/scoring_function_160.rda) on 160 features
selected with LassoCV from 723: amino-acid composition (FASTA), DSSP, NNScore 2.0/BINANA,
PaDEL, RDKit 2D/3D, SASA and Vina terms (vina4dv).

Two ways to use it:

  A) From a features table (any OS; needs only R + randomForest):
       python predict_rfl_score.py --rfl-dir <rfl-score_v1> --features <..._160_input.csv> -o predictions.csv
     The table has an id column first (e.g. 'pdb') and the 160 features (as written by the authors' sf160.py).

  B) Full pipeline for a folder of complexes (Linux or the Docker image): computes the 160
     features with the authors' scoring/Descriptors code, unchanged, then predicts:
       python predict_rfl_score.py --rfl-dir <rfl-score_v1> -d <complexes folder> -o predictions.csv
     Each complex folder needs <code>_protein.pdb, <code>_ligand.mol2 and the protein
     sequence: a *.fasta / *.fasta.txt file in the folder; if there is none, --fasta-from
     chooses: rcsb (download https://www.rcsb.org/fasta/entry/<CODE>, as the authors did;
     default) or pdb (built from the protein file; chains not in the file, e.g. peptide
     ligands, are then missing and the amino-acid features change).
     Programs: Open Babel 2.4 ('babel'), Java (PaDEL), DSSP, MGLTools ($MGLPY, $MGLUTIL),
     vina4dv ($VINADIR) and R. Two adaptations, applied at run time:
       * DSSP 4.2 no longer accepts 'dssp -i in -o out' (4.0.4, used by the authors, still
         does): with DSSP 4 a small 'dssp' wrapper is put first on PATH that calls
         'mkdssp --output-format dssp in out' (or the old form if that fails);
       * MGLTools' prepare_ligand4.py only finds the ligand when it runs in the ligand's
         folder: Vina58.prepare_ligand is replaced by the same command run from there.
     With these, the 160 features of the authors' example 1a30 (examples/1a30) are
     reproduced exactly.

The prediction is the authors' R model (predict.randomForest); their R script rounds it to
2 decimals, here it is written with 4.
"""
import argparse
import os
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
MODEL = os.path.join("scoring", "RScript", "model", "scoring_function_160.rda")
FEATURES = os.path.join("scoring", "FeatureSelection", "features_selected_160.csv")

R_CODE = r'''
args <- commandArgs(trailingOnly = TRUE)
suppressMessages(library(randomForest))
load(args[1])
df <- read.table(args[2], header = TRUE, stringsAsFactors = FALSE, sep = ",", check.names = FALSE)
feats <- read.table(args[3], header = TRUE, sep = ",", stringsAsFactors = FALSE, check.names = FALSE)[[1]]
missing <- setdiff(feats, names(df))
if (length(missing) > 0) stop(paste("missing features:", paste(missing, collapse = " ")))
pred <- predict(scoring_function, newdata = df[, feats])
write.table(data.frame(pdbid = df[[1]], pKd_predicted = sprintf("%.4f", pred)), args[4],
            sep = ",", row.names = FALSE, quote = FALSE)
cat("randomForest", as.character(packageVersion("randomForest")), "\n")
'''


def find_rscript():
    pre = os.environ.get("CONDA_PREFIX") or sys.prefix
    cands = [os.environ.get("RSCRIPT"), shutil.which("Rscript")]
    for base in dict.fromkeys([pre, sys.prefix]):
        cands += [os.path.join(base, "Lib", "R", "bin", "x64", "Rscript.exe"), os.path.join(base, "Lib", "R", "bin", "Rscript.exe"),
                  os.path.join(base, "Scripts", "Rscript.exe"), os.path.join(base, "bin", "Rscript")]
    for c in cands:
        if c and os.path.isfile(c):
            return c
    raise RuntimeError("Rscript not found: install R (environment.yml) or set RSCRIPT")


def r_predict(rfl_dir, features_csv, out_csv):
    """Run the authors' Random Forest on a features table. Returns a DataFrame (pdb, pKd_predicted)."""
    import pandas as pd
    tmp = tempfile.mkdtemp(prefix="rfl_r_")
    try:
        script = os.path.join(tmp, "predict.R")
        with open(script, "w") as f:
            f.write(R_CODE)
        r = subprocess.run([find_rscript(), "--vanilla", script, os.path.join(rfl_dir, MODEL),
                            os.path.abspath(features_csv), os.path.join(rfl_dir, FEATURES), os.path.abspath(out_csv)],
                           capture_output=True, text=True)
        if r.returncode != 0:
            raise RuntimeError("R failed:\n" + (r.stderr or r.stdout)[-1500:])
        return pd.read_csv(out_csv)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


# ------------------------------------------------------------------ full pipeline (Linux)
def _dssp_real():
    """The DSSP program and whether it needs the wrapper (DSSP >= 4.2 dropped 'dssp -i in -o out')."""
    exe = shutil.which("dssp") or shutil.which("mkdssp")
    if not exe:
        raise RuntimeError("DSSP not found (apt install dssp)")
    out = subprocess.run([exe, "--version"], capture_output=True, text=True)
    txt = (out.stdout + out.stderr).lower()
    return os.path.realpath(exe), ("version 4" in txt or "mkdssp version" in txt)


def setup_pipeline(rfl_dir, work):
    """Environment variables, DSSP wrapper and the prepare_ligand fix. Returns the authors' modules."""
    for var in ("MGLPY", "MGLUTIL", "VINADIR"):
        if not os.environ.get(var):
            raise RuntimeError("$%s is not set (MGLTools / vina4dv, see INSTALL.md)" % var)
    real, wrap = _dssp_real()
    if wrap:
        bindir = os.path.join(work, "bin")
        os.makedirs(bindir, exist_ok=True)
        with open(os.path.join(bindir, "dssp"), "w") as f:
            f.write('#!/bin/sh\nIN=""; OUT=""\nwhile [ $# -gt 0 ]; do case "$1" in -i) IN="$2"; shift 2;; '
                    '-o) OUT="$2"; shift 2;; *) shift;; esac; done\n'
                    '"%s" --output-format dssp "$IN" "$OUT" 2>/dev/null || exec "%s" -i "$IN" -o "$OUT"\n' % (real, real))
        os.chmod(os.path.join(bindir, "dssp"), 0o755)
        os.environ["PATH"] = bindir + os.pathsep + os.environ["PATH"]
    for exe in ("msms", "msms.x86_64Linux2.2.6.1", "msms.x86_64Linux2.2.6.1.staticgcc", "pdb_to_xyzr", "pdb_to_xyzrn"):
        p = os.path.join(rfl_dir, "scoring", "Descriptors", "Sasa10", "msms", exe)
        if os.path.isfile(p):
            os.chmod(p, 0o755)
    if rfl_dir not in sys.path:
        sys.path.insert(0, rfl_dir)
    from scoring.Descriptors import Descriptors          # authors' code
    from scoring.Descriptors.Vina58 import Vina58
    from scoring.FeatureSelection import FeatureSelection

    def prepare_ligand(ligand, tmp_folder_name):
        flig, _ = os.path.splitext(os.path.basename(ligand))
        out = os.path.abspath(os.path.join(tmp_folder_name, flig + ".pdbqt"))
        log = os.path.abspath(os.path.join(tmp_folder_name, "out2.tmp"))
        os.system('cd "%s" && $MGLPY $MGLUTIL/prepare_ligand4.py -l "%s" -o "%s" -U nphs > "%s"'
                  % (os.path.dirname(os.path.abspath(ligand)), os.path.basename(ligand), out, log))
        return out
    Vina58.prepare_ligand = prepare_ligand
    return Descriptors, FeatureSelection


def find_fasta(folder, code, source, cache):
    for f in sorted(os.listdir(folder)):
        if ".fasta" in f.lower() or f.lower().endswith(".fa"):
            return os.path.join(folder, f), "file"
    os.makedirs(cache, exist_ok=True)
    out = os.path.join(cache, code.upper() + ".fasta.txt")
    if source == "rcsb":
        if not os.path.isfile(out):
            import urllib.request
            with urllib.request.urlopen("https://www.rcsb.org/fasta/entry/%s" % code.upper(), timeout=60) as r:
                data = r.read().decode()
            if not data.startswith(">"):
                raise RuntimeError("RCSB returned no FASTA for %s" % code)
            with open(out, "w") as f:
                f.write(data)
        return out, "rcsb"
    from Bio.PDB import PDBParser
    from Bio.SeqUtils import seq1
    s = PDBParser(QUIET=True).get_structure(code, os.path.join(folder, code + "_protein.pdb"))
    with open(out, "w") as f:
        for ch in s[0]:
            seq = "".join(seq1(r.get_resname()) for r in ch if r.id[0] == " ")
            if seq:
                f.write(">%s:%s\n%s\n" % (code.upper(), ch.id, seq))
    return out, "pdb"


def featurize(rfl_dir, complexes, work, fasta_from="rcsb"):
    """complexes: list of (code, folder). Returns the 160-feature DataFrame and the FASTA source per code."""
    import pandas as pd
    Descriptors, FeatureSelection = setup_pipeline(rfl_dir, work)
    rows, src = [], {}
    old = os.getcwd()
    os.chdir(rfl_dir)                                   # the authors' code uses relative paths
    try:
        for code, folder in complexes:
            fasta, src[code] = find_fasta(folder, code, fasta_from, os.path.join(work, "fasta"))
            tmp = os.path.join(work, "tmp_" + code)
            os.makedirs(tmp, exist_ok=True)
            pdblist = pd.DataFrame([{"receptor": os.path.join(folder, code + "_protein.pdb"),
                                     "ligand": os.path.join(folder, code + "_ligand.mol2"),
                                     "fasta": fasta, "receptor_mol2": None}])
            dt, _ = Descriptors.get_descriptors(descriptor_names=Descriptors.get_features_names(), tmp_folder_name=tmp,
                                                pdblist=pdblist,
                                                features_selected=FeatureSelection.load_features_selected_160())
            dt.index = [code]
            rows.append(dt)
    finally:
        os.chdir(old)
    feats = pd.concat(rows)
    feats.index.name = "pdb"
    return feats, src


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--rfl-dir", required=True, help="rfl-score_v1 folder (scoring/, sf160.py)")
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--features", help="CSV with 'pdb' + the 160 features (mode A)")
    g.add_argument("-d", "--directory", help="folder with one sub-folder per complex (mode B, Linux/Docker)")
    ap.add_argument("-o", "--output", default="predictions.csv")
    ap.add_argument("--fasta-from", choices=("rcsb", "pdb"), default="rcsb",
                    help="when a complex folder has no FASTA file (mode B): rcsb (default) or pdb")
    a = ap.parse_args()
    rfl = os.path.abspath(a.rfl_dir)
    os.makedirs(os.path.dirname(os.path.abspath(a.output)), exist_ok=True)
    if a.features:
        df = r_predict(rfl, a.features, a.output)
        print(df.to_string(index=False))
        return
    root = os.path.abspath(a.directory)
    codes = sorted(d for d in os.listdir(root) if os.path.isdir(os.path.join(root, d)))
    work = tempfile.mkdtemp(prefix="rfl_")
    try:
        feats, src = featurize(rfl, [(c, os.path.join(root, c)) for c in codes], work, a.fasta_from)
        fcsv = os.path.splitext(os.path.abspath(a.output))[0] + "_features160.csv"
        feats.to_csv(fcsv)
        df = r_predict(rfl, fcsv, a.output)
        df["fasta_source"] = [src.get(str(c), "") for c in df.pdbid]
        df.to_csv(a.output, index=False)
        print(df.to_string(index=False))
        print("Features -> %s" % fcsv)
    finally:
        shutil.rmtree(work, ignore_errors=True)


if __name__ == "__main__":
    main()
