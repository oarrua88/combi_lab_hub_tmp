# OnionNet-2 — Installation guide (inference only)

**OnionNet-2** predicts protein–ligand binding affinity (pKd) with a convolutional neural network. For every ligand atom it finds the closest atom of each protein residue and counts residue–atom contacts in 62 concentric distance shells. Residues fall into 21 types and ligand atoms into 8 element types, so each complex gives 62 × 21 × 8 = 10,416 features, reshaped to an 84 × 124 image. The model was trained on PDBbind v2019.

| | |
|---|---|
| Paper | Wang Z. *et al.* (2021) "OnionNet-2: A Convolutional Neural Network Model for Predicting Protein-Ligand Binding Affinity based on Residue-Atom Contacting Shells", *Frontiers in Chemistry* 9, 753002 — [doi:10.3389/fchem.2021.753002](https://doi.org/10.3389/fchem.2021.753002) |
| Code | <https://github.com/zchwang/OnionNet-2> (GPL-3.0), pinned commit `79e84dd2683d9cb307d3775fa6b4f2e4531486ce` |
| Trained model | `62shell_saved-model.h5`, 885 MB, Zenodo [record 10728089](https://zenodo.org/records/10728089), MD5 `52eb7563a867b5ee22f505070922cc6c` |
| Scaler | `models/train_scaler.scaler`, included in the repository |
| Hardware | CPU is enough (TensorFlow CPU build). Prediction needs about 2 GB of free RAM |
| Reported CASF-2016 PCC | 0.864 (paper); 0.851 reproduced by Eaves *et al.* (2026) |

Files in this folder:

| File | Purpose |
|---|---|
| `environment.yml` | Python 3.8 + Open Babel from conda-forge; TensorFlow 2.3 CPU and the README versions from pip |
| `Dockerfile` | Self-contained image: code, environment and model |
| `predict_onionnet2.py` | Batch prediction: reuses the authors' feature code, converts ligands with Open Babel, loads the model once |
| `test_1a30.py` | Installation test with complex **1a30** |
| `reference/1a30_features_nonzero.csv` | Our non-zero 1a30 features (CASF-2016 files), used by the test |
| `demo_onionnet2.bat` | One-click Windows demo |

> **What to know before using OnionNet-2**
>
> 1. **The ligand must be a `.pdb` file.** CASF-2016 and PDBbind give ligands as `.mol2`/`.sdf`, and the authors' README says to convert them with Open Babel. `predict_onionnet2.py` does that automatically, so you can point it at CASF-2016 folders as they are.
> 2. **Waters change the prediction.** The parser reads `HETATM` lines of the protein file, so crystallographic waters count as "OTH" residues. PDBbind protein files, which the authors used, contain waters. CASF-2016 `coreset` protein files do not. For 1a30, the authors' sample files (with waters) give pKd **5.4568**, and the CASF-2016 files give **5.8866**. To compare with the paper, use the PDBbind version of the protein files. Keep this in mind when computing the PCC on CASF-2016.
> 3. **Old TensorFlow.** The model was saved with TensorFlow 2.3 (Keras HDF5). Newer TensorFlow/Keras 3 versions may not load it. TensorFlow 2.3 needs Python 3.8 or older, h5py 2.10 and protobuf 3.x.

---

## Quick demo (Windows, one click)

Double-click `demo_onionnet2.bat` in this folder. It does the following:

1. Activates Miniconda.
2. Creates the `onionnet2` environment if it does not exist. This takes several minutes, because TensorFlow is a large download.
3. Unzips the OnionNet-2 code from `Funciones_Score_Tabla1\OnionNet-2.zip`.
4. Downloads the 885 MB model from Zenodo and prints its MD5.
5. Runs `test_1a30.py`.

The window stays open at the end so you can read the result (`RESULT: PASS`).

The default paths match our lab computer. On another computer, set `SF`, `CASF`, `ZIP` or `CONDA` in the Anaconda Prompt and run the script from there.

---

## A. Installation with Miniconda (Windows)

Requirements: Miniconda installed (`C:\Users\Admin\miniconda3`), about 3 GB of free disk space and 2 GB of free RAM.

All commands go in the **Anaconda Prompt (miniconda3)**.

### A1. Define the folders

```bat
set PLUGIN=C:\Users\Admin\Desktop\PROYECTO_UNIVERSIDAD\combi_lab_hub_tmp\plugins\onionnet2
set SF=C:\Users\Admin\Desktop\PROYECTO_UNIVERSIDAD\sf
set CASF=C:\Users\Admin\Desktop\SOFTWARE SF\CASF-2016\CASF-2016
mkdir "%SF%"
```

> `set` only lasts for the current window. If you open a new Anaconda Prompt, run the three `set` lines again.

### A2. Create the conda environment

```bat
conda env create -f "%PLUGIN%\environment.yml"
conda activate onionnet2
set TF_CPP_MIN_LOG_LEVEL=2
python -c "import tensorflow as tf, sklearn, numpy; print('tensorflow', tf.__version__, '| sklearn', sklearn.__version__, '| numpy', numpy.__version__)"
obabel -V
```

Expected output: `tensorflow 2.3.4 | sklearn 0.22.1 | numpy 1.18.5`, and `Open Babel 3.1.1`. Keep scikit-learn 0.22.1, because the scaler was saved with that version.

`TF_CPP_MIN_LOG_LEVEL=2` only hides TensorFlow's informational messages.

### A3. Get the OnionNet-2 code (pinned commit)

**Option 1, with Git:**

```bat
set GIT_LFS_SKIP_SMUDGE=1
git clone https://github.com/zchwang/OnionNet-2.git "%SF%\OnionNet-2"
git -C "%SF%\OnionNet-2" checkout 79e84dd2683d9cb307d3775fa6b4f2e4531486ce
```

**Option 2, without Git:** unzip `SOFTWARE SF\Funciones_Score_Tabla1\OnionNet-2.zip`. Its content is identical to that commit. Rename the folder `OnionNet-2-HEAD` to `OnionNet-2` and move it into `%SF%`.

The repository does not include the model, only `models/train_scaler.scaler`.

### A4. Download the trained model

1. Open <https://zenodo.org/records/10728089> and download `62shell_saved-model.h5` (885 MB).
2. Move it to `%SF%\OnionNet-2\models\62shell_saved-model.h5`.
3. Check that the download is not corrupted:

```bat
certutil -hashfile "%SF%\OnionNet-2\models\62shell_saved-model.h5" MD5
```

It must print `52eb7563a867b5ee22f505070922cc6c`.

### A5. Run the installation test (complex 1a30)

```bat
conda activate onionnet2
python "%PLUGIN%\test_1a30.py" --on-dir "%SF%\OnionNet-2" --complex "%CASF%\coreset\1a30" --model "%SF%\OnionNet-2\models\62shell_saved-model.h5"
```

Expected result (about 20 seconds, most of it loading the model):

```
[1] Features: 2419 non-zero (reference 2419), max difference 0.0000
    PASS - identical to the CombiLabHUB reference

[2a] Authors' sample 1a30 (with waters): pKd 5.4568 (reference 5.4568, experimental 4.30)
    PASS - matches the reference

[2b] CASF-2016 1a30 (no waters)       : pKd 5.8866 (reference 5.8866, experimental 4.30)
    PASS - matches the reference

RESULT: PASS
```

What each check verifies:
- `[1]` Open Babel converts the CASF-2016 ligand and the features are computed exactly as in our reference.
- `[2a]` Uses the sample complex shipped by the authors. It gives the same pKd as their own `scoring/predict.py`, which checks the model, the scaler and TensorFlow.
- `[2b]` The same check on the CASF-2016 files.

The difference between `[2a]` and `[2b]` comes from the waters (see note 2 above). Complex 1a30 is over-predicted, as it is by ET-Score and GB-Score, so a pKd around 5.5–5.9 against the experimental 4.30 is the **expected** behaviour.

TensorFlow may print warnings such as `Allocation of 441600000 exceeds 10% of free system memory`. They are harmless.

> Without the model you can still run the test (omit `--model`). Then only the features are checked.

### A6. Use OnionNet-2 on your own complexes

Put each complex in its own folder, with `<code>_protein.pdb` and the ligand as `<code>_ligand.pdb`, `.mol2` or `.sdf`. Hydrogens are ignored for the protein and kept for the ligand. CASF-2016 folders work as they are, because the extra `_pocket.pdb` and `_ligand_opt.mol2` files are ignored.

```bat
python "%PLUGIN%\predict_onionnet2.py" --on-dir "%SF%\OnionNet-2" -d "%CASF%\coreset" -m "%SF%\OnionNet-2\models\62shell_saved-model.h5" -o "%SF%\results_onionnet2\predictions.csv"
```

The output `predictions.csv` has one row per complex (`pdbid`, `pKd_predicted`).

The authors' single-complex script also works:

```bat
cd /d "%SF%\OnionNet-2\scoring"
python predict.py -rec_fpath ..\samples\1a30\1a30_protein.pdb -lig_fpath ..\samples\1a30\1a30_ligand.pdb -shape 84,124,1 -scaler ..\models\train_scaler.scaler -model ..\models\62shell_saved-model.h5 -shells 62 -out_fpath 1a30_pred.csv
```

It writes `1a30_pred.csv` with `pred_pKd = 5.457`.

---

## B. Installation with Docker (alternative)

Requirements: Docker Desktop with the WSL2 backend, and internet access during the build (GitHub, Debian mirrors, conda-forge, PyPI and Zenodo). The image includes the code, the environment and the verified model, so steps A2–A4 are not needed.

### B1. Build the image

```bat
cd /d C:\Users\Admin\Desktop\PROYECTO_UNIVERSIDAD\combi_lab_hub_tmp\plugins\onionnet2
docker build -t combilab/onionnet2:1.0 .
```

The build fails on purpose if the model's MD5 does not match.

### B2. Run the installation test

```bat
docker run --rm -v "C:\Users\Admin\Desktop\SOFTWARE SF\CASF-2016\CASF-2016\coreset\1a30:/complex:ro" combilab/onionnet2:1.0 python /opt/onionnet2/test_1a30.py --on-dir /opt/OnionNet-2 --complex /complex --model /opt/OnionNet-2/models/62shell_saved-model.h5
```

The expected result is the same as in A5 (`RESULT: PASS`).

### B3. Predict a set of complexes

```bat
docker run --rm -v "%CASF%\coreset:/input:ro" -v "%SF%\results_onionnet2:/data" combilab/onionnet2:1.0 python /opt/onionnet2/predict_onionnet2.py --on-dir /opt/OnionNet-2 -d /input -m /opt/OnionNet-2/models/62shell_saved-model.h5 -o /data/predictions.csv
```

---

## Troubleshooting

| Symptom | Cause and fix |
|---|---|
| `ValueError: Unknown loss function: PCC_RMSE` or other errors loading the `.h5` | Wrong TensorFlow version. Run `conda activate onionnet2` and check that A2 prints `tensorflow 2.3.4`. |
| `TypeError: Descriptors cannot be created directly` | protobuf is too new. Run `pip install protobuf==3.20.3`. |
| `ModuleNotFoundError: No module named 'openbabel'` | Open Babel is missing. Run `conda install -c conda-forge openbabel=3.1.1` in the environment. |
| Predictions differ from the reference in `[2b]` but `[2a]` passes | The protein file is not the CASF-2016 one (for example, a PDBbind file with waters). See note 2. |
| `certutil` MD5 differs | The download is incomplete. Download the model again. |
| `MemoryError` / the computer slows down | The model needs about 2 GB of free RAM. Close other programs. |

## Uninstall

```bat
conda env remove -n onionnet2
rmdir /s /q "%SF%\OnionNet-2"
docker rmi combilab/onionnet2:1.0
```

The last line is only needed if you used Docker.

---
*Prepared for CombiLabHUB (combi-lab). Tested on 19/10/2026 on Linux with Python 3.8, TensorFlow 2.3.4 (CPU), scikit-learn 0.22.1 and Open Babel 3.1.1, using the real model: all three checks above pass. All Windows packages were checked to exist for Python 3.8. On Windows, run step A5, or the demo, to confirm.*
