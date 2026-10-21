# delta_LinF9_XGB — Installation guide (inference only)

**delta_LinF9_XGB** is a *delta machine-learning* scoring function: the empirical **Lin_F9** score plus an **XGBoost correction** (10 models, averaged) computed from 92 features. These include smina/Vina interaction terms, AlphaSpace2 pocket features (ligand coverage, beta score), MSMS buried surface areas by pharmacophore type, RDKit ligand descriptors and bridging-water terms.

| | |
|---|---|
| Authors | C. Yang, Y. Zhang — *J. Chem. Inf. Model.* 62 (2022), <https://doi.org/10.1021/acs.jcim.2c00485> |
| Code | <https://github.com/cyangNYU/delta_LinF9_XGB>, pinned commit `54ae79584f7e22f5af3e28625b9f387f0b74cc0f` (licence GPL-3.0) |
| Trained models | `saved_model/mod_1…10.pickle.dat` (xgboost 1.2.0), **included in the repository** (e.g. `mod_1` MD5 `6bde159de18b9f601437f42683bdf468`) |
| Programs | smina (`software/smina.static`, `software/smina_feature`, in the repository, MD5 `2d0cf016…` / `4d33f4c3…`), AlphaSpace2 (`software/AlphaSpace2_2021.tar.gz`, in the repository), **MSMS 2.6.1** (conda-forge) and **MGLTools 1.5.7** (bioconda, Python 2.7) |
| Operating system | **Linux only.** On Windows: **Docker** (section B) or WSL (section A) |
| Hardware | CPU is enough |
| Reported CASF-2016 PCC | 0.845 (paper) — Eaves et al. 2026: 0.84 ("statistically reproduced") |

Files in this folder:

| File | Purpose |
|---|---|
| `environment.yml` | `dlinf9` environment: Python 3.8 + RDKit 2020.09.5 + Open Babel 3.1.1 + xgboost 1.2.0 + mdtraj + MSMS (Linux) |
| `environment_mgltools.yml` | `mgltools` environment: MGLTools 1.5.7 (Python 2.7), for `prepare_receptor4.py` |
| `Dockerfile` | Self-contained image with everything above (the way to run it on Windows) |
| `predict_delta_linf9_xgb.py` | Scores a folder of complexes with the authors' `script/runXGB.py:run_XGB()` |
| `pdb_to_xyzr.py` | Python version of MSMS's `pdb_to_xyzr` script, which the MSMS conda package does not include |
| `test_1a30.py` | Installation test: the authors' example 1e66 + complex **1a30** |
| `demo_delta_linf9_xgb.bat` | One-click Windows demo **through Docker** |

> **What to know before using delta_LinF9_XGB**
>
> 1. **Paths.** The authors' scripts have their own paths written in (`/home/cyang/...`) for smina, `sf_vina.txt`, MGLTools, MSMS and the models; the README asks you to edit them. `predict_delta_linf9_xgb.py` sets them at run time to this installation, without editing any file. It also builds the MSMS folder the scripts expect (MSMS executable, `software/atmtypenumbers` and `pdb_to_xyzr`). Our `pdb_to_xyzr.py` gives byte-identical output to the original awk script of MSMS 2.6.1 (checked on 1crn and the 1a30 protein).
> 2. **MGLTools is Python 2.** `prepare_receptor4.py` runs with the Python of the `mgltools` environment. It prints many `Sorry, there are no Gasteiger parameters available for atom …` lines; they are harmless.
> 3. **Waters matter.** The protein file is used with its crystallographic waters (bridging-water features). The CASF-2016 core-set protein files have no waters. That matches the "dry" set the authors scored in `dataset/test_set.csv`. For 1a30, our 92 features match theirs except 4: 3 smina terms and the AlphaSpace beta score (−8.7 vs −10.5), probably because of the MGLTools version (1.5.7 vs their 1.5.6). This changes the prediction by 0.02 (ours 5.1582, with their features 5.1792). Their example `test/1e66_wat` gives 8.9115 (README: 8.893), the same size of difference.
> 4. **Old xgboost.** The models are pickled `XGBRegressor` objects from xgboost 1.2.0 and are used with `ntree_limit`, which was removed in xgboost 2. Keep xgboost 1.2.0.

---

## Quick demo (Windows, one click, needs Docker Desktop)

Open Docker Desktop, then double-click `demo_delta_linf9_xgb.bat` in this folder. It does the following:

1. Checks that Docker is running.
2. Builds the image `combilab/delta_linf9_xgb:1.0` the first time. This takes several minutes and downloads the code from GitHub.
3. Runs `test_1a30.py` inside the container with your CASF-2016 1a30 folder. The window must end with `RESULT: PASS`.

---

## A. Installation with Miniconda (Linux or WSL)

In a Linux terminal (or Ubuntu on WSL):

### A1. Define the folders

```bash
PLUGIN=/path/to/combi_lab_hub_tmp/plugins/delta_linf9_xgb
SF=/path/to/sf
CASF=/path/to/CASF-2016
mkdir -p "$SF"
```

On WSL, the Windows folders are under `/mnt/c/...`, e.g. `CASF="/mnt/c/Users/Admin/Desktop/SOFTWARE SF/CASF-2016/CASF-2016"`.

### A2. Create the two conda environments

```bash
conda env create -f "$PLUGIN/environment.yml"
conda env create -f "$PLUGIN/environment_mgltools.yml"
```

### A3. Get the code (pinned commit) and install AlphaSpace2

```bash
git clone https://github.com/cyangNYU/delta_LinF9_XGB.git "$SF/delta_LinF9_XGB"
git -C "$SF/delta_LinF9_XGB" checkout 54ae79584f7e22f5af3e28625b9f387f0b74cc0f
conda activate dlinf9
pip install --no-deps "$SF/delta_LinF9_XGB/software/AlphaSpace2_2021.tar.gz"
chmod +x "$SF/delta_LinF9_XGB/software/smina.static" "$SF/delta_LinF9_XGB/software/smina_feature"
```

Without Git: unzip `SOFTWARE SF/Funciones_Score_Tabla1/delta_LinF9_XGB.zip` (identical to that commit) and rename `delta_LinF9_XGB-HEAD` to `delta_LinF9_XGB`.

### A4. Run the installation test

```bash
conda activate dlinf9
export ADT="$(conda info --base)/envs/mgltools/bin/prepare_receptor4.py"
python -W ignore "$PLUGIN/test_1a30.py" --dl-dir "$SF/delta_LinF9_XGB" --complex "$CASF/coreset/1a30"
```

Expected output (end):

```
[1] 1e66_wat: 8.9115 (reference 8.9115; authors' README 8.893)
    PASS

[2] Predicted pKd 1a30: 5.1582 (reference 5.1582; with the authors' published features 5.1792; experimental 4.30)
    PASS

RESULT: PASS
```

### A5. Score CASF-2016 or your own complexes

Each complex in its own folder, with `<code>_protein.pdb` and `<code>_ligand.mol2`:

```bash
python -W ignore "$PLUGIN/predict_delta_linf9_xgb.py" --dl-dir "$SF/delta_LinF9_XGB" -d "$CASF/coreset" -o "$SF/results_delta_linf9_xgb/predictions.csv"
```

Output columns: `pdbid, pKd_predicted, error`.

---

## B. Installation with Docker (Windows)

### B1. Build the image

```bat
cd /d C:\Users\Admin\Desktop\PROYECTO_UNIVERSIDAD\combi_lab_hub_tmp\plugins\delta_linf9_xgb
docker build -t combilab/delta_linf9_xgb:1.0 .
```

### B2. Run the installation test

```bat
docker run --rm -v "C:\Users\Admin\Desktop\SOFTWARE SF\CASF-2016\CASF-2016\coreset\1a30:/complex:ro" combilab/delta_linf9_xgb:1.0 python -W ignore /opt/delta_linf9_xgb/test_1a30.py --dl-dir /opt/delta_LinF9_XGB --complex /complex
```

### B3. Score the CASF-2016 core set

```bat
docker run --rm -v "C:\Users\Admin\Desktop\SOFTWARE SF\CASF-2016\CASF-2016\coreset:/coreset:ro" -v "C:\Users\Admin\Desktop\PROYECTO_UNIVERSIDAD\sf\results_delta_linf9_xgb:/data" combilab/delta_linf9_xgb:1.0 python -W ignore /opt/delta_linf9_xgb/predict_delta_linf9_xgb.py --dl-dir /opt/delta_LinF9_XGB -d /coreset -o /data/predictions.csv
```

---

## Troubleshooting

| Problem | Cause / fix |
|---|---|
| `prepare_receptor4.py (MGLTools) not found` | Create the `mgltools` environment (A2) and set `ADT` (A4), or pass `--adt`. |
| `SyntaxError: Missing parentheses in call to 'print'` | `prepare_receptor4.py` ran with Python 3. Use `predict_delta_linf9_xgb.py`, which runs it with the MGLTools Python. |
| `msms executable not found` | The `dlinf9` environment was not created from `environment.yml`, or pass `--msms`. |
| `SASA failed` | MSMS could not compute the surface. Check that `msms` runs. |
| `ValueError: could not convert string to float: 'None'` | smina was not found or not executable (`chmod +x`, A3). |
| `TypeError: predict() got an unexpected keyword argument 'ntree_limit'` | xgboost ≥ 2 is installed. `pip install xgboost==1.2.0`. |

## Uninstall

```bash
conda env remove -n dlinf9
conda env remove -n mgltools
rm -rf "$SF/delta_LinF9_XGB"
```

---

*Prepared for CombiLabHUB (combi-lab). Tested on 21/10/2026 on Linux with the two environments above (Python 3.8, RDKit 2020.09.5, Open Babel 3.1.1, xgboost 1.2.0, mdtraj 1.10.0, MSMS 2.6.1, MGLTools 1.5.7): both checks pass. The Docker image uses the same environment files; build it and run step B2 to confirm.*
