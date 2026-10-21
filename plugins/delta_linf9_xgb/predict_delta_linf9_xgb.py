"""delta_LinF9_XGB - batch prediction for a folder of protein-ligand complexes (Linux).

delta_LinF9_XGB (Yang & Zhang, J. Chem. Inf. Model. 2022) = Lin_F9 empirical score
+ an XGBoost correction (10 models, averaged) from 92 features: Vina/Lin_F9 terms
(smina), AlphaSpace2 beta-atom pocket features, MSMS surface areas, RDKit ligand
descriptors and bridging waters. It runs the authors' script/runXGB.py:run_XGB()
unchanged; this wrapper only:
  * points the authors' hard-coded paths (/home/cyang/...) to this installation:
    smina binaries and sf_vina.txt (software/), saved_model/, MGLTools'
    prepare_receptor4.py and an MSMS folder (msms executable + atmtypenumbers +
    pdb_to_xyzr, created on the fly; pdb_to_xyzr.py reproduces MSMS's awk script);
  * works on a copy of each complex in a temporary folder (run_XGB writes
    <protein>.pdbqt, betaAtoms.pdb, <ligand>.pdb next to the inputs);
  * returns the full-precision score instead of round(score, 3).

Only Linux: smina, MSMS and MGLTools are Linux programs. On Windows use the Docker
image (INSTALL.md, section B) or WSL.

Each complex folder must contain <code>_protein.pdb and <code>_ligand.mol2.
Water molecules in the protein file are used (bridging-water features).

Usage (inside the dlinf9 environment)
  python predict_delta_linf9_xgb.py --dl-dir <delta_LinF9_XGB folder> -d <complexes folder>
         [-o predictions.csv] [--adt <prepare_receptor4.py>] [--msms <msms executable>]
"""
import argparse
import contextlib
import io
import os
import shutil
import stat
import sys
import tempfile
import warnings

warnings.filterwarnings("ignore")

HERE = os.path.dirname(os.path.abspath(__file__))


def find_adt(adt=None):
    """MGLTools' prepare_receptor4.py: --adt, $ADT, or the 'mgltools' conda environment."""
    cands = [adt, os.environ.get("ADT"), shutil.which("prepare_receptor4.py")]
    prefix = os.environ.get("CONDA_PREFIX", "")
    if prefix:
        cands.append(os.path.join(os.path.dirname(prefix), "mgltools", "bin", "prepare_receptor4.py"))
    for c in cands:
        if c and os.path.isfile(c):
            return os.path.abspath(c)
    raise RuntimeError("prepare_receptor4.py (MGLTools) not found: use --adt or set ADT")


def setup(dl_dir, adt=None, msms=None, work=None):
    """Import the authors' scripts and point their global paths to this installation."""
    dl_dir = os.path.abspath(dl_dir)
    work = os.path.abspath(work)
    script = os.path.join(dl_dir, "script")
    if script not in sys.path:
        sys.path.insert(0, script)
    sw = os.path.join(dl_dir, "software")
    for exe in ("smina_feature", "smina.static"):
        p = os.path.join(sw, exe)
        os.chmod(p, os.stat(p).st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
    envbin = os.path.dirname(sys.executable)
    msms = msms or os.environ.get("MSMS") or shutil.which("msms") or \
        next((c for c in (os.path.join(envbin, "msms"),) if os.path.isfile(c)), None)
    if not msms:
        raise RuntimeError("msms executable not found: use --msms or install the bioconda msms package")
    mdir = os.path.join(work, "msms")
    os.makedirs(mdir, exist_ok=True)
    shutil.copy(os.path.join(sw, "atmtypenumbers"), mdir)
    link = os.path.join(mdir, "msms.x86_64Linux2.2.6.1")
    if not os.path.exists(link):
        os.symlink(os.path.abspath(msms), link)
    p2x = os.path.join(mdir, "pdb_to_xyzr")
    with open(p2x, "w") as f:
        f.write('#!/bin/sh\nexec "%s" "%s" "$@"\n' % (sys.executable, os.path.join(HERE, "pdb_to_xyzr.py")))
    os.chmod(p2x, 0o755)
    adt = find_adt(adt)
    # prepare_receptor4.py is Python 2 code; the authors call it as an executable, so wrap it
    # with the MGLTools Python (the python next to it in the mgltools environment, or $MGL_PYTHON).
    mgl_py = os.environ.get("MGL_PYTHON") or os.path.join(os.path.dirname(adt), "python")
    if not os.path.isfile(mgl_py):
        raise RuntimeError("MGLTools Python 2 not found next to %s: set MGL_PYTHON" % adt)
    adt_sh = os.path.join(work, "prepare_receptor4")
    with open(adt_sh, "w") as f:
        f.write('#!/bin/sh\nexec "%s" "%s" "$@"\n' % (mgl_py, adt))
    os.chmod(adt_sh, 0o755)
    adt = adt_sh

    import runXGB, calc_vina_features, calc_bridge_wat, featureSASA, prepare_betaAtoms   # authors' code
    runXGB._original_run_XGB = runXGB.run_XGB
    vina, smina, sf = (os.path.join(sw, "smina_feature"), os.path.join(sw, "smina.static"),
                       os.path.join(sw, "sf_vina.txt"))
    runXGB.Vina, runXGB.Smina, runXGB.SF, runXGB.ADT = vina, smina, sf, adt
    runXGB.model_dir = os.path.join(dl_dir, "saved_model")
    calc_vina_features.Vina, calc_vina_features.Smina, calc_vina_features.SF = vina, smina, sf
    calc_bridge_wat.smina = smina
    featureSASA.msmsdir = mdir
    prepare_betaAtoms.ADT = adt
    return runXGB


def predict_one(run_xgb_mod, protein, ligand, work):
    """Copy the complex to work/ and run the authors' run_XGB(). Returns the score (pK)."""
    os.makedirs(work, exist_ok=True)
    p = shutil.copy(protein, os.path.join(work, os.path.basename(protein)))
    l = shutil.copy(ligand, os.path.join(work, os.path.basename(ligand)))
    if not hasattr(run_xgb_mod, "_run_XGB_full"):
        # the authors' run_XGB() with its last line "XGB = round(..., 3)" kept at full precision
        import inspect
        code = inspect.getsource(run_xgb_mod.run_XGB)
        old_line = "XGB = round(y_predict[0]+LinF9,3)"
        if old_line not in code:
            raise RuntimeError("script/runXGB.py is not the expected version")
        exec(compile(code.replace(old_line, "XGB = float(y_predict[0]+LinF9)"), run_xgb_mod.__file__, "exec"),
             run_xgb_mod.__dict__)
        run_xgb_mod._run_XGB_full = run_xgb_mod.__dict__.pop("run_XGB")
        run_xgb_mod.run_XGB = run_xgb_mod._original_run_XGB
    old = os.getcwd()
    try:
        os.chdir(work)
        with contextlib.redirect_stdout(io.StringIO()):
            return float(run_xgb_mod._run_XGB_full(p, l))
    finally:
        os.chdir(old)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dl-dir", required=True, help="delta_LinF9_XGB folder (script/, software/, saved_model/)")
    ap.add_argument("-d", "--directory", required=True, help="folder with one sub-folder per complex")
    ap.add_argument("-o", "--output", default="predictions.csv", help="output CSV (default: predictions.csv)")
    ap.add_argument("--adt", help="MGLTools prepare_receptor4.py (default: $ADT or the 'mgltools' environment)")
    ap.add_argument("--msms", help="msms executable (default: $MSMS or msms on PATH)")
    a = ap.parse_args()
    import pandas as pd
    root = os.path.abspath(a.directory)
    tmp = tempfile.mkdtemp(prefix="dlinf9_")
    rows = []
    try:
        mod = setup(os.path.abspath(a.dl_dir), a.adt, a.msms, tmp)
        codes = sorted(d for d in os.listdir(root) if os.path.isdir(os.path.join(root, d)))
        for n, code in enumerate(codes, 1):
            f = os.path.join(root, code)
            try:
                s = predict_one(mod, os.path.join(f, code + "_protein.pdb"), os.path.join(f, code + "_ligand.mol2"),
                                os.path.join(tmp, code))
                rows.append((code, round(s, 4), ""))
                print("[%d/%d] %s  pKd %.4f" % (n, len(codes), code, s))
            except Exception as e:                       # noqa: BLE001
                rows.append((code, None, str(e).splitlines()[0][:200] if str(e) else type(e).__name__))
                print("[%d/%d] %s  ERROR: %s" % (n, len(codes), code, rows[-1][2]))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    out = pd.DataFrame(rows, columns=["pdbid", "pKd_predicted", "error"])
    os.makedirs(os.path.dirname(os.path.abspath(a.output)), exist_ok=True)
    out.to_csv(a.output, index=False)
    print("Done: %d complexes (%d errors) -> %s" % (len(out), out.pKd_predicted.isna().sum(), a.output))


if __name__ == "__main__":
    main()
