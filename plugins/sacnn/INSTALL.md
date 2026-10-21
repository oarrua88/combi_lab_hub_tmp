# saCNN — Installation guide (inference only)

**saCNN** is a 3D convolutional neural network with **spatial attention**, so that it focuses on the voxels near the interaction centres. Each complex becomes a 24 × 24 × 24 Å grid centred on the ligand, with 16 channels: 8 moleculekit atom-property channels for the protein and 8 for the ligand. The prediction is the mean over 24 rotations of the grid.

| | |
|---|---|
| Authors | Y. Wang, Z. Qiu, Q. Jiao, C. Chen, Z. Meng, X. Cui — IEEE BIBM 2021, <https://ieeexplore.ieee.org/document/9669781> |
| Code | <https://github.com/xfcui/saCNN>, pinned commit `3e42aa93796d32deab1d266f1f32113ef4254301` (licence MIT) |
| Trained model | `checkpoint/model.pkl`, 18.2 MB, **included in the repository**, MD5 `0418f265c1dc6758a4a76aae0ae7531c` |
| Example features | `data/feature/3jvr.h5` (complex 3jvr), MD5 `ffcee2ab2523c4fd7fee7b9ebddb8a7b` |
| Hardware | CPU is enough (about 3 s per complex, mostly protein preparation) |
| Reported CASF-2016 PCC | 0.865 — Eaves et al. 2026 reproduce **0.862** |

Files in this folder:

| File | Purpose |
|---|---|
| `environment.yml` | Python 3.10 + PyTorch 2.5.1 + moleculekit 1.11.5 + pdb2pqr 3.6.1 + propka 3.5.1 + RDKit 2024.3.5 (versions checked for Windows) |
| `Dockerfile` | Self-contained image (CPU PyTorch) |
| `predict_sacnn.py` | Featurises and scores a folder of complexes (one protein–ligand pair per sub-folder) with the authors' network and checkpoint |
| `test_1a30.py` | Installation test with complex **1a30** (and the authors' example 3jvr) |
| `demo_sacnn.bat` | One-click Windows demo |

> **What to know before using saCNN**
>
> 1. **HTMD is not needed (and no longer installs).** The authors' README asks for `htmd=2.0.6`, which requires Acellera's non-public `acemd3`. Their scripts only use HTMD for the `Molecule` class and for one fallback; `Molecule` comes from moleculekit. `predict_sacnn.py` does the featurisation (the authors' `src/data.py`) and the scoring (`src/inference.py`) in one step, with moleculekit only, and imports the authors' `src/model.py` and `src/Rotations.py` unchanged.
> 2. **Protein preparation follows Eaves et al.** We use the corrected preparation of their fork (<https://github.com/jeavesj/saCNN>, commit `e7c166f2b96ad7272b284d1a671c295970dd8aa2`): remove LLP residues, keep the original bonds, `prepareProteinForAtomtyping` (pdb2pqr + propka at pH 7.4), drop atoms left without bonds and voxelise without validity checks. If that fails, the same is retried without the input hydrogens. Eaves et al. have one more fallback in between (HTMD `proteinPrepare` + CHARMM build); it needs HTMD and is **not** included, so a complex that only works with it is reported as failed. The output column `protein_preparation` says which preparation was used.
> 3. **The result depends on the moleculekit / pdb2pqr / propka versions**, because the protonation states (e.g. ASP 25 of the HIV protease becomes ASH in 1a30) change the voxel channels. Our versions are the same as Eaves et al. (moleculekit 1.11.5, pdb2pqr 3.6.1, propka 3.5.1). The test checks that our features of 3jvr are identical to the authors' `3jvr.h5`.
> 4. **The checkpoint was saved on a GPU.** The authors' `inference.py` fails on a CPU-only computer (`Attempting to deserialize object on a CUDA device`); the wrapper loads it with `map_location="cpu"`.
> 5. **mdtraj on Windows** (a moleculekit dependency) has no PyPI wheel, so `environment.yml` takes it from conda-forge.

---

## Quick demo (Windows, one click)

Double-click `demo_sacnn.bat` in this folder. It does the following:

1. Activates Miniconda.
2. Creates the `sacnn` environment if it does not exist. This takes several minutes, because PyTorch is a large download.
3. Unzips the saCNN code and checkpoint from `Funciones_Score_Tabla1\saCNN.zip`.
4. Checks the MD5 of `model.pkl`.
5. Runs `test_1a30.py`.

The window stays open at the end so you can read the result (`RESULT: PASS`).

The default paths match our lab computer. On another computer, set `SF`, `CASF`, `ZIP` or `CONDA` in the Anaconda Prompt and run the script from there.

---

## A. Installation with Miniconda (Windows)

Requirements: Miniconda installed (`C:\Users\Admin\miniconda3`) and about 2 GB of free disk space.

All commands go in the **Anaconda Prompt (miniconda3)**.

### A1. Define the folders

```bat
set PLUGIN=C:\Users\Admin\Desktop\PROYECTO_UNIVERSIDAD\combi_lab_hub_tmp\plugins\sacnn
set SF=C:\Users\Admin\Desktop\PROYECTO_UNIVERSIDAD\sf
set CASF=C:\Users\Admin\Desktop\SOFTWARE SF\CASF-2016\CASF-2016
mkdir "%SF%"
```

> `set` only lasts for the current window. If you open a new Anaconda Prompt, run the three `set` lines again.

### A2. Create the conda environment

```bat
conda env create -f "%PLUGIN%\environment.yml"
conda activate sacnn
python -W ignore -c "import torch, moleculekit, rdkit; print('torch', torch.__version__, '| moleculekit', moleculekit.__version__, '| rdkit', rdkit.__version__)"
```

Expected output: `torch 2.5.1+cpu | moleculekit 1.11.5 | rdkit 2024.03.5`. On Windows, the PyPI build of PyTorch is CPU-only.

### A3. Get the saCNN code (pinned commit)

**Option 1, with Git:**

```bat
git clone https://github.com/xfcui/saCNN.git "%SF%\saCNN"
git -C "%SF%\saCNN" checkout 3e42aa93796d32deab1d266f1f32113ef4254301
```

**Option 2, without Git:** unzip `SOFTWARE SF\Funciones_Score_Tabla1\saCNN.zip`. Its content is identical to that commit. Rename the folder `saCNN-HEAD` to `saCNN` and move it into `%SF%`.

Check the checkpoint:

```bat
certutil -hashfile "%SF%\saCNN\checkpoint\model.pkl" MD5
```

It must print `0418f265c1dc6758a4a76aae0ae7531c`.

### A4. Run the installation test (complex 1a30)

```bat
conda activate sacnn
python "%PLUGIN%\test_1a30.py" --sacnn-dir "%SF%\saCNN" --complex "%CASF%\coreset\1a30"
```

Expected result (about 10 s):

```
[1] Authors' features of 3jvr (data/feature/3jvr.h5): pKd 4.7484 (reference 4.7484)
    PASS - matches the reference

[2] Our features of 3jvr vs the authors' 3jvr.h5: max. difference 3.05e-07
    PASS - same features

[3] CASF-2016 1a30 (protein preparation: standard): pKd 5.0950 (reference 5.0950, experimental 4.30)
    PASS - matches the reference

RESULT: PASS
```

What each check verifies:
- `[1]` The network, the checkpoint and PyTorch, using the features the authors ship.
- `[2]` That moleculekit, pdb2pqr and propka produce the same voxel features as the authors' environment.
- `[3]` The whole pipeline on CASF-2016 1a30. The value is **exactly** the one of Eaves et al. (`5.09495…` in `casf2016_saCNN_preds_and_times.csv` of their fork). 3jvr also matches their value (4.7484).

### A5. Use saCNN on CASF-2016 or your own complexes

**CASF-2016 core set (285 complexes):**

```bat
python "%PLUGIN%\predict_sacnn.py" --sacnn-dir "%SF%\saCNN" -d "%CASF%\coreset" -o "%SF%\results_sacnn\predictions.csv"
```

The output CSV has `pdbid, pKd_predicted, protein_preparation`. Complexes that could not be prepared are listed at the end.

**Your own complexes:** put each one in its own folder with `<code>_protein.pdb` and `<code>_ligand.mol2`. The grid is centred on the ligand, so the ligand must be in its binding pose.

---

## B. Installation with Docker (alternative)

Requirements: Docker Desktop with the WSL2 backend, and internet access during the build (GitHub, Debian mirrors, conda-forge and PyPI). Steps A2–A3 are not needed.

### B1. Build the image

```bat
cd /d C:\Users\Admin\Desktop\PROYECTO_UNIVERSIDAD\combi_lab_hub_tmp\plugins\sacnn
docker build -t combilab/sacnn:1.0 .
```

The build fails on purpose if the MD5 of `model.pkl` or `3jvr.h5` does not match.

### B2. Run the installation test

```bat
docker run --rm -v "C:\Users\Admin\Desktop\SOFTWARE SF\CASF-2016\CASF-2016\coreset\1a30:/complex:ro" combilab/sacnn:1.0 python /opt/sacnn/test_1a30.py --sacnn-dir /opt/saCNN --complex /complex
```

### B3. Score the CASF-2016 core set

```bat
docker run --rm -v "C:\Users\Admin\Desktop\SOFTWARE SF\CASF-2016\CASF-2016\coreset:/coreset:ro" -v "C:\Users\Admin\Desktop\PROYECTO_UNIVERSIDAD\sf\results_sacnn:/data" combilab/sacnn:1.0 python /opt/sacnn/predict_sacnn.py --sacnn-dir /opt/saCNN -d /coreset -o /data/predictions.csv
```

---

## Troubleshooting

| Symptom | Cause and fix |
|---|---|
| `PackagesNotFoundError: htmd=2.0.6` / `acemd3` | You followed the authors' README. HTMD is not needed: use `environment.yml`. |
| `Attempting to deserialize object on a CUDA device` | The authors' `inference.py` on a CPU-only computer. Use `predict_sacnn.py` (or add `map_location="cpu"`). |
| `Skipping <code>: protein preparation failed` | pdb2pqr/propka could not prepare that protein (non-standard residues, broken backbone). Fix the `.pdb` (e.g. with PDBFixer) and run again. |
| `No module named 'mdtraj'` on Windows | Recreate the environment from `environment.yml` (mdtraj comes from conda-forge). |
| Check `[2]` fails | Different moleculekit, pdb2pqr or propka version. Check A2. |

## Uninstall

```bat
conda env remove -n sacnn
rmdir /s /q "%SF%\saCNN"
docker rmi combilab/sacnn:1.0
```

The last line is only needed if you used Docker.

---
*Prepared for CombiLabHUB (combi-lab). Tested on 20/10/2026 on Linux with Python 3.10, PyTorch 2.5.1 (CPU), moleculekit 1.11.5, pdb2pqr 3.6.1, propka 3.5.1 and RDKit 2024.03.5: all three checks pass, and 1a30 and 3jvr match Eaves et al. to every printed digit. All Windows packages in `environment.yml` were checked to exist for Python 3.10. On Windows, run step A4, or the demo, to confirm.*
