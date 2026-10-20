# ET-Score — Installation guide (inference only)

**ET-Score** predicts protein–ligand binding affinity (pKd) with an Extra Trees model trained on PDBbind v2016 (refined set minus core set). It uses distance-weighted protein–ligand atom-pair contacts (12 Å cutoff), grouped by four amino-acid classes, for 180 features in total.

| | |
|---|---|
| Paper | Rayka M. *et al.* (2021) *Molecular Informatics* 40, 2060084 — [doi:10.1002/minf.202060084](https://doi.org/10.1002/minf.202060084) |
| Code | <https://github.com/miladrayka/ET_Score> (GPL-3.0), pinned commit `593b018f621a42b98b7dffd37931cb1c25257de7` |
| Trained model | `et_score.sav`, 150 MB, Figshare [10.6084/m9.figshare.23684538](https://figshare.com/articles/software/ET-Score/23684538) (CC BY 4.0), MD5 `c7c5865d085fee31ed6e978c9b66c39e` |
| Hardware | CPU only (no GPU needed) |
| Reported CASF-2016 PCC | 0.827 (paper); 0.793 with the exact environment, according to the authors' README |

Files in this folder:

| File | Purpose |
|---|---|
| `environment.yml` | Exact package versions published by the authors (`Files.7z`) |
| `Dockerfile` | Self-contained image: code, environment and model |
| `test_1a30.py` | Installation test on CASF-2016 complex **1a30** |
| `reference/1a30_features.csv` | The authors' feature vector for 1a30, used by the test |
| `prepare_casf.py` | Copies CASF-2016 complexes into the layout ET-Score expects |
| `patch_glob.py` | Linux path fix, used only by the Dockerfile |
| `demo_et_score.bat` | One-click Windows demo: runs steps A2–A5 and shows the 1a30 result |

> **Why exact versions matter:** Eaves *et al.* (2026, *J. Chem. Inf. Model.*) obtained PCC 0.385 and divide-by-zero errors when they used newer packages. Keep Python 3.7 and scikit-learn 0.22.2, because the model was pickled with that version.

---

## Quick demo (Windows, one click)

Double-click `demo_et_score.bat` in this folder. It activates Miniconda, creates the `et-score` environment if it does not exist, unzips the ET-Score code from `Funciones_Score_Tabla1\ET-Score.zip`, downloads `et_score.sav` from Figshare, prints its MD5 and runs `test_1a30.py`. The window stays open at the end so you can read the result (`RESULT: PASS`).

The default paths match our lab computer. On another computer, set `SF`, `CASF`, `ZIP` or `CONDA` in the Anaconda Prompt before running the script from there. The steps below explain what the demo does, one by one.

---

## A. Installation with Miniconda (Windows)

Requirements: Miniconda installed (`C:\Users\Admin\miniconda3`) and about 1.5 GB of free disk space.

The paths below match our lab computer, so adjust them if yours differ. All commands go in the **Anaconda Prompt (miniconda3)**, which you can find in the Start menu.

### A1. Define the folders

```bat
set PLUGIN=C:\Users\Admin\Desktop\PROYECTO_UNIVERSIDAD\combi_lab_hub_tmp\plugins\et_score
set SF=C:\Users\Admin\Desktop\PROYECTO_UNIVERSIDAD\sf
set CASF=C:\Users\Admin\Desktop\SOFTWARE SF\CASF-2016\CASF-2016
mkdir "%SF%"
```

`PLUGIN` is this folder in the repository. `SF` holds the third-party code and model, which stay out of the repository. `CASF` is the CASF-2016 benchmark.

> `set` only lasts for the current window. If you open a new Anaconda Prompt, run the three `set` lines again.

### A2. Create the conda environment

```bat
conda env create -f "%PLUGIN%\environment.yml"
conda activate et-score
python -c "import sklearn, pandas, numpy, biopandas; print('sklearn', sklearn.__version__, '| pandas', pandas.__version__, '| numpy', numpy.__version__)"
```

Expected output: `sklearn 0.22.2.post1 | pandas 1.3.5 | numpy 1.21.6`. The download is about 185 MB and takes a few minutes.

### A3. Get the ET-Score code (pinned commit)

**Option 1, with Git:**

```bat
git clone https://github.com/miladrayka/ET_Score.git "%SF%\ET_Score"
git -C "%SF%\ET_Score" checkout 593b018f621a42b98b7dffd37931cb1c25257de7
```

**Option 2, without Git:** unzip `SOFTWARE SF\Funciones_Score_Tabla1\ET-Score.zip`. Its content is identical to that commit. Rename the folder `ET_Score-HEAD` to `ET_Score` and move it into `%SF%`.

### A4. Download the trained model

1. Open <https://figshare.com/articles/software/ET-Score/23684538> and click **Download**. You get `et_score.sav`, 150 MB.
2. Move it to `%SF%\ET_Score\et_score.sav`.
3. Check that the download is not corrupted:

```bat
certutil -hashfile "%SF%\ET_Score\et_score.sav" MD5
```

It must print `c7c5865d085fee31ed6e978c9b66c39e`.

### A5. Run the installation test (complex 1a30)

```bat
conda activate et-score
python "%PLUGIN%\test_1a30.py" --et-dir "%SF%\ET_Score" --complex "%CASF%\coreset\1a30" --model "%SF%\ET_Score\et_score.sav"
```

Expected result (it takes a few seconds):

```
[1] Features: 68 non-zero (reference 68), max difference 0.0000
    PASS - identical to the authors' features

[2] Predicted pKd 1a30: 5.6837 (reference 5.6837, experimental 4.30)
    PASS - matches the authors' prediction

RESULT: PASS
```

Check `[1]` verifies that feature generation on your machine reproduces the authors' published features exactly. Check `[2]` verifies that the model loads and predicts like the authors' own run. Complex 1a30 (HIV-1 protease, Ki = 50 µM) is over-predicted by ET-Score, so a pKd of 5.68 against the experimental 4.30 is the **expected** behaviour, not an installation error.

> Without the model you can still run the test (omit `--model`). Then only the features are checked.

### A6. Use ET-Score on your own complexes

ET-Score needs **one folder per complex** with **exactly one** ligand `.mol2` and **one** protein `.pdb`. Hydrogens must be present in both files. CASF-2016/PDBbind files already include them.

```
my_complexes\
   1a30\1a30_ligand.mol2
   1a30\1a30_protein.pdb
   1bcu\...
```

> ⚠️ ET-Score takes the *first* `.mol2`/`.pdb` it finds. The CASF-2016 folders also contain `_ligand_opt.mol2` and `_pocket.pdb`, so **do not point ET-Score at `coreset` directly**. Prepare a clean copy first:

```bat
python "%PLUGIN%\prepare_casf.py" "%CASF%\coreset" "%SF%\coreset_et"
cd /d "%SF%"
python "%SF%\ET_Score\predict.py" -m "%SF%\ET_Score\et_score.sav" -d coreset_et
```

The command writes two files to the current folder:
- `features.xlsx`: the features of every complex.
- `prediction.xlsx`: the predicted pKd of every complex.

---

## B. Installation with Docker (alternative)

Requirements: Docker Desktop with the WSL2 backend, and internet access during the build (GitHub, Debian mirrors, conda-forge and Figshare). The image includes the code, the environment and the verified model, so steps A2–A4 are not needed.

### B1. Build the image

```bat
cd /d C:\Users\Admin\Desktop\PROYECTO_UNIVERSIDAD\combi_lab_hub_tmp\plugins\et_score
docker build -t combilab/et-score:1.0 .
```

The build fails on purpose if the model's MD5 does not match, or if the upstream code changed and the path patch no longer applies.

### B2. Run the installation test

```bat
docker run --rm -v "C:\Users\Admin\Desktop\SOFTWARE SF\CASF-2016\CASF-2016\coreset\1a30:/complex:ro" combilab/et-score:1.0 python /opt/et_score_test/test_1a30.py --et-dir /opt/ET_Score --complex /complex --model /opt/ET_Score/et_score.sav
```

The expected result is the same as in A5 (`RESULT: PASS`).

### B3. Predict a set of complexes

Mount a folder of prepared complexes (see A6) at `/input` and an output folder at `/data`:

```bat
docker run --rm -v "%SF%\coreset_et:/input:ro" -v "%SF%\results_et:/data" combilab/et-score:1.0 python /opt/ET_Score/predict.py -m /opt/ET_Score/et_score.sav -d /input
```

`features.xlsx` and `prediction.xlsx` appear in `%SF%\results_et`.

---

## Troubleshooting

| Symptom | Cause and fix |
|---|---|
| `IndexError: list index out of range` in `generate_feature.py` | A complex folder has no `.mol2` or `.pdb`. On Linux/macOS without Docker, it is also the Windows-only path bug: run `python patch_glob.py <ET_Score>\generate_feature.py` once. |
| Predictions differ from the reference / warnings about `sklearn` versions | Wrong environment. Run `conda activate et-score` and check the versions printed in A2. |
| `conda env create` asks you to accept Anaconda Terms of Service | `environment.yml` already uses only conda-forge (`nodefaults`). Run `conda config --remove channels defaults` once and retry. |
| `certutil` MD5 differs | The download is incomplete. Download `et_score.sav` again. |
| `PermissionError` writing `features.xlsx` | The file is open in Excel. Close it and run again. |

## Uninstall

```bat
conda env remove -n et-score
rmdir /s /q "%SF%\ET_Score"
docker rmi combilab/et-score:1.0
```

The last line is only needed if you used Docker.

---
*Prepared for CombiLabHUB (combi-lab). Tested on 19/10/2026 on Linux with the exact environment: the 1a30 features match the authors' reference exactly. On Windows, run step A5 to confirm the prediction with the real model.*
