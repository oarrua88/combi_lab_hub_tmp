# PointNet / PointTransformer — Installation guide (inference only)

This method turns a protein–ligand complex into a **point cloud** of 1024 atoms and scores it with a point-cloud neural network. Each point has six values: x, y, z, two atom features (van der Waals radius and atomic weight, scaled) and its origin (protein `1` or ligand `-1`). The authors' program `POINTNET` builds the cloud from the protein and ligand `.pdb` files. Two networks are available: **PointNet** and **PointTransformer**.

| | |
|---|---|
| Authors | Y. Wang, S. Sun, Z. Li, F. Liu, W. Zheng — *A point cloud-based deep learning strategy for protein–ligand binding affinity prediction*, Brief. Bioinform. 2022 (arXiv 2107.04340) |
| Code | <https://github.com/wyji001/Point-Cloud>, pinned commit `d1eae550bdaffbb877cb36a2a6e362d4dc625fe4` (no licence file) |
| Trained models | **In the repository**: 5 PointTransformer models (`Model/PointTransformer（B）/0.819…0.827.pth`, 77 MB each) and 5 PointNet models (`Model/PointNet（B）/0.764…0.794.pth`, 28 MB each), trained with the larger point-cloud set (refined + general). The file names are the validation PCCs. MD5 of `POINTNET` `2aaddebe49fd1d029a9e490ea447ade0`; MD5 of each model in the `Dockerfile` |
| Not used | The XGBoost variant (features and scripts on Google Drive) and the 2048-point and atom-channel clouds (`POINTNET-2048`, `POINTNET-atomchannel`), which have no trained network in the repository |
| Hardware | CPU is enough (a few seconds per complex). It was placed in Level 3 for its CUDA 11.1 requirements; no GPU is needed for inference |
| Reported CASF-2016 PCC | **0.859** PointTransformer, **0.831** PointNet (paper). Our Table 1 lists 0.852. Not checked by Eaves et al. 2026. |
| **Our check** | The 1a30 test passes (values below). There is no prepared CASF-2016 data from the authors to compare with, so the PCC of the paper is not checked yet. |

Files in this folder:

| File | Purpose |
|---|---|
| `environment.yml` | Environment `pointnet`: Python 3.10 + PyTorch 2.2.2 CPU + NumPy + Open Babel |
| `Dockerfile` | Self-contained image with the whole pipeline (Open Babel + `POINTNET` + models) |
| `predict_pointnet.py` | Scores a folder of complexes, or one ready point cloud (`--cloud`) |
| `test_1a30.py` | Installation test with complex **1a30** |
| `ref_1a30_cloud.txt` | Our point cloud of 1a30 (reference for the test; also used on Windows) |
| `demo_pointnet.bat` | One-click Windows demo (conda, models only) |
| `docker_pointnet.bat` / `docker_pointnet.sh` | Docker test on Windows / Linux (whole pipeline) |

> **What to know before using it**
>
> 1. **`POINTNET` is a Linux program.** It is a compiled x86-64 Linux executable with no source code. On Windows the conda environment can only score clouds that are already made. To make clouds on Windows, use Docker (`docker_pointnet.bat`).
> 2. **Preparation, as in the authors' README.** The wrapper keeps the `ATOM` records of `<code>_protein.pdb`, which removes waters, metals and ions. It removes all hydrogens and adds polar hydrogens with Open Babel (`--AddPolarH`). The ligand `<code>_ligand.mol2` is converted to `.pdb` with the same hydrogen treatment. The README does not say more, so other choices (for example adding all hydrogens) would give different clouds.
> 3. **Random rotations, made repeatable.** The authors' `pred.py` averages the 5 models over 5 random rotations of the cloud (25 predictions). PointTransformer also picks its first point at random. The wrapper does the same with a fixed seed (`--seed 0` by default), so the same input always gives the same pKd. With other seeds, 1a30 changes by about ±0.1–0.3.
> 4. **Default network: PointTransformer** (the best of the paper). `--model PointNet` uses the other one.
> 5. **No reference values from the authors.** The test values below are our own (Linux, PyTorch 2.3.1 CPU). The authors' example cloud `example/5c2h_11.09` is used as a second check.

---

## Quick demo (Windows, one click)

Double-click `demo_pointnet.bat` in this folder. It does the following:

1. Activates Miniconda.
2. Creates the `pointnet` environment if it does not exist.
3. Unzips the code and models from `Funciones_Score_Tabla1\pointnet.zip` into `%SF%\PointNet`.
4. Checks the MD5 of one model.
5. Runs `test_1a30.py`. Step 1 of the test (making the cloud) is skipped on Windows, and steps 2–3 use `ref_1a30_cloud.txt`.

For the whole pipeline, including the cloud, run `docker_pointnet.bat`.

---

## A. Installation with Miniconda (Windows: models only; Linux: whole pipeline)

All commands go in the **Anaconda Prompt (miniconda3)**.

### A1. Define the folders

```bat
set PLUGIN=C:\Users\Admin\Desktop\PROYECTO_UNIVERSIDAD\combi_lab_hub_tmp\plugins\pointnet
set SF=C:\Users\Admin\Desktop\PROYECTO_UNIVERSIDAD\sf
set CASF=C:\Users\Admin\Desktop\SOFTWARE SF\CASF-2016\CASF-2016
mkdir "%SF%"
```

### A2. Create the conda environment

```bat
conda env create -f "%PLUGIN%\environment.yml"
conda activate pointnet
python -c "import torch, numpy; print('torch', torch.__version__, '| numpy', numpy.__version__)"
```

Expected output: `torch 2.2.2+cpu | numpy 1.26.4`.

### A3. Get the code and models (pinned commit)

**Option 1, with Git** (about 500 MB):

```bat
git clone https://github.com/wyji001/Point-Cloud.git "%SF%\PointNet"
git -C "%SF%\PointNet" checkout d1eae550bdaffbb877cb36a2a6e362d4dc625fe4
```

**Option 2, without Git:** unzip `SOFTWARE SF\Funciones_Score_Tabla1\pointnet.zip`. Its content is identical to that commit. Rename the folder `Point-Cloud-HEAD` to `PointNet` and move it into `%SF%`.

### A4. Run the installation test (complex 1a30)

```bat
conda activate pointnet
python -W ignore "%PLUGIN%\test_1a30.py" --pointnet-dir "%SF%\PointNet" --complex "%CASF%\coreset\1a30"
```

Expected result on Linux or Docker (on Windows, step [1] says `SKIPPED`):

```
[1] Point cloud of 1a30 (Open Babel + POINTNET):
    PASS - same 1024 points as the reference cloud

[2] Authors' example cloud 5c2h (5 models x 5 rotations, seed 0):
    PointTransformer pKd 7.4829 (reference 7.4829) PASS
    PointNet         pKd 7.5160 (reference 7.5160) PASS

[3] 1a30 (experimental pKd 4.30):
    PointTransformer pKd 4.6973 (reference 4.6973) PASS   models: 4.18 4.68 5.32 4.78 4.53
    PointNet         pKd 4.7429 (reference 4.7429) PASS   models: 4.02 5.46 4.71 5.43 4.09

RESULT: PASS
```

What each check verifies:
- `[1]` Open Babel and `POINTNET` build the same cloud of 1a30 as ours (993 protein + 31 ligand points).
- `[2]` and `[3]` The 10 trained models and PyTorch give our reference values.

### A5. Use it on CASF-2016 or your own complexes (Linux or Docker)

```bash
python -W ignore predict_pointnet.py --pointnet-dir $SF/PointNet -d $CASF/coreset -o predictions.csv --keep-clouds clouds/
```

The output CSV has `pdbid, pKd_predicted` (mean of the 5 models) and `pKd_model0..4`. `--keep-clouds` saves the clouds, which can then be scored on Windows with `--cloud <file>`.

---

## B. Installation with Docker (whole pipeline, recommended)

Requirements: Docker Desktop with the WSL2 backend, and internet access during the build (Docker Hub, GitHub, Debian mirrors and conda-forge). The image is about 3 GB. `docker_pointnet.bat` (Windows) or `docker_pointnet.sh` (Linux) do B1 and B2 in one step.

### B1. Build the image

```bat
cd /d C:\Users\Admin\Desktop\PROYECTO_UNIVERSIDAD\combi_lab_hub_tmp\plugins\pointnet
docker build -t combilab/pointnet:1.0 .
```

The build fails on purpose if the MD5 of `POINTNET` or of a model does not match.

### B2. Run the installation test

```bat
docker run --rm -v "C:\Users\Admin\Desktop\SOFTWARE SF\CASF-2016\CASF-2016\coreset\1a30:/complex:ro" combilab/pointnet:1.0 python -W ignore /opt/pointnet/test_1a30.py --pointnet-dir /opt/PointCloud --complex /complex
```

### B3. Score the CASF-2016 core set

```bat
docker run --rm -v "C:\Users\Admin\Desktop\SOFTWARE SF\CASF-2016\CASF-2016\coreset:/coreset:ro" -v "C:\Users\Admin\Desktop\PROYECTO_UNIVERSIDAD\sf\results_pointnet:/data" combilab/pointnet:1.0 python -W ignore /opt/pointnet/predict_pointnet.py --pointnet-dir /opt/PointCloud -d /coreset -o /data/predictions.csv --keep-clouds /data/clouds
```

---

## Troubleshooting

| Symptom | Cause and fix |
|---|---|
| `POINTNET is a Linux program` | You are on Windows conda. Use Docker for the clouds, or score ready clouds with `--cloud`. |
| `terminate called without an active exception` | `POINTNET` received a file it cannot read (for example a `.mol2`). It only reads `.pdb`; use `predict_pointnet.py`. |
| `Open Babel failed` | The `pointnet` environment is not active. Run `conda activate pointnet` and `obabel -V`. |
| `expected 5 .pth files` | The model folders were renamed. Their names contain full-width parentheses: `PointTransformer（B）`. Unzip again. |
| Values differ slightly from the reference | Another PyTorch version, or another `--seed`. A difference of a few hundredths is normal. |

## Uninstall

```bat
conda env remove -n pointnet
rmdir /s /q "%SF%\PointNet"
docker rmi combilab/pointnet:1.0
```

---
*Prepared for CombiLabHUB (combi-lab). Tested on 22/10/2026 on Linux with Python 3.10, PyTorch 2.3.1 (CPU, conda-forge) and Open Babel 3.1.1: the 1a30 test passes. The Docker image could not be built on the test machine (no access to Docker Hub), and Windows conda (PyTorch 2.2.2) was not run: run the demo and `docker_pointnet.bat` to confirm. The paper's PCC (0.859 / 0.831) has not been checked yet.*
