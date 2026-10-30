# ΔVinaRF20 (DeltaVinaRF20) — Installation guide (inference only)

**ΔVinaRF20** corrects the AutoDock Vina score with a **Random Forest** (R package `randomForest`) on **20 features**: 10 Vina interaction terms computed with **vina4dv** (a version of Vina 1.1.2 that prints 58 terms) and the **buried solvent-accessible surface** of the complex by pharmacophore type (P, N, DA, D, A, AR, H, PL, HA and total; MSMS). pKd = Vina score in pKd units + RF correction. It was the best scoring function of CASF-2016 in scoring power.

| | |
|---|---|
| Authors | C. Wang, Y. Zhang (NYU) — *J. Comput. Chem.* 2017, 38, 169–177, <https://doi.org/10.1002/jcc.24667> |
| Code | <https://github.com/chengwang88/deltavina>, pinned commit `612bbe7f8b854a583ab81f4f1357422b0c108c98` (licence MIT). Identical to `deltavina.zip` in `SOFTWARE SF\Funciones_Score_Su2018` (same MD5 for the model, the feature code and the example) |
| Trained model | `deltavina/models/rffit.rda` in the repository, MD5 `944e70f5ded661296aa29f1470e372cc` |
| Vina terms | vina4dv <https://github.com/chengwang88/vina4dv>, commit `d8e4cd1b350200bf0e622721fd41102a4dbb5f5a`, compiled from source in the Docker image (as in the RFL-Score image) |
| Hardware | CPU; about 2 s per complex |
| Reported CASF-2016 PCC | 0.816 (Su et al. 2019, best of CASF-2016) |
| Origin | **Lista 1**, scoring functions of Su et al. 2019 (CASF-2016), folder `Funciones_Score_Su2018` |

Files in this folder:

| File | Purpose |
|---|---|
| `environment.yml` | Light environment `deltavinarf20_win` (Windows / Linux): Python 3.10 + R 4.3.3 + randomForest 4.7-1.2, runs the model on a features table |
| `environment_pipeline.yml`, `environment_mgltools.yml` | Full pipeline (Linux, used by the Docker image): Python 2.7 + Open Babel 2.4.1 + pandas + MSMS 2.6.1 + R 4.0.3 + randomForest 4.6-14; MGLTools 1.5.7 |
| `Dockerfile` | Self-contained image with the whole pipeline |
| `predict_deltavinarf20.py` | Mode A: predicts from a features CSV (any OS). Mode B: computes the features of a folder of complexes with the authors' code and predicts (Linux / Docker) |
| `test_1a30.py` | Installation test with complex **1a30** |
| `features_1a30.csv` | The 21 inputs of 1a30 (Vina score + F1–F20) computed with the full pipeline, for the Windows test |
| `pdb_to_xyzr.py` | Python version of MSMS's `pdb_to_xyzr` (same file as in the delta_LinF9_XGB plugin) |
| `demo_deltavinarf20.bat` | One-click Windows demo (model check) |
| `docker_deltavinarf20.bat` / `.sh` | Builds the image and runs the full test with Docker |

> **What to know before using ΔVinaRF20**
>
> 1. **The features need Linux.** The authors' code is **Python 2** (`print` statements, `pybel` of Open Babel 2) and calls MGLTools (`prepare_receptor4.py`, `prepare_ligand4.py` with `-U nphs`), vina4dv and MSMS (`pdb_to_xyzr`, `msms`) through shell commands. On Windows use the Docker image. The trained model itself only needs R, so the Windows conda test checks the model on stored features.
> 2. **No change to the authors' files.** `predict_deltavinarf20.py` calls their functions (`featureVina.vina`, `featureSASA.sasa`) and applies their model with the formula of their `DVRF20.R` (`predict(rffit, newdata = df[3:22]) + df$vina`). It only runs each complex in a temporary folder (their code writes `*.tmp` files and a `tmp/` folder in the current directory, and `prepare_ligand4.py` only finds the ligand when it runs in the ligand's folder), and it gives MSMS a `pdb_to_xyzr` with the `atmtypenumbers` table of MSMS 2.6.1 (the conda MSMS package has neither; the table is downloaded from the delta_LinF9_XGB repository, same group, MD5 `85e40580c9e77d4584e860b6f01a6e51`).
> 3. **Input.** One sub-folder per complex with `<code>_protein.pdb` (full protein) and `<code>_ligand.mol2`, the CASF-2016 / PDBbind files as they are. The authors' example uses files they processed first (`1a42_protein_proc_se.pdb`, `1a42_ligand_fix.mol2`); CASF-2016 ran ΔVinaRF20 on its own files, and so does this plugin.
> 4. **Rounding.** The authors' script rounds to 2 decimals, and so does CASF-2016. The CSV has the value before rounding (`pKd_predicted`), the rounded one (`pKd_rounded`) and the Vina part (`vina_pKd` = −0.73349 × Vina score in kcal/mol).
> 5. **Reference values.**
>    - **1a30**: the full pipeline gives **4.7758 → 4.78**, the value of CASF-2016 (`power_scoring\examples\deltaVinaRF20.dat`). Vina part 3.6665 (= −0.73349 × −4.99866, the CASF-2016 Vina score). Experimental pKd 4.30.
>    - **Authors' example (1a42)**: their features (`examples/input.csv`) give **7.55**, as their `examples/output.csv`, with R 4.0.3 + randomForest 4.6-14 and with R 4.3.3 + randomForest 4.7-1.2.
>    - Recomputing the features of 1a42 from their processed files gives the same 10 Vina terms but moves 7.38 Å² of buried surface from type D (donor) to AR (aromatic), so the prediction is 7.60 instead of 7.55: the pharmacophore types come from Open Babel's atom types, and Open Babel 2.4.1 (the only Open Babel 2 for Python 2.7 in conda-forge) types one atom of 1a42 differently from the version the authors used in 2016. 1a30 is not affected (it reproduces CASF-2016).

---

## Quick demo (Windows, one click)

Double-click `demo_deltavinarf20.bat`. It activates Miniconda, creates the `deltavinarf20_win` environment (R + randomForest, a few minutes), downloads the deltavina code at the pinned commit into `%SF%\deltavina` and runs `test_1a30.py` (checks [1], [2] and [3b] with the stored features of 1a30). The window must end with `RESULT: PASS`.

For the full pipeline on Windows, double-click `docker_deltavinarf20.bat` (Docker Desktop must be running; the first build takes several minutes). It computes the features of 1a30 from the CASF-2016 files (check [3a]).

---

## A. Installation with Miniconda (Windows) — model on a features table

Open an **Anaconda Prompt (miniconda3)**.

```bat
set PLUGIN=C:\Users\Admin\Desktop\PROYECTO_UNIVERSIDAD\combi_lab_hub_tmp\plugins\deltavinarf20
set SF=C:\Users\Admin\Desktop\PROYECTO_UNIVERSIDAD\sf
set CASF=C:\Users\Admin\Desktop\SOFTWARE SF\CASF-2016\CASF-2016
conda env create -f "%PLUGIN%\environment.yml"
conda activate deltavinarf20_win
```

Get the code (it includes the model):

```bat
curl -L -o "%SF%\deltavina.zip" https://github.com/chengwang88/deltavina/archive/612bbe7f8b854a583ab81f4f1357422b0c108c98.zip
tar -xf "%SF%\deltavina.zip" -C "%SF%"
ren "%SF%\deltavina-612bbe7f8b854a583ab81f4f1357422b0c108c98" deltavina
```

(or unzip `SOFTWARE SF\Funciones_Score_Su2018\deltavina.zip` and rename `deltavina-master` to `deltavina`: same files.)

Test:

```bat
python "%PLUGIN%\test_1a30.py" --dv-dir "%SF%\deltavina" --complex "%CASF%\coreset\1a30"
```

Expected end of the output:

```
[3b] pKd of 1a30: 4.7758 -> 4.78 (Vina part 3.6665)
     CASF-2016 reference 4.78, CombiLabHUB 4.7758
     PASS
RESULT: PASS
```

Predict from a features table (columns `pdb, vina, F1..F20`, as the authors' `input.csv`):

```bat
python "%PLUGIN%\predict_deltavinarf20.py" --dv-dir "%SF%\deltavina" --features features.csv -o predictions_dvrf20.csv
```

---

## B. Docker (Windows with Docker Desktop, or Linux) — full pipeline

```bat
cd /d "%PLUGIN%"
docker build -t combilab/deltavinarf20:1.0 .
docker run --rm -v "%CASF%\coreset\1a30:/complex:ro" combilab/deltavinarf20:1.0 python /opt/deltavinarf20/test_1a30.py --dv-dir /opt/deltavina --complex /complex
```

`docker_deltavinarf20.bat` (Windows) and `docker_deltavinarf20.sh` (Linux) do the same.

To score a folder of complexes (one sub-folder per complex):

```bat
docker run --rm -v "<folder of complexes>:/complexes:ro" -v "%CD%:/data" combilab/deltavinarf20:1.0 python /opt/deltavinarf20/predict_deltavinarf20.py --dv-dir /opt/deltavina -d /complexes -o /data/predictions_dvrf20.csv
```

It writes `predictions_dvrf20.csv` and the features in `predictions_dvrf20_features.csv`.

---

## Test record

| Date | Where | Mode | 1a30 | Result |
|---|---|---|---|---|
| 30/10/2026 | Linux (development), Python 2.7 pipeline + R 4.0.3 | full | 4.7758 → 4.78 (= CASF-2016) | PASS |
| 30/10/2026 | Linux (development), Python 3.10 + R 4.3.3 (Windows environment) | model on stored features | 4.7758 → 4.78 | PASS |
| — | Lab PC, Windows conda | model | | pending |
| — | Lab PC, Docker | full | | pending |
