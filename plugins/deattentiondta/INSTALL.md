# DEAttentionDTA — Installation guide (inference only)

**DEAttentionDTA** predicts protein–ligand binding affinity from **sequences only**: the protein amino-acid sequence, the positions of the binding-pocket residues inside that sequence, and the ligand **SMILES**. It uses dynamic word embeddings, 1D convolutions and self-attention. No 3D coordinates reach the network (the 3D files are only used to extract the sequence and the pocket). The prediction is the **average of 10 cross-validation models** (Fold 1–10).

| | |
|---|---|
| Authors | whatamazing1 group (contact yjiny@126.com) — see the repository for the paper reference |
| Code | <https://github.com/whatamazing1/DEAttentionDTA>, pinned commit `6a9618c0e93b2224797ab0067119be3d73e81a98` (licence MIT) |
| Trained models | `src/model/Fold 1..10 best_model.ckpt`, 89 MB in total, **included in the repository** (MD5s in the table below) |
| Pre-processed CASF-2016 core set | `data/seq_data_core.csv`, **included in the repository** (SMILES, sequence, pocket and positions of the 285 complexes) |
| Hardware | CPU is enough |
| Reported CASF-2016 PCC | 0.845 (paper). Eaves et al. 2026 reproduce 0.819. Our run on the authors' pre-processed data reproduces the authors' own `src/kfold_result.csv` (278 complexes, PCC 0.853). |

The repository has two versions: `src/` (version 1, **with** active-site information, the one evaluated on CASF-2016) and `src-v2/` (without it). This plugin uses `src/`.

| Model file | MD5 |
|---|---|
| `Fold 1 best_model.ckpt` | `7c9ce530d8d8858752668d827bc31027` |
| `Fold 2 best_model.ckpt` | `122ad4a28ea09cf3f6168aa0c9461908` |
| `Fold 3 best_model.ckpt` | `f446cbfcc6d88bfac09a41c7a56c8bc2` |
| `Fold 4 best_model.ckpt` | `895f192e69d9df518197cd916d8a9ea5` |
| `Fold 5 best_model.ckpt` | `2bf1dbe1567c84bd8b3663261b167e19` |
| `Fold 6 best_model.ckpt` | `0fb0d10c3be693479ee5fab97f577d34` |
| `Fold 7 best_model.ckpt` | `7cdc46d7df1026fe526b4002a4c29ca2` |
| `Fold 8 best_model.ckpt` | `13454ecee193d90834fa086e0873c8ac` |
| `Fold 9 best_model.ckpt` | `870c9d79f9fc0e67e845987cb369ca10` |
| `Fold 10 best_model.ckpt` | `c9df6afe748c2314b077f38132ae2bb5` |

Files in this folder:

| File | Purpose |
|---|---|
| `environment.yml` | Python 3.10 + PyTorch 2.2.2 + Open Babel 3.1.1 (checked for Windows) |
| `Dockerfile` | Self-contained image (conda-forge CPU PyTorch 2.3.1 + Open Babel) |
| `predict_deattentiondta.py` | Builds the inputs from a folder of complexes and scores them with the 10 fold models |
| `test_1a30.py` | Installation test with complex **1a30** |
| `demo_deattentiondta.bat` | One-click Windows demo |

> **What to know before using DEAttentionDTA**
>
> 1. **The authors' `test.py` only reads their own CSV files.** To score new complexes you need the SMILES, the protein sequence and the pocket positions. `predict_deattentiondta.py` builds them from `<code>_ligand.mol2`, `<code>_protein.pdb` and `<code>_pocket.pdb`, the same way as the authors' `pre-code/` scripts (SMILES with Open Babel).
> 2. **CASF-2016 pocket files have no chain IDs.** In multi-chain proteins (1a30 is the HIV-1 protease dimer) the same residue number appears in each chain. The authors' original parser assumes a chain column and fails; the fix by Eaves et al. maps every pocket residue to the *last* chain with that number. Our wrapper matches each pocket residue to the protein residue with the same number and name, in file order (chain A first, then chain B). For 1a30 this gives the same positions as the authors for all 51 CASF pocket residues.
> 3. **The CASF-2016 pocket is a bit different from the authors' pocket.** The authors took their pockets from PDBbind v2020; for 1a30 theirs has 56 residues and the CASF-2016 file 51. SMILES and protein sequence are identical. That is why our test shows two values: 6.3185 with the authors' inputs and 6.2026 with the CASF-2016 files.
> 4. **Fixed lengths.** Sequences longer than 1024 residues and SMILES longer than 256 characters are truncated by the model (the output CSV says so in `note`). A SMILES character outside the model's vocabulary (e.g. a rare element) makes the complex fail; the wrapper skips it and prints the reason.
> 5. The authors' predictions in `src/kfold_result.csv` cover 278 of the 285 core-set complexes (`1nc1`, `1nc3`, `1ps3`, `3lka`, `3myg`, `4jsz`, `4tmn` are missing). Our wrapper scores all of them.

---

## Quick demo (Windows, one click)

Double-click `demo_deattentiondta.bat` in this folder. It does the following:

1. Activates Miniconda.
2. Creates the `deattentiondta` environment if it does not exist. This takes several minutes, because PyTorch is a large download.
3. Unzips the DEAttentionDTA code and models from `Funciones_Score_Tabla1\DEAttentionDTA.zip`.
4. Checks the MD5 of `Fold 1 best_model.ckpt`.
5. Runs `test_1a30.py`.

The window stays open at the end so you can read the result (`RESULT: PASS`).

The default paths match our lab computer. On another computer, set `SF`, `CASF`, `ZIP` or `CONDA` in the Anaconda Prompt and run the script from there.

---

## A. Installation with Miniconda (Windows)

Requirements: Miniconda installed (`C:\Users\Admin\miniconda3`) and about 2 GB of free disk space.

All commands go in the **Anaconda Prompt (miniconda3)**.

### A1. Define the folders

```bat
set PLUGIN=C:\Users\Admin\Desktop\PROYECTO_UNIVERSIDAD\combi_lab_hub_tmp\plugins\deattentiondta
set SF=C:\Users\Admin\Desktop\PROYECTO_UNIVERSIDAD\sf
set CASF=C:\Users\Admin\Desktop\SOFTWARE SF\CASF-2016\CASF-2016
mkdir "%SF%"
```

> `set` only lasts for the current window. If you open a new Anaconda Prompt, run the three `set` lines again.

### A2. Create the conda environment

```bat
conda env create -f "%PLUGIN%\environment.yml"
conda activate deattentiondta
python -c "import torch, numpy; from openbabel import pybel; print('torch', torch.__version__, '| numpy', numpy.__version__, '| openbabel', pybel.ob.OBReleaseVersion())"
```

Expected output: `torch 2.2.2+cpu | numpy 1.26.4 | openbabel 3.1.0` (the conda-forge Open Babel 3.1.1 package reports itself as 3.1.0). On Windows, the PyPI build of PyTorch is CPU-only.

### A3. Get the DEAttentionDTA code (pinned commit)

**Option 1, with Git:**

```bat
git clone https://github.com/whatamazing1/DEAttentionDTA.git "%SF%\DEAttentionDTA"
git -C "%SF%\DEAttentionDTA" checkout 6a9618c0e93b2224797ab0067119be3d73e81a98
```

**Option 2, without Git:** unzip `SOFTWARE SF\Funciones_Score_Tabla1\DEAttentionDTA.zip`. Its content is identical to that commit. Rename the folder `DEAttentionDTA-HEAD` to `DEAttentionDTA` and move it into `%SF%`.

Check one model (the others are in the MD5 table above):

```bat
certutil -hashfile "%SF%\DEAttentionDTA\src\model\Fold 1 best_model.ckpt" MD5
```

It must print `7c9ce530d8d8858752668d827bc31027`.

### A4. Run the installation test (complex 1a30)

```bat
conda activate deattentiondta
python "%PLUGIN%\test_1a30.py" --dea-dir "%SF%\DEAttentionDTA" --complex "%CASF%\coreset\1a30"
```

Expected result (a few seconds):

```
Inputs built from the CASF-2016 files:
    SMILES (Open Babel, from 1a30_ligand.mol2): same as the authors
    protein sequence (198 residues): same as the authors
    pocket residues: 51 (authors: 56)

[1] Authors' pre-processed 1a30 (data/seq_data_core.csv): pKd 6.3185 (reference 6.3185, experimental 4.30)
    PASS - matches the reference

[2] CASF-2016 1a30 (mol2 + protein.pdb + pocket.pdb): pKd 6.2026 (reference 6.2026, experimental 4.30)
    PASS - matches the reference

RESULT: PASS
```

What each check verifies:
- `[1]` Uses 1a30 exactly as the authors pre-processed it. The value equals the authors' own result in `src/kfold_result.csv` (6.3184166), which checks the 10 models and PyTorch.
- `[2]` Builds the inputs from the CASF-2016 files from PDBbind. SMILES and sequence must be identical to the authors'; the pocket differs a little (note 3 above).

Complex 1a30 is over-predicted by DEAttentionDTA too, so 6.2–6.3 against the experimental 4.30 is the **expected** behaviour.

### A5. Use DEAttentionDTA on CASF-2016 or your own complexes

**CASF-2016 core set (285 complexes):**

```bat
python "%PLUGIN%\predict_deattentiondta.py" --dea-dir "%SF%\DEAttentionDTA" -d "%CASF%\coreset" -o "%SF%\results_deattentiondta\predictions.csv"
```

The output CSV has `pdbid, pKd_predicted` (average of the 10 folds), `fold1..fold10`, `seq_len, pocket_residues, ligand_source, smiles, note`.

**Your own complexes:** put each one in its own folder with `<code>_protein.pdb`, `<code>_pocket.pdb` and `<code>_ligand.mol2` (or `<code>_ligand.smi` with the SMILES as first word).

---

## B. Installation with Docker (alternative)

Requirements: Docker Desktop with the WSL2 backend, and internet access during the build (GitHub, Debian mirrors and conda-forge). Steps A2–A3 are not needed.

### B1. Build the image

```bat
cd /d C:\Users\Admin\Desktop\PROYECTO_UNIVERSIDAD\combi_lab_hub_tmp\plugins\deattentiondta
docker build -t combilab/deattentiondta:1.0 .
```

The build fails on purpose if the MD5 of any of the 10 models does not match.

### B2. Run the installation test

```bat
docker run --rm -v "C:\Users\Admin\Desktop\SOFTWARE SF\CASF-2016\CASF-2016\coreset\1a30:/complex:ro" combilab/deattentiondta:1.0 python /opt/deattentiondta/test_1a30.py --dea-dir /opt/DEAttentionDTA --complex /complex
```

### B3. Score the CASF-2016 core set

```bat
docker run --rm -v "C:\Users\Admin\Desktop\SOFTWARE SF\CASF-2016\CASF-2016\coreset:/coreset:ro" -v "C:\Users\Admin\Desktop\PROYECTO_UNIVERSIDAD\sf\results_deattentiondta:/data" combilab/deattentiondta:1.0 python /opt/deattentiondta/predict_deattentiondta.py --dea-dir /opt/DEAttentionDTA -d /coreset -o /data/predictions.csv
```

---

## Troubleshooting

| Symptom | Cause and fix |
|---|---|
| `KeyError` on a SMILES character | The SMILES has a character outside the model's 53-symbol vocabulary. The complex cannot be scored by this model. |
| `pocket residue ... not found in the protein` | The pocket file has a residue that is not in `<code>_protein.pdb`, or the two files come from different structures. |
| `No module named 'openbabel'` | Open Babel is missing. Recreate the environment from `environment.yml` (it comes from conda-forge, not pip). |
| `KeyError: (..., ...)` with the authors' `pre-code/get_pocket.py` | That script assumes chain IDs in the pocket file. Use `predict_deattentiondta.py`. |
| Predictions differ from the reference | Different PyTorch or Open Babel version. Check A2. |

## Uninstall

```bat
conda env remove -n deattentiondta
rmdir /s /q "%SF%\DEAttentionDTA"
docker rmi combilab/deattentiondta:1.0
```

The last line is only needed if you used Docker.

---
*Prepared for CombiLabHUB (combi-lab). Tested on 20/10/2026 on Linux with Python 3.10, PyTorch 2.3.1 (CPU) and Open Babel 3.1.1: both checks above pass, and scoring the authors' pre-processed core set reproduces their `src/kfold_result.csv` for all 278 complexes (largest difference 0.0001, PCC 0.853). All Windows packages were checked to exist for Python 3.10. On Windows, run step A4, or the demo, to confirm.*
