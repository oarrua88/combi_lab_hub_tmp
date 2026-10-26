"""CombiLabHUB - T-ALPHA predictions (inference only, CPU).

T-ALPHA (Kyro et al., J. Chem. Inf. Model. 2025) scores complexes stored in the authors'
HDF5 feature files (ESM2-3B protein embedding, SMILES-transformer and RDKit ligand vectors,
pocket/ligand/complex graphs and the protein surface point cloud, all already scaled).
The authors publish these files for their benchmarks on Zenodo 14510963 (test_files.tar.gz);
CASF_crystal.h5 holds the CASF-2016 core set built from the crystal structures.

This script runs the authors' own inference code (src/inference/perform_inference.py) on CPU
and writes predictions.csv (pdbid, pKd_predicted) like every other CombiLabHUB plugin.

Changes needed to run on CPU, applied here without touching the authors' files:
  * torch.cuda.synchronize() is called unconditionally in src/models/dmasif.py -> no-op;
  * EGNN_Encoder defaults to device="cuda" and full_model.py does not pass a device -> "cpu";
  * the checkpoint keys are renamed with the authors' update_parameter_keys() on a temporary
    copy (scripts/inference.py overwrites the original checkpoint instead);
  * perform_inference() builds the predictions table but does not save it -> captured here.

usage:
  python predict_t_alpha.py --talpha-dir <T-ALPHA repo> --ckpt <CASF.ckpt> --hdf <CASF_crystal.h5>
                            -o predictions.csv [--ids 1a30 1bcu ...] [--batch-size 8]
"""
import argparse
import os
import shutil
import sys
import tempfile
import types


def load_talpha(talpha_dir):
    import torch
    sys.path.insert(0, os.path.abspath(talpha_dir))
    if not torch.cuda.is_available():
        torch.cuda.synchronize = lambda *a, **k: None
        import src.models.egnn_encoder as EE
        d = EE.EGNN_Encoder.__init__.__defaults__
        EE.EGNN_Encoder.__init__.__defaults__ = tuple("cpu" if v == "cuda" else v for v in d)
    import matplotlib
    matplotlib.use("Agg")
    from src.utils.checkpoint_utils import update_parameter_keys
    import src.inference.perform_inference as PI
    return PI, update_parameter_keys


def predict(talpha_dir, ckpt, hdf, ids=None, batch_size=32, quiet=False):
    """Returns a DataFrame with columns pdbid, pKd_predicted, pKd_experimental."""
    import h5py
    import pandas as pd

    PI, update_parameter_keys = load_talpha(talpha_dir)
    tmp = tempfile.mkdtemp(prefix="talpha_")
    try:
        ck = os.path.join(tmp, "params_renamed.ckpt")
        update_parameter_keys(ckpt, ck)

        test = hdf
        with h5py.File(hdf, "r") as f:
            keys = list(f.keys())
            if ids:
                want = [i.lower() for i in ids]
                sel = [k for k in keys if k.lower() in want]
                missing = sorted(set(want) - {k.lower() for k in sel})
                if missing:
                    raise SystemExit("ERROR: not in %s: %s" % (hdf, ", ".join(missing)))
                test = os.path.join(tmp, "subset.h5")
                with h5py.File(test, "w") as g:
                    for k in sel:
                        f.copy(k, g)

        n = len(ids) if ids else len(keys)
        if n < 2:  # the authors' metrics need at least two points
            PI.pearsonr = PI.spearmanr = lambda a, b: (float("nan"), None)
            PI.r2_score = lambda a, b: float("nan")

        captured = {}

        def _df(*a, **k):
            captured["df"] = pd.DataFrame(*a, **k)
            return captured["df"]

        PI.pd = types.SimpleNamespace(DataFrame=_df)
        PI.plt.show = lambda *a, **k: None

        cwd = os.getcwd()
        os.chdir(tmp)  # the authors write scatter_plot.png to the working directory
        try:
            if quiet:
                import contextlib, io
                with contextlib.redirect_stdout(io.StringIO()):
                    PI.perform_inference(ckpt_path=ck, test_set_path=test, batch_size=batch_size,
                                         batch_norm=True, device="cpu")
            else:
                PI.perform_inference(ckpt_path=ck, test_set_path=test, batch_size=batch_size,
                                     batch_norm=True, device="cpu")
        finally:
            os.chdir(cwd)

        df = captured["df"]
        out = pd.DataFrame({
            "pdbid": [p.decode() if isinstance(p, bytes) else str(p) for p in df["pdbid"]],
            "pKd_predicted": df["prediction"].astype(float),
            "pKd_experimental": df["target"].astype(float),
        })
        return out
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--talpha-dir", required=True, help="T-ALPHA repository (pinned commit)")
    ap.add_argument("--ckpt", required=True, help="trained model, e.g. model_parameters/CASF.ckpt")
    ap.add_argument("--hdf", required=True, help="authors' feature file, e.g. test_files/CASF_crystal.h5")
    ap.add_argument("-o", "--output", default="predictions.csv")
    ap.add_argument("--ids", nargs="*", help="only these PDB codes (default: every complex in the file)")
    ap.add_argument("--batch-size", type=int, default=32,
                    help="default 32, as the authors' scripts/inference.py. Predictions change slightly "
                         "with the batch (see INSTALL.md); 32 over the whole CASF_crystal.h5 reproduces the paper")
    a = ap.parse_args()

    df = predict(a.talpha_dir, a.ckpt, a.hdf, a.ids, a.batch_size)
    os.makedirs(os.path.dirname(os.path.abspath(a.output)), exist_ok=True)
    df[["pdbid", "pKd_predicted"]].to_csv(a.output, index=False, float_format="%.4f")
    print("%d complexes -> %s" % (len(df), a.output))
    if len(df) >= 2:
        from scipy.stats import pearsonr
        print("PCC vs the experimental values stored in the HDF5 file: %.4f" %
              pearsonr(df["pKd_predicted"], df["pKd_experimental"])[0])


if __name__ == "__main__":
    main()
