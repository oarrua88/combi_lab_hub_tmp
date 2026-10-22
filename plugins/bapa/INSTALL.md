# BAPA — Installation guide (inference only)

**BAPA** is a convolutional neural network with an attention mechanism. It predicts protein–ligand binding affinity from two inputs:

- **Descriptor counts:** how often each of 2,500 selected small protein–ligand atom graphs (built from Sybyl atom types, within 12 Å) occurs in the complex. They are computed from the protein and ligand `.mol2` files.
- **Six Vina terms:** gauss1, gauss2, repulsion, hydrophobic, hydrogen bond and rotatable bonds. `rf-extract` (RF-Score v3) computes them from the `.pdbqt` files.

| | |
|---|---|
| Authors | S. Seo, J. Choi, S. Park, J. Ahn — *Binding affinity prediction for protein–ligand complex using deep attention mechanism based on intermolecular interactions*, BMC Bioinformatics 2021, 22, 542 |
| Code | <https://github.com/Blue1993/BAPA>, pinned commit `e53a2f9596647e6f3bfd2861960e19b3963b32b1` (no licence file) |
| Trained network | **In the repository**, `module/network/BAPA_network.*` (TensorFlow 1 checkpoint), with `module/normalized_parameters.pkl` and `module/selected_descriptors_list.pkl`. MD5 of `BAPA_network.data-00000-of-00001`: `8f33149ef5647678b837d76de4d07ccc` (the others are in the `Dockerfile`) |
| rf-extract | The original repository (`HongjianLi/RF-Score`) is no longer on GitHub. We use the fork <https://github.com/lachrymator/RF-Score>, commit `8d05430bccdbd29f1f8247cb7e8939ee6967b6a5` (Apache 2.0). It gives the authors' Vina terms exactly. `bin/` has it already compiled: `rf-extract.exe` (Windows, built with MinGW, static) and `rf-extract` (Linux, static) |
| Hardware | CPU (well under 1 s per complex). It was in Level 3 for TensorFlow 1.12, UCSF Chimera and RF-Score |
| Reported CASF-2016 PCC | 0.819 (paper). Not checked by Eaves et al. 2026 |
| **Our check** | The authors' example complex **10gs** is reproduced end to end: `.pdbqt` files, Vina terms, descriptor counts and the pKd 4.91 of their `result/result.csv`. The CASF-2016 PCC is not checked yet. |

Files in this folder:

| File | Purpose |
|---|---|
| `environment.yml` | Environment `bapa`: Python 3.6 + TensorFlow 1.12 CPU + Open Babel 2.4.1 + scikit-learn 0.22 |
| `Dockerfile` | Self-contained image (compiles rf-extract from the fork) |
| `bin/rf-extract.exe`, `bin/rf-extract` | rf-extract for Windows and Linux; `bin/RF-Score_LICENSE.txt` is its licence |
| `predict_bapa.py` | Scores a folder of complexes (one per sub-folder) with the authors' code |
| `test_1a30.py` | Installation test: authors' example 10gs + CASF-2016 complex **1a30** |
| `demo_bapa.bat` | One-click Windows demo (conda) |
| `docker_bapa.bat` / `docker_bapa.sh` | Docker test on Windows / Linux |

> **What to know before using BAPA**
>
> 1. **Open Babel must be 2.4.1.** The authors convert the protein `.pdb` and ligand `.mol2` to `.pdbqt` with `babel` 2.4.1. Open Babel 3 writes the receptor atoms in another order, and rf-extract then gives a different hydrophobic term (10gs: 38.15 or 37.98 instead of 39.66). With 2.4.1 our `.pdbqt` files are identical to the authors' ones.
> 2. **The protein `.mol2` matters.** The authors make it with **UCSF Chimera** (`write format mol2`). With the Chimera `.mol2` of their example, our descriptor counts equal theirs. For CASF-2016 the wrapper uses by default the `<code>_protein.mol2` that comes with CASF-2016 (`--protein-mol2 casf`). If UCSF Chimera is installed and in the PATH, `--protein-mol2 chimera` follows the authors exactly. `--protein-mol2 obabel` is a last resort. For 10gs it changes the pKd from 4.91 to 5.42, and for 1a30 from 5.54 to 5.06.
> 3. **Waters are removed** from the `.pdb` before the `.pdbqt` conversion, as in the authors' `convert_to_PDBQT.py`. The ligand `.mol2` is used as it is.
> 4. **One network, no ensemble.** `predict_bapa.py` writes `pdbid, pKd_predicted` and the six Vina terms.

---

## Quick demo (Windows, one click)

Double-click `demo_bapa.bat` in this folder. It does the following:

1. Activates Miniconda.
2. Creates the `bapa` environment if it does not exist (several minutes).
3. Unzips the BAPA code and network from `Funciones_Score_Tabla1\BAPA.zip`.
4. Checks the MD5 of the network.
5. Runs `test_1a30.py`.

The window stays open at the end so you can read the result (`RESULT: PASS`).

---

## A. Installation with Miniconda (Windows)

Requirements: Miniconda installed (`C:\Users\Admin\miniconda3`) and about 1.5 GB of free disk space.

All commands go in the **Anaconda Prompt (miniconda3)**.

### A1. Define the folders

```bat
set PLUGIN=C:\Users\Admin\Desktop\PROYECTO_UNIVERSIDAD\combi_lab_hub_tmp\plugins\bapa
set SF=C:\Users\Admin\Desktop\PROYECTO_UNIVERSIDAD\sf
set CASF=C:\Users\Admin\Desktop\SOFTWARE SF\CASF-2016\CASF-2016
mkdir "%SF%"
```

### A2. Create the conda environment

```bat
conda env create -f "%PLUGIN%\environment.yml"
conda activate bapa
python -c "import tensorflow as tf; print('tensorflow', tf.__version__)"
babel -V
```

Expected output: `tensorflow 1.12.0` and `Open Babel 2.4.1`.

### A3. Get the BAPA code (pinned commit)

**Option 1, with Git:**

```bat
git clone https://github.com/Blue1993/BAPA.git "%SF%\BAPA"
git -C "%SF%\BAPA" checkout e53a2f9596647e6f3bfd2861960e19b3963b32b1
```

**Option 2, without Git:** unzip `SOFTWARE SF\Funciones_Score_Tabla1\BAPA.zip`. Its content is identical to that commit. Rename the folder `BAPA-HEAD` to `BAPA` and move it into `%SF%`.

### A4. Run the installation test

```bat
conda activate bapa
python -W ignore "%PLUGIN%\test_1a30.py" --bapa-dir "%SF%\BAPA" --complex "%CASF%\coreset\1a30"
```

Expected result (a few seconds, after some TensorFlow messages):

```
[1] Authors' example 10gs:
    Vina terms  111.8976 1374.5154 5.2593 39.6612 7.0350 0.0690 PASS
    Descriptors 2500 counts, sum 7400 PASS - same as the authors' dataset.pkl
    pKd 4.9104 (authors' result.csv: 4.91) PASS

[2] 1a30 (experimental pKd 4.30), protein .mol2 from CASF-2016:
    Vina terms  85.6817 1306.8164 4.7111 30.4484 3.5947 0.0741 PASS
    pKd 5.5433 (reference 5.5433) PASS

RESULT: PASS
```

What each check verifies:
- `[1]` Open Babel 2.4.1, rf-extract, the descriptor code and the network reproduce the authors' own example.
- `[2]` The same pipeline on 1a30 gives our reference values. The authors publish none for 1a30.

### A5. Use BAPA on CASF-2016 or your own complexes

**CASF-2016 core set (285 complexes):**

```bat
python -W ignore "%PLUGIN%\predict_bapa.py" --bapa-dir "%SF%\BAPA" -d "%CASF%\coreset" -o "%SF%\results_bapa\predictions.csv"
```

**Your own complexes:** put each one in its own folder with `<code>_protein.pdb`, `<code>_ligand.mol2` and, for the default mode, `<code>_protein.mol2`. Otherwise use `--protein-mol2 chimera` (UCSF Chimera installed) or `obabel`.

---

## B. Installation with Docker (alternative)

Requirements: Docker Desktop with the WSL2 backend, and internet access during the build (Docker Hub, GitHub, Debian mirrors, conda-forge and PyPI). Steps A2–A3 are not needed. `docker_bapa.bat` (Windows) or `docker_bapa.sh` (Linux) do B1 and B2 in one step.

### B1. Build the image

```bat
cd /d C:\Users\Admin\Desktop\PROYECTO_UNIVERSIDAD\combi_lab_hub_tmp\plugins\bapa
docker build -t combilab/bapa:1.0 .
```

The build fails on purpose if the MD5 of a network file does not match.

### B2. Run the installation test

```bat
docker run --rm -v "C:\Users\Admin\Desktop\SOFTWARE SF\CASF-2016\CASF-2016\coreset\1a30:/complex:ro" combilab/bapa:1.0 python /opt/bapa/test_1a30.py --bapa-dir /opt/BAPA --complex /complex
```

### B3. Score the CASF-2016 core set

```bat
docker run --rm -v "C:\Users\Admin\Desktop\SOFTWARE SF\CASF-2016\CASF-2016\coreset:/coreset:ro" -v "C:\Users\Admin\Desktop\PROYECTO_UNIVERSIDAD\sf\results_bapa:/data" combilab/bapa:1.0 python /opt/bapa/predict_bapa.py --bapa-dir /opt/BAPA -d /coreset -o /data/predictions.csv
```

---

## Troubleshooting

| Symptom | Cause and fix |
|---|---|
| `Vina terms ... FAIL`, only the hydrophobic term differs | Open Babel 3 is being used. Check `babel -V` (must be 2.4.1) inside the `bapa` environment. |
| `rf-extract not found` | `bin\rf-extract.exe` is missing from the plugin folder. Use `--rf-extract <path>`. |
| `rf-extract failed` | The `.pdbqt` files are empty. Check that the protein `.pdb` and ligand `.mol2` exist. |
| `<code>_protein.mol2 not found` | The folder has no protein `.mol2`. Use `--protein-mol2 chimera` or `obabel`. |
| `--protein-mol2 chimera needs UCSF Chimera in the PATH` | Install UCSF Chimera 1.x (free for academic use) and add its `bin` folder to the PATH. |
| Many TensorFlow `FutureWarning` messages | They come from TensorFlow 1.12 with NumPy 1.19 and are harmless. |

## Uninstall

```bat
conda env remove -n bapa
rmdir /s /q "%SF%\BAPA"
docker rmi combilab/bapa:1.0
```

---
*Prepared for CombiLabHUB (combi-lab). Tested on 22/10/2026 on Linux with exactly this `environment.yml` (Python 3.6, TensorFlow 1.12.0 CPU, Open Babel 2.4.1, NumPy 1.19.5): the test passes. `bin/rf-extract.exe` was also run under Wine and gives the same Vina terms as the Linux build. All packages in `environment.yml` exist for Windows. The Docker image could not be built on the test machine (no access to Docker Hub). On Windows, run the demo and `docker_bapa.bat` to confirm.*
