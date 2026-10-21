# RFL-Score — Installation guide (inference only)

**RFL-Score v1** is the scoring function of our lab (combi-lab, FURG). It predicts protein–ligand binding affinity (pKd) with a **Random Forest** (R package `randomForest`) on **160 descriptors** selected with LassoCV from 723: amino-acid composition of the protein sequence, DSSP secondary structure, NNScore 2.0 / BINANA contacts (ODDT), PaDEL and RDKit 2D/3D ligand descriptors, SASA and the Vina terms of ΔVinaRF20 (vina4dv). It was trained on PDBbind 2018 (general) + CSAR and validated on CASF-2013 and CASF-2016.

| | |
|---|---|
| Authors | O. Arrua, J. Aderhold, A. V. Werhli, K. S. Machado — IEEE CIBCB 2024 |
| Code | <https://github.com/combilab-furg/rfl-score_v1>, pinned commit `2020d9039436b7c48891753a3d7aa5a97a239246` |
| Trained model | `scoring/RScript/model/scoring_function_160.rda` in the repository, MD5 `d1ad344ed3f167e2e053e97dd1f9890e` |
| Vina terms | vina4dv <https://github.com/chengwang88/vina4dv>, commit `d8e4cd1b350200bf0e622721fd41102a4dbb5f5a` (static Linux binary `build/linux/release/vina`, MD5 `6d78ba24f4b507a6edb29888f41e0d61`) |
| Hardware | CPU; about 10 s per complex for the full pipeline |
| Reported CASF-2016 PCC | to be filled in from the paper (sheet *Estado SF*) |

Files in this folder:

| File | Purpose |
|---|---|
| `environment.yml` | Light environment for Windows: Python 3.10 + R 4.3.3 + randomForest 4.7-1.2 (runs the model on a features table) |
| `environment_pipeline.yml`, `environment_mgltools.yml` | Full pipeline (Linux, used by the Docker image): Python 3.7, Open Babel 2.4.1, RDKit 2020.09.1, ODDT 0.7, Java 11, R 4.0.3 + randomForest 4.6-14; MGLTools 1.5.7 |
| `Dockerfile` | Self-contained image with the whole pipeline (DSSP, MGLTools, vina4dv, PaDEL, R) |
| `predict_rfl_score.py` | Mode A: predicts from a 160-features CSV (any OS). Mode B: computes the features of a folder of complexes with the authors' code and predicts (Linux / Docker) |
| `test_1a30.py` | Installation test with complex **1a30** |
| `demo_rfl_score.bat` | One-click Windows demo (model check) |
| `docker_rfl_score.bat` / `.sh` | Builds the image and runs the full test with Docker |

> **What to know before using RFL-Score**
>
> 1. **The features need Linux.** The descriptor pipeline calls `babel` (Open Babel 2.4), `java` (PaDEL), `dssp`, MGLTools (`prepare_receptor4.py`, `prepare_ligand4.py`), vina4dv and MSMS through shell commands. On Windows, use the Docker image. The trained model itself only needs R, so the Windows conda test checks the model on the authors' features of 1a30.
> 2. **Two small adaptations, no change to the authors' files** (applied by `predict_rfl_score.py` at run time):
>    - DSSP 4.2 no longer accepts `dssp -i in.pdb -o out.dssp` (4.0.4, the version in the README, still does). With DSSP 4 a small `dssp` wrapper is put first on `PATH` that calls `mkdssp --output-format dssp in out`.
>    - MGLTools 1.5.7's `prepare_ligand4.py` only finds the ligand when it runs in the ligand's folder; `Vina58.prepare_ligand` is replaced by the same command run from there.
>
>    With these, the 160 features computed from the CASF-2016 files of 1a30 are **identical** to the authors' `examples/1a30/1a30_160_input.csv`.
> 3. **Protein sequence (FASTA).** The amino-acid composition comes from the FASTA of the PDB entry, downloaded from RCSB (`https://www.rcsb.org/fasta/entry/<CODE>`), as the authors did. It includes chains that are not in the CASF protein file (in 1a30, the peptide inhibitor `EDL`). `predict_rfl_score.py` uses a `*.fasta*` file in the complex folder if there is one, otherwise it downloads it (**internet needed**); `--fasta-from pdb` builds it from the protein file instead, which changes the result (1a30: 4.4739 instead of 4.4494).
> 4. **Reference values for 1a30:** 4.4494 with `examples/1a30/1a30_160_input.csv` (and with our features, identical); 4.5071 with the row of 1a30 in `examples/all_160_input.csv`, computed by the authors with another version of the RDKit 3D descriptors. Experimental pKd 4.30. R prints 2 decimals (4.45); here 4 are written.
> 5. `RFL-Score.zip` in `Funciones_Score_Tabla1` is an older snapshot (July 2022, before the DSSP 4.0.4 fix). Its model and 1a30 example are identical (same MD5), so it is fine for the Windows test; the Docker image uses the pinned commit.

---

## Quick demo (Windows, one click)

Double-click `demo_rfl_score.bat`. It activates Miniconda, creates the `rfl_score` environment (R + randomForest, a few minutes), unzips `Funciones_Score_Tabla1\RFL-Score.zip` into `%SF%\rfl-score_v1` and runs `test_1a30.py` (check [1]). The window must end with `RESULT: PASS`.

For the full pipeline on Windows, double-click `docker_rfl_score.bat` (needs Docker Desktop running; the first build takes several minutes). It runs checks [1] and [2].

---

## A. Installation with Miniconda (Windows) — model on a features table

Open an **Anaconda Prompt**.

```bat
set PLUGIN=C:\Users\Admin\Desktop\PROYECTO_UNIVERSIDAD\combi_lab_hub_tmp\plugins\rfl_score
set SF=C:\Users\Admin\Desktop\PROYECTO_UNIVERSIDAD\sf
conda env create -f "%PLUGIN%\environment.yml"
conda activate rfl_score
```

Get the code: `git clone https://github.com/combilab-furg/rfl-score_v1.git "%SF%\rfl-score_v1"` and `git -C "%SF%\rfl-score_v1" checkout 2020d9039436b7c48891753a3d7aa5a97a239246`, or unzip `RFL-Score.zip` and rename `rfl-score_v1-HEAD` to `rfl-score_v1`.

```bat
certutil -hashfile "%SF%\rfl-score_v1\scoring\RScript\model\scoring_function_160.rda" MD5
python -W ignore "%PLUGIN%\test_1a30.py" --rfl-dir "%SF%\rfl-score_v1"
```

The MD5 must be `d1ad344ed3f167e2e053e97dd1f9890e`, and the test:

```
[1] Model + authors' features of 1a30: pKd 4.4494 (reference 4.4494, experimental 4.30); files: MD5 OK
    PASS

RESULT: PASS
```

To predict from any features table written by the authors' `sf160.py` (first column = id, then the 160 features):

```bat
python "%PLUGIN%\predict_rfl_score.py" --rfl-dir "%SF%\rfl-score_v1" --features my_160_input.csv -o "%SF%\results_rfl\predictions.csv"
```

---

## B. Installation with Docker — full pipeline

### B1. Build the image

```bat
cd /d "%PLUGIN%"
docker build -t combilab/rfl_score:1.0 .
```

### B2. Run the installation test

```bat
docker run --rm -v "C:\Users\Admin\Desktop\SOFTWARE SF\CASF-2016\CASF-2016\coreset\1a30:/complex:ro" combilab/rfl_score:1.0 python -W ignore /opt/rfl_score/test_1a30.py --rfl-dir /opt/rfl-score_v1 --complex /complex --full
```

Expected output (end):

```
[1] Model + authors' features of 1a30: pKd 4.4494 (reference 4.4494, experimental 4.30); files: MD5 OK
    PASS
...
[2] Full pipeline: 0 of 160 features differ from the authors' 1a30_160_input.csv; pKd 4.4494 (reference 4.4494)
    PASS

RESULT: PASS
```

### B3. Score the CASF-2016 core set (internet needed for the FASTA files)

```bat
docker run --rm -v "C:\Users\Admin\Desktop\SOFTWARE SF\CASF-2016\CASF-2016\coreset:/coreset:ro" -v "C:\Users\Admin\Desktop\PROYECTO_UNIVERSIDAD\sf\results_rfl:/data" combilab/rfl_score:1.0 python -W ignore /opt/rfl_score/predict_rfl_score.py --rfl-dir /opt/rfl-score_v1 -d /coreset -o /data/predictions.csv
```

Output: `predictions.csv` (`pdbid, pKd_predicted, fasta_source`) and `predictions_features160.csv` (the 160 features of every complex). `tools\run_coreset_level1.bat` runs this step as SF `rfl`.

---

## Troubleshooting

| Problem | Cause / fix |
|---|---|
| `Rscript not found` | Activate the `rfl_score` environment, or set `RSCRIPT` to `Rscript.exe`. |
| `there is no package called 'randomForest'` | The environment was created without `r-randomforest`; recreate it from `environment.yml`. |
| `dssp: unrecognized option '-i'` | DSSP ≥ 4.2 called directly (by `sf160.py`). Use `predict_rfl_score.py`, which adds the wrapper. |
| `prepare_ligand4.py: ligand filename ... doesn't exist` | The authors' `Vina58.prepare_ligand` run outside the ligand's folder; use `predict_rfl_score.py`. |
| `URLError` / `RCSB returned no FASTA` | No internet inside the container; put `<code>.fasta.txt` in each complex folder, or use `--fasta-from pdb`. |

## Uninstall

```bat
conda env remove -n rfl_score
docker image rm combilab/rfl_score:1.0
rmdir /s /q "%SF%\rfl-score_v1"
```

---

*Prepared for CombiLabHUB (combi-lab). Tested on 21/10/2026 on Linux: check [1] with R 4.0.3 / randomForest 4.6-14 and with R 4.3.3 / randomForest 4.7-1.2 (same 4.4494); check [2] with the `environment_pipeline.yml` versions, MGLTools 1.5.7, vina4dv `d8e4cd1` and DSSP 4.2.2 (through the wrapper): 0 of 160 features differ. The Docker image (DSSP 4.0.4 from Debian) and the Windows demo still have to be run on the lab computer.*
