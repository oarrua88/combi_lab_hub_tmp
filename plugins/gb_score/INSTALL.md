# GB-Score — Installation guide (inference only)

**GB-Score** predicts protein–ligand binding affinity (pKd) with a Gradient Boosting model (20,000 trees) trained on PDBbind v2019 (general + refined set minus the CASF-2016 core set). It uses distance-weighted protein–ligand contacts between 10 element types, grouped by four amino-acid classes and cut off at 12 Å. That gives 400 raw features. After the authors' preprocessing, the model uses 104 of them.

| | |
|---|---|
| Paper | Rayka M. *et al.* (2022) "GB-Score: Minimally designed machine learning scoring function based on distance-weighted interatomic contact features", *Molecular Informatics* — [doi:10.1002/minf.202200135](https://doi.org/10.1002/minf.202200135) |
| Code | <https://github.com/miladrayka/GB_Score> (AGPL-3.0), pinned commit `b543f0b24358640c6ce4505c1679788f9b01d054` |
| Trained model | `gb_score.joblib`, 620 MB, Figshare [10.6084/m9.figshare.16912150](https://figshare.com/articles/software/gb_score_joblib/16912150), MD5 `90ce46593c302792086ed402ebf93921` |
| Authors' data | `gb_score_files.rar`, 45 MB, Figshare [10.6084/m9.figshare.23684484](https://figshare.com/articles/dataset/GB-Score_Files/23684484), MD5 `e8fced617e0ff87112baa9089e815146`. Only needed to audit the preprocessing |
| Hardware | CPU only (no GPU needed). Loading the model uses about 1.5 GB of RAM |
| Reported CASF-2016 PCC | 0.862 (RMSE 1.190) in the authors' notebook |

Files in this folder:

| File | Purpose |
|---|---|
| `environment.yml` | Package versions from the GB-Score README (Python 3.8.8, scikit-learn 0.24.1) |
| `Dockerfile` | Self-contained image: code, environment and model |
| `predict_gb_score.py` | Features + preprocessing + prediction (the GB-Score repository has no prediction script) |
| `test_1a30.py` | Installation test on CASF-2016 complex **1a30** |
| `reference/1a30_features.csv` | Our 1a30 feature vector, used by the test |
| `reference/1a30_features_authors.csv` | The authors' published 1a30 features, shown for comparison |
| `reference/1a30_prediction.txt` | Reference pKd for 1a30 |
| `reference/gb_score_preprocessing.csv` | The 104 features the model uses, with the mean and std for standardization |
| `make_preprocessing.py` | Rebuilds the preprocessing table from the authors' `total_set_2019.csv` |
| `prepare_casf.py` | Copies CASF-2016 complexes into the layout GB-Score expects |
| `demo_gb_score.bat` | One-click Windows demo |

> **Two things the GB-Score repository does not tell you**
>
> 1. **The model needs preprocessed features.** The authors' notebook drops near-constant features (variance ≤ 0.01) and highly correlated features (|r| > 0.95). It then standardizes the remaining 104 with the mean and std of their whole dataset. Passing the 400 raw features gives wrong predictions, or an error. `predict_gb_score.py` applies this step with `reference/gb_score_preprocessing.csv`, which `make_preprocessing.py` computed from the authors' Figshare data.
> 2. **The public `generate_features.py` under-counts protein hydrogens.** It assigns elements with a fixed table of atom names that misses names such as HG21, HD11, HE21 and HH11. For 1a30, some H features come out at half the value in the authors' published data. Taking the element from the PDB file reproduces the published features (maximum difference 0.16 for 1a30, from slightly different PDBbind files). `predict_gb_score.py` does that, and still uses the authors' own functions for everything else.

---

## Quick demo (Windows, one click)

Double-click `demo_gb_score.bat` in this folder. It does the following:

1. Activates Miniconda.
2. Creates the `gb-score` environment if it does not exist.
3. Unzips the GB-Score code from `Funciones_Score_Tabla1\GB-Score.zip`.
4. Downloads `gb_score.joblib` to `sf\GB_Score_figshare`, unless it is already there, and prints its MD5.
5. Runs `test_1a30.py`.

The window stays open at the end so you can read the result (`RESULT: PASS`).

The default paths match our lab computer. On another computer, set `SF`, `CASF`, `ZIP` or `CONDA` in the Anaconda Prompt and run the script from there.

---

## A. Installation with Miniconda (Windows)

Requirements: Miniconda installed (`C:\Users\Admin\miniconda3`), about 2 GB of free disk space and 2 GB of free RAM.

All commands go in the **Anaconda Prompt (miniconda3)**.

### A1. Define the folders

```bat
set PLUGIN=C:\Users\Admin\Desktop\PROYECTO_UNIVERSIDAD\combi_lab_hub_tmp\plugins\gb_score
set SF=C:\Users\Admin\Desktop\PROYECTO_UNIVERSIDAD\sf
set CASF=C:\Users\Admin\Desktop\SOFTWARE SF\CASF-2016\CASF-2016
mkdir "%SF%\GB_Score_figshare"
```

> `set` only lasts for the current window. If you open a new Anaconda Prompt, run the three `set` lines again.

### A2. Create the conda environment

```bat
conda env create -f "%PLUGIN%\environment.yml"
conda activate gb-score
python -c "import sklearn, pandas, numpy; print('sklearn', sklearn.__version__, '| pandas', pandas.__version__, '| numpy', numpy.__version__)"
```

Expected output: `sklearn 0.24.1 | pandas 1.2.4 | numpy 1.21.2`. Keep scikit-learn 0.24.1, because the model was saved with that version.

### A3. Get the GB-Score code (pinned commit)

**Option 1, with Git:**

```bat
git clone https://github.com/miladrayka/GB_Score.git "%SF%\GB_Score"
git -C "%SF%\GB_Score" checkout b543f0b24358640c6ce4505c1679788f9b01d054
```

**Option 2, without Git:** unzip `SOFTWARE SF\Funciones_Score_Tabla1\GB-Score.zip`. Its content is identical to that commit. Rename the folder `GB_Score-HEAD` to `GB_Score` and move it into `%SF%`.

### A4. Download the trained model

1. Open <https://figshare.com/articles/software/gb_score_joblib/16912150> and click **Download**. You get `gb_score.joblib`, 620 MB.
2. Move it to `%SF%\GB_Score_figshare\gb_score.joblib`.
3. Check that the download is not corrupted:

```bat
certutil -hashfile "%SF%\GB_Score_figshare\gb_score.joblib" MD5
```

It must print `90ce46593c302792086ed402ebf93921`.

### A5. Run the installation test (complex 1a30)

```bat
conda activate gb-score
python "%PLUGIN%\test_1a30.py" --gb-dir "%SF%\GB_Score" --complex "%CASF%\coreset\1a30" --model "%SF%\GB_Score_figshare\gb_score.joblib"
```

Expected result (about 15 seconds, most of it loading the model):

```
[1] Features: 68 non-zero (reference 68), max difference 0.0000
    PASS - identical to the CombiLabHUB reference
    (info) max difference vs the authors' published features: 0.164

[2] Predicted pKd 1a30: 5.6171 (reference 5.6171, experimental 4.30)
    PASS - matches the reference prediction

RESULT: PASS
```

Check `[1]` verifies that feature generation on your machine reproduces our reference exactly. The info line shows that our features also match the authors' published data. Check `[2]` verifies that the model loads and predicts with the right preprocessing. With the authors' own 1a30 features, the model gives 5.6570.

Complex 1a30 (HIV-1 protease, Ki = 50 µM) is over-predicted, as it is by ET-Score. A pKd of about 5.6 against the experimental 4.30 is the **expected** behaviour, not an installation error.

> Without the model you can still run the test (omit `--model`). Then only the features are checked.

### A6. Use GB-Score on your own complexes

GB-Score needs **one folder per complex** with **exactly one** ligand `.mol2` and **one** protein `.pdb`. Hydrogens must be present in both files. CASF-2016/PDBbind files already include them.

```
my_complexes\
   1a30\1a30_ligand.mol2
   1a30\1a30_protein.pdb
   1bcu\...
```

> ⚠️ The CASF-2016 folders also contain `_ligand_opt.mol2` and `_pocket.pdb`, so **do not point GB-Score at `coreset` directly**. Prepare a clean copy first:

```bat
python "%PLUGIN%\prepare_casf.py" "%CASF%\coreset" "%SF%\coreset_gb"
python "%PLUGIN%\predict_gb_score.py" --gb-dir "%SF%\GB_Score" -d "%SF%\coreset_gb" -m "%SF%\GB_Score_figshare\gb_score.joblib" -o "%SF%\results_gb\predictions.csv"
```

The command writes two files:
- `predictions.csv`: the predicted pKd of every complex.
- `predictions_features.csv`: the 400 raw features of every complex.

The whole core set (285 complexes) takes a few minutes on a normal CPU.

---

## B. Installation with Docker (alternative)

Requirements: Docker Desktop with the WSL2 backend, and internet access during the build (GitHub, Debian mirrors, conda-forge and Figshare). The image includes the code, the environment and the verified model, so steps A2–A4 are not needed.

### B1. Build the image

```bat
cd /d C:\Users\Admin\Desktop\PROYECTO_UNIVERSIDAD\combi_lab_hub_tmp\plugins\gb_score
docker build -t combilab/gb-score:1.0 .
```

The build fails on purpose if the model's MD5 does not match.

### B2. Run the installation test

```bat
docker run --rm -v "C:\Users\Admin\Desktop\SOFTWARE SF\CASF-2016\CASF-2016\coreset\1a30:/complex:ro" combilab/gb-score:1.0 python /opt/gb_score/test_1a30.py --gb-dir /opt/GB_Score --complex /complex --model /opt/GB_Score/gb_score.joblib
```

The expected result is the same as in A5 (`RESULT: PASS`).

### B3. Predict a set of complexes

Mount a folder of prepared complexes (see A6) at `/input` and an output folder at `/data`:

```bat
docker run --rm -v "%SF%\coreset_gb:/input:ro" -v "%SF%\results_gb:/data" combilab/gb-score:1.0 python /opt/gb_score/predict_gb_score.py --gb-dir /opt/GB_Score -d /input -m /opt/GB_Score/gb_score.joblib -o /data/predictions.csv
```

`predictions.csv` and `predictions_features.csv` appear in `%SF%\results_gb`.

---

## Regenerating the preprocessing table (optional)

`reference/gb_score_preprocessing.csv` is already in the repository. To audit it, download `gb_score_files.rar` from Figshare, extract `total_set_2019.csv` and run:

```bat
python "%PLUGIN%\make_preprocessing.py" total_set_2019.csv check.csv
```

It must report `104 features kept`. That is the number of inputs the model expects (`n_features_ = 104`).

---

## Troubleshooting

| Symptom | Cause and fix |
|---|---|
| `ValueError: Number of features of the model must match the input` | Raw features were passed to the model. Use `predict_gb_score.py`, which applies the preprocessing. |
| Predictions differ from the reference / warnings about `sklearn` versions | Wrong environment. Run `conda activate gb-score` and check the versions printed in A2. |
| `MemoryError` while loading the model | The model needs about 1.5 GB of free RAM. Close other programs. |
| `conda env create` asks you to accept Anaconda Terms of Service | `environment.yml` already uses only conda-forge (`nodefaults`). Run `conda config --remove channels defaults` once and retry. |
| `certutil` MD5 differs | The download is incomplete. Download `gb_score.joblib` again. |
| `Skipping <code>: needs one .mol2 and one .pdb` | That complex folder is missing a file. Use `prepare_casf.py` for CASF-2016 folders. |

## Uninstall

```bat
conda env remove -n gb-score
rmdir /s /q "%SF%\GB_Score"
rmdir /s /q "%SF%\GB_Score_figshare"
docker rmi combilab/gb-score:1.0
```

The last line is only needed if you used Docker.

---
*Prepared for CombiLabHUB (combi-lab). Tested on 19/10/2026 on Linux with Python 3.8 and scikit-learn 0.24.1, using the real model: the 1a30 features and prediction match the references above. On Windows, run step A5, or the demo, to confirm.*
