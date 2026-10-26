# T-ALPHA — Installation guide (inference only)

**T-ALPHA** predicts protein–ligand binding affinity (pKd) with a hierarchical transformer that combines six views of the complex: protein sequence (ESM2-3B embedding), protein surface (dMaSIF point cloud), pocket graph, ligand properties (RDKit descriptors), ligand sequence (pre-trained SMILES transformer) and ligand graph, plus a protein–ligand complex graph.

| | |
|---|---|
| Authors | G. W. Kyro et al. (Yale) — *J. Chem. Inf. Model.* 65(5), 2395–2415 (2025), <https://doi.org/10.1021/acs.jcim.4c02332>; preprint bioRxiv 10.1101/2024.12.19.629497 |
| Code | <https://github.com/gregory-kyro/T-ALPHA>, pinned commit `f9973d1966b61986178ab4370c73e46b4401d140` (licence MIT) |
| Trained model | `model_parameters/CASF.ckpt` (92 MB, MD5 `704f963c2fe2f8363e4cc06fd4a2f304`), inside `model_parameters.tar.gz` (1.4 GB, MD5 `16f1b83b90b9c2b84a0960bbbf3365da`), Zenodo [14510963](https://zenodo.org/records/14510963). Trained on PDBbind v2020 without the CASF-2016 core set |
| CASF-2016 inputs | `test_files/CASF_crystal.h5` (348 MB, MD5 `b853bbf8dd86edfd8c8f01e95bdf08aa`), inside `test_files.tar.gz` (847 MB, MD5 `68cc4568df39f72f5e3beb3562131a41`), same Zenodo record. Features already computed by the authors |
| Hardware | CPU is enough (the 289 complexes of the file take about 1 minute) |
| Operating system | **Linux only.** On Windows: **Docker** (section B) or WSL (section A) |
| Reported CASF-2016 results | PCC **0.869**, RMSE 1.112, MAE 0.875, Spearman 0.860 (paper). Reproduced exactly with the files above (see note 3) |
| Origin | **Lista 2** of CombiLabHUB (systematic review of Transformer models, `Apresentação.pdf`, slides 22–23), Level 2 |

Files in this folder:

| File | Purpose |
|---|---|
| `environment.yml` | Python 3.11 + CPU PyTorch 2.5.1 + PyG 2.6.1 + torch_cluster (conda-forge), Lightning 2.4 and pykeops 2.2.3 (pip), C++ compiler for pykeops |
| `Dockerfile` | Self-contained image (same packages), downloads code, model and CASF-2016 features with MD5 checks |
| `predict_t_alpha.py` | Scores the complexes of the authors' HDF5 feature file on CPU → `predictions.csv` |
| `test_1a30.py` | Installation test with complex **1a30** |
| `demo_t_alpha.bat` | One-click Windows demo **through Docker** |
| `docker_t_alpha.bat` / `docker_t_alpha.sh` | Builds the Docker image (first time) and runs the test (Windows / Linux) |

> **What to know before using T-ALPHA**
>
> 1. **It scores the authors' feature files, not the CASF-2016 PDB/mol2 files.** Building the features of a new complex needs the 3-billion-parameter ESM2 protein model (about 11 GB of RAM in float32), the authors' pre-trained SMILES transformer (854 MB plus its 1.3 GB training CSV, needed to rebuild the vocabulary), Open Babel and a GPU-oriented surface step. That pipeline exists only in the authors' Colab notebook (`T-ALPHA.ipynb`) and is **not** part of this plugin. The test therefore uses the 1a30 entry of `CASF_crystal.h5`.
> 2. **`CASF_crystal.h5` is not exactly the CASF-2016 core set.** It has 289 complexes: 283 of the 285 core-set complexes (**1g2k** and **1sqa** are missing) plus 6 others (3cyx, 4mrw, 4mrz, 4msc, 4msn, 5c1w). The paper's metrics are over these 289. On the 283 core-set complexes the PCC is 0.867.
> 3. **Predictions change a little with the batch.** The model's output for a complex depends slightly on the other complexes in the same batch (for 1a30: 5.7758 alone, 5.7024 in the authors' first batch of 32, 5.7326 in batches of 8). `predict_t_alpha.py` uses batches of 32 by default, like the authors' `scripts/inference.py`: over the whole file this gives exactly the paper's numbers (PCC 0.869, RMSE 1.112, MAE 0.875, Spearman 0.860). With batches of 1 the PCC is 0.872. The test checks both situations.
> 4. **Changes needed to run on CPU**, applied by `predict_t_alpha.py` without touching the authors' files: `torch.cuda.synchronize()` is called unconditionally in `src/models/dmasif.py` (made a no-op); `EGNN_Encoder` creates its layers on `"cuda"` because `full_model.py` does not pass a device (default changed to `"cpu"`); the checkpoint keys are renamed with the authors' `update_parameter_keys()` on a temporary copy (their `scripts/inference.py` overwrites the original file); `perform_inference()` builds the predictions table but does not save it (captured and written to `predictions.csv`).
> 5. **pykeops compiles C++ code the first time it runs** (about 20 seconds; cached in `~/.cache/keops2.2.3`). It needs `g++` (included in `environment.yml` and in the image) and has no official Windows support, so the plugin is Linux/WSL/Docker only.
> 6. **Reference values for 1a30** (own values, 25/10/2026, Linux, both with pip and conda-forge PyTorch 2.5.1 CPU): alone `5.7758`, authors' batch `5.7024` (experimental 4.30).

---

## Quick demo (Windows, one click, needs Docker Desktop)

Open Docker Desktop and wait for "Engine running". Then double-click `demo_t_alpha.bat`. The first time it builds the image: it downloads about 2.3 GB from Zenodo and keeps only the 440 MB it needs, then compiles the pykeops kernels. The window must end with `RESULT: PASS`.

---

## A. Installation with Miniconda (Linux or WSL)

```bash
PLUGIN=~/combi_lab_hub_tmp/plugins/t_alpha     # this folder
SF=~/sf                                        # code, model and data of each SF
```

On WSL, the Windows folders are under `/mnt/c/...`, e.g. `SF=/mnt/c/Users/Admin/Desktop/PROYECTO_UNIVERSIDAD/sf`.

### A1. Environment

```bash
conda env create -f "$PLUGIN/environment.yml"
conda activate talpha
python -c "import torch, torch_geometric, torch_cluster, pykeops; print(torch.__version__, torch_geometric.__version__)"
```

Expected: `2.5.1 2.6.1` (and a KeOps warning saying it runs in CPU-only mode).

### A2. Code (pinned commit)

```bash
git clone https://github.com/gregory-kyro/T-ALPHA.git "$SF/T-ALPHA"
git -C "$SF/T-ALPHA" checkout f9973d1966b61986178ab4370c73e46b4401d140
```

### A3. Model and CASF-2016 features (Zenodo 14510963)

```bash
mkdir -p "$SF/T-ALPHA/data" && cd "$SF/T-ALPHA/data"
curl -L -o model_parameters.tar.gz "https://zenodo.org/records/14510963/files/model_parameters.tar.gz?download=1"
curl -L -o test_files.tar.gz "https://zenodo.org/records/14510963/files/test_files.tar.gz?download=1"
md5sum model_parameters.tar.gz test_files.tar.gz
tar -xzf model_parameters.tar.gz model_parameters/CASF.ckpt
tar -xzf test_files.tar.gz test_files/CASF_crystal.h5
```

The MD5 must be `16f1b83b90b9c2b84a0960bbbf3365da` and `68cc4568df39f72f5e3beb3562131a41`. The archives also hold the other checkpoints and test sets of the paper (LP-PDBbind, BDB2020+, EGFR, Mpro, ablations); only the two files above are needed here, so the archives can be deleted afterwards.

### A4. Installation test (complex 1a30)

```bash
python -W ignore "$PLUGIN/test_1a30.py" --talpha-dir "$SF/T-ALPHA" --data-dir "$SF/T-ALPHA/data"
```

Expected (under a minute; the first run also compiles pykeops):

```
[1] Model .../model_parameters/CASF.ckpt
    Features .../test_files/CASF_crystal.h5
    PASS - MD5 704f963c2fe2f8363e4cc06fd4a2f304, b853bbf8dd86edfd8c8f01e95bdf08aa

[2] 1a30 in CASF_crystal.h5 (289 complexes): experimental pKd 4.30
    PASS

[3] 1a30 alone: pKd 5.7758 (experimental 4.30) vs CombiLabHUB reference 5.7758
    PASS - matches the reference

[4] 1a30 in the authors' setting (first batch of 32 complexes): pKd 5.7024 vs reference 5.7024
    PASS - matches the reference
    (the whole file with batches of 32 gives the paper's CASF-2016 metrics: PCC 0.869, RMSE 1.112)

RESULT: PASS
```

### A5. Predictions

```bash
python -W ignore "$PLUGIN/predict_t_alpha.py" --talpha-dir "$SF/T-ALPHA" \
    --ckpt "$SF/T-ALPHA/data/model_parameters/CASF.ckpt" \
    --hdf "$SF/T-ALPHA/data/test_files/CASF_crystal.h5" -o "$SF/results_t_alpha/predictions.csv"
```

Output: `predictions.csv` (`pdbid, pKd_predicted`) for the 289 complexes of the file. `--ids 1a30 1bcu ...` scores only some of them.

---

## B. Installation with Docker (Windows or Linux)

Double-click `docker_t_alpha.bat` (Windows) or run `./docker_t_alpha.sh` (Linux), or:

```bat
cd /d C:\Users\Admin\Desktop\PROYECTO_UNIVERSIDAD\combi_lab_hub_tmp\plugins\t_alpha
docker build -t combilab/t_alpha:1.0 .
docker run --rm combilab/t_alpha:1.0 python -W ignore /opt/t_alpha/test_1a30.py --talpha-dir /opt/T-ALPHA --data-dir /opt/talpha_data
```

The build fails on purpose if any MD5 does not match, and it runs the test once so the pykeops kernels stay compiled inside the image. The model and features are already inside the image, so no folder needs to be mounted for the test. To save the CASF-2016 predictions:

```bat
docker run --rm -v "C:\Users\Admin\Desktop\PROYECTO_UNIVERSIDAD\sf\results_t_alpha:/data" combilab/t_alpha:1.0 python -W ignore /opt/t_alpha/predict_t_alpha.py --talpha-dir /opt/T-ALPHA --ckpt /opt/talpha_data/model_parameters/CASF.ckpt --hdf /opt/talpha_data/test_files/CASF_crystal.h5 -o /data/predictions.csv
```

---

## Troubleshooting

| Symptom | Cause and fix |
|---|---|
| `RuntimeError: Found no NVIDIA driver` | You ran the authors' `scripts/inference.py` on a computer without GPU. Use `predict_t_alpha.py` / `test_1a30.py` (note 4). |
| `ImportError: 'knn' requires 'torch-cluster'` | torch_cluster is missing. Recreate the environment from `environment.yml` (conda-forge `pytorch_cluster`). |
| KeOps error about `g++` or `CXX` | No C++ compiler. With conda, activate the environment (it sets `CXX`); otherwise install `g++`. |
| `[3]` or `[4]` FAIL by a few hundredths | Different PyTorch/PyG build. Recreate the environment from `environment.yml` or use Docker. |
| `[1] FAIL - MD5 ...` | Incomplete download. Download the archive again and check its MD5. |

## Uninstall

```bash
conda env remove -n talpha
rm -rf "$SF/T-ALPHA" ~/.cache/keops2.2.3
docker rmi combilab/t_alpha:1.0
```

---
*Prepared for CombiLabHUB (combi-lab) on 25/10/2026. Tested on 25/10/2026 on Linux with pip wheels (PyTorch 2.5.1 + torch_cluster built from source) and with the conda-forge environment of `environment.yml`: 1a30 test PASS (5.7758 / 5.7024), whole `CASF_crystal.h5` reproduces the paper (PCC 0.869, RMSE 1.112). Docker image tested on the lab computer (Windows + Docker Desktop) on 25/10/2026: test PASS with the same values.*
