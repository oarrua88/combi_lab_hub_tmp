# DeepRLI — Installation guide (inference only)

**DeepRLI** predicts protein–ligand interactions with an improved **graph transformer** on a fully connected graph of the complex (ligand atoms + pocket atoms within 6.5 Å, with a cosine envelope on the edges) and a physics-informed module. It has three read-out heads: **scoring** (binding free energy ΔG, used here), **docking** and **screening**. It uses the 3D structure of the complex.

| | |
|---|---|
| Authors | H. Lin et al. (J. Pei and L. Lai groups, Peking University) — *Digital Discovery* 2025, <https://doi.org/10.1039/d4dd00403e> |
| Code | <https://github.com/fairydance/DeepRLI>, pinned commit `9d6e73993edded01de57b765da42fe58463c670a` (= tag v1.0.2 plus a README change; licence MIT) |
| Trained model | `trained_model.state_dict.pth`, 2.4 MB, **GitHub release v1.0.2** (the same file is attached to v1.0.0 and v1.0.1), MD5 `334ada642693c0f68a8b0305e77f0a29` |
| Hardware | CPU is enough (small model; the preprocessing with RDKit takes most of the time) |
| Reported CASF-2016 PCC | to be filled in from the paper (scoring power) |
| Origin | **Lista 2** of CombiLabHUB (systematic review of Transformer models, `Apresentação.pdf`, slides 22–23) |

Files in this folder:

| File | Purpose |
|---|---|
| `environment.yml` | Python 3.10 + PyTorch 2.2.2 + DGL 2.2.1 + RDKit 2023.9.6 (pip, Windows) |
| `Dockerfile` | Self-contained image (CPU PyTorch 2.3.1 + conda-forge DGL 2.2.1), downloads the code and the model and checks the MD5 |
| `predict_deeprli.py` | Scores a folder of complexes (one sub-folder per complex) with the authors' preprocessing and model |
| `test_1a30.py` | Installation test with complex **1a30** |
| `demo_deeprli.bat` | One-click Windows demo (conda) |
| `docker_deeprli.bat` / `docker_deeprli.sh` | Builds the Docker image (first time) and runs the test (Windows / Linux) |

> **What to know before using DeepRLI**
>
> 1. **Give it the full protein.** DeepRLI cuts the pocket itself: every residue with an atom closer than 6.5 Å to the ligand (`dist_cutoff`, authors' default). The wrapper copies `<code>_protein.pdb` as the authors' `receptor.pdb`.
> 2. **Ligand file order: `.sdf`, then `.mol2`** (as in the authors' README, `--ligand-file-types "sdf,mol2"`). If RDKit cannot read the `.sdf` — this happens for several CASF-2016 complexes, **1a30** among them — the `.mol2` is used. The output CSV says which file was used (`ligand_file`).
> 3. **The scoring head predicts ΔG in kcal/mol** (the training target, column `DeltaG` of the authors' index files). The wrapper converts it to pKd with pKd = −ΔG / (ln 10 · R · T), T = 298.15 K (factor 1.3643), the relation of the authors' data (pKd 5.70 ↔ ΔG −7.77 in their example). Both values are written to the CSV.
> 4. **Hyper-parameters** are the defaults of the authors' `infer.heavy.py` (hidden 64, 8 heads, batch norm, residual, envelope, multi-objective). The model is loaded with `torch.load(..., weights_only=True)`: only the weights, no pickled code.
> 5. **Versions.** The authors used Python 3.11 + PyTorch 2.0.1 + DGL 1.1.2 (CUDA 11.8). DGL 1.1.2 has no Windows CPU build on PyPI, so we use the same stack as the egGNN plugin: DGL 2.2.1 (last release with Windows wheels) with PyTorch 2.2.2 on Windows and the conda-forge DGL 2.2.1 with PyTorch 2.3.1 in Docker.
> 6. **Reference value for 1a30.** Neither the authors nor Eaves et al. 2026 publish a DeepRLI prediction for 1a30. `test_1a30.py` checks the model MD5, that the graph is built, and that the prediction is finite and repeatable; the reference `REF_PKD = 4.1986` (ΔG −5.7279 kcal/mol, experimental pKd 4.30) was recorded on 23/10/2026 and is identical with Windows conda and Docker.

---

## Quick demo (Windows, one click)

Double-click `demo_deeprli.bat` in this folder. It does the following:

1. Activates Miniconda.
2. Creates the `deeprli` environment if it does not exist. This takes several minutes, because PyTorch is a large download.
3. Downloads the DeepRLI code at the pinned commit (GitHub zip) into `%SF%\DeepRLI` and the trained model from release v1.0.2, and shows its MD5.
4. Runs `test_1a30.py`.

The window stays open at the end so you can read the result (`RESULT: PASS`).

The default paths match our lab computer. On another computer, set `SF`, `CASF` or `CONDA` in the Anaconda Prompt and run the script from there.

---

## A. Installation with Miniconda (Windows)

Requirements: Miniconda installed (`C:\Users\Admin\miniconda3`), internet access to GitHub and about 2 GB of free disk space.

All commands go in the **Anaconda Prompt (miniconda3)**.

### A1. Define the folders

```bat
set PLUGIN=C:\Users\Admin\Desktop\PROYECTO_UNIVERSIDAD\combi_lab_hub_tmp\plugins\deeprli
set SF=C:\Users\Admin\Desktop\PROYECTO_UNIVERSIDAD\sf
set CASF=C:\Users\Admin\Desktop\SOFTWARE SF\CASF-2016\CASF-2016
mkdir "%SF%"
```

> `set` only lasts for the current window. If you open a new Anaconda Prompt, run the three `set` lines again.

### A2. Create the conda environment

```bat
conda env create -f "%PLUGIN%\environment.yml"
conda activate deeprli
set DGLBACKEND=pytorch
python -W ignore -c "import torch, dgl, rdkit; print('torch', torch.__version__, '| dgl', dgl.__version__, '| rdkit', rdkit.__version__)"
```

Expected output: `torch 2.2.2+cpu | dgl 2.2.1 | rdkit 2023.09.6`.

### A3. Get the DeepRLI code (pinned commit) and the trained model

**Option 1, with Git:**

```bat
git clone https://github.com/fairydance/DeepRLI.git "%SF%\DeepRLI"
git -C "%SF%\DeepRLI" checkout 9d6e73993edded01de57b765da42fe58463c670a
```

**Option 2, without Git:**

```bat
curl -L -o "%SF%\DeepRLI.zip" https://github.com/fairydance/DeepRLI/archive/9d6e73993edded01de57b765da42fe58463c670a.zip
tar -xf "%SF%\DeepRLI.zip" -C "%SF%"
ren "%SF%\DeepRLI-9d6e73993edded01de57b765da42fe58463c670a" DeepRLI
```

**Trained model** (both options):

```bat
curl -L -o "%SF%\DeepRLI\trained_model.state_dict.pth" https://github.com/fairydance/DeepRLI/releases/download/v1.0.2/trained_model.state_dict.pth
certutil -hashfile "%SF%\DeepRLI\trained_model.state_dict.pth" MD5
```

It must print `334ada642693c0f68a8b0305e77f0a29`.

### A4. Run the installation test (complex 1a30)

```bat
conda activate deeprli
set DGLBACKEND=pytorch
python "%PLUGIN%\test_1a30.py" --deeprli-dir "%SF%\DeepRLI" --complex "%CASF%\coreset\1a30"
```

Expected result (a few seconds). Before `[2]`, RDKit prints `Explicit valence for atom # 6 C, 6, is greater than permitted` and `Could not sanitize molecule ending on line 102`: that is the `.sdf` of 1a30 failing, as expected (note 2); DeepRLI then uses the `.mol2`.

```
[1] Model ...\trained_model.state_dict.pth
    PASS - MD5 334ada642693c0f68a8b0305e77f0a29

[2] Complex graph built from 1a30_protein.pdb + 1a30_ligand.mol2
    PASS

[3] Prediction: DeltaG -5.7279 kcal/mol -> pKd 4.1986 (experimental 4.30)
    docking score -3.6945 | screening score -1.3636
    PASS - finite and identical in a second run

[4] pKd 4.1986 vs CombiLabHUB reference 4.1986
    PASS - matches the reference

RESULT: PASS
```

What each check verifies:
- `[1]` The trained model is the authors' file (release v1.0.2).
- `[2]` The authors' preprocessing reads the protein and the ligand and builds the complex graph. For 1a30 the `.sdf` cannot be read by RDKit, so the `.mol2` is used.
- `[3]` The model runs and is deterministic.
- `[4]` The value matches the CombiLabHUB reference (note 6).

### A5. Use DeepRLI on CASF-2016 or your own complexes

**CASF-2016 core set (285 complexes):**

```bat
python "%PLUGIN%\predict_deeprli.py" --deeprli-dir "%SF%\DeepRLI" -d "%CASF%\coreset" -o "%SF%\results_deeprli\predictions.csv"
```

The output CSV has `pdbid, pKd_predicted, DeltaG_predicted, docking_score, screening_score, ligand_file`.

**Your own complexes:** put each one in its own folder with `<code>_protein.pdb` and `<code>_ligand.sdf` and/or `<code>_ligand.mol2`. `--workdir <folder>` keeps DeepRLI's intermediate files (raw copies, processed graphs).

---

## B. Installation with Docker (alternative)

Requirements: Docker Desktop with the WSL2 backend, and internet access during the build (GitHub, Debian mirrors, conda-forge and PyPI). Steps A2–A3 are not needed. Or double-click `docker_deeprli.bat`.

### B1. Build the image

```bat
cd /d C:\Users\Admin\Desktop\PROYECTO_UNIVERSIDAD\combi_lab_hub_tmp\plugins\deeprli
docker build -t combilab/deeprli:1.0 .
```

The build fails on purpose if the MD5 of the model does not match.

### B2. Run the installation test

```bat
docker run --rm -v "C:\Users\Admin\Desktop\SOFTWARE SF\CASF-2016\CASF-2016\coreset\1a30:/complex:ro" combilab/deeprli:1.0 python /opt/deeprli/test_1a30.py --deeprli-dir /opt/DeepRLI --complex /complex
```

### B3. Score the CASF-2016 core set

```bat
docker run --rm -v "C:\Users\Admin\Desktop\SOFTWARE SF\CASF-2016\CASF-2016\coreset:/coreset:ro" -v "C:\Users\Admin\Desktop\PROYECTO_UNIVERSIDAD\sf\results_deeprli:/data" combilab/deeprli:1.0 python /opt/deeprli/predict_deeprli.py --deeprli-dir /opt/DeepRLI -d /coreset -o /data/predictions.csv
```

---

## Troubleshooting

| Symptom | Cause and fix |
|---|---|
| `Cannot find DGL C++ graphbolt library` | PyTorch version not supported by DGL 2.2.1. Recreate the environment from `environment.yml` (PyTorch 2.2.2). |
| `No module named 'torchdata.datapipes'` | torchdata 0.10 or newer. Install `torchdata==0.7.1` (Windows) or `0.8.0` (Docker). |
| `ERROR: MD5 of ... is not 334ada64...` | Incomplete download of the model. Delete it and download it again (step A3). |
| `WARNING: N complexes could not be processed` | RDKit could not read the ligand (`.sdf` nor `.mol2`) or the pocket. Check those files. |
| `Unpickling error ... weights_only` | Very old PyTorch. Use the versions in `environment.yml`. |
| Predictions differ from the reference | Different RDKit, PyTorch or DGL version. Check A2. |

## Uninstall

```bat
conda env remove -n deeprli
rmdir /s /q "%SF%\DeepRLI"
docker rmi combilab/deeprli:1.0
```

The last line is only needed if you used Docker.

---
*Prepared for CombiLabHUB (combi-lab) on 23/10/2026. Tested on 23/10/2026 on the lab computer: 1a30 test PASS with Windows + conda (Python 3.10, PyTorch 2.2.2, DGL 2.2.1, RDKit 2023.9.6) and with Docker (`combilab/deeprli:1.0`, PyTorch 2.3.1 CPU, conda-forge DGL 2.2.1); both give pKd 4.1986 for 1a30.*
