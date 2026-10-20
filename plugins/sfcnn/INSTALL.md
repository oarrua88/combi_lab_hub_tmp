# Sfcnn — Installation guide (inference only)

**Sfcnn** predicts protein–ligand binding affinity (pKd) with a 3D convolutional neural network. It places the complex in a 20 × 20 × 20 Å grid (1 Å voxels) centred on the ligand and encodes each voxel with 14 atom types (element plus hybridization for C, N and S), counted separately for protein and ligand atoms. That gives a 20 × 20 × 20 × 28 tensor. The model was trained on PDBbind v2019.

| | |
|---|---|
| Paper | Wang Y. *et al.* (2022), Sfcnn: a 3D convolutional neural network scoring function for protein–ligand binding affinity prediction (corresponding author: wangyu@cqupt.edu.cn, Chongqing University of Posts and Telecommunications) |
| Code | <https://github.com/bioinfocqupt/Sfcnn> (GPL-3.0), pinned commit `30ba8f0f8d54e1860d8e4672beb5fb7920bf7b4d` |
| Trained weights | `weights_22_112-0.0083.h5`, 5.5 MB, **included in the repository**, MD5 `b1315396dfd1616b4be80fdaeff4a428` |
| Hardware | CPU only (TensorFlow CPU build) |
| Reported CASF-2016 PCC | 0.793 (paper); 0.789 reproduced by Eaves *et al.* (2026) |

Files in this folder:

| File | Purpose |
|---|---|
| `environment.yml` | Python 3.8 + Open Babel 3.1.1 from conda-forge; TensorFlow 2.3.4 CPU from pip |
| `Dockerfile` | Self-contained image: code, weights and environment |
| `predict_sfcnn.py` | Batch prediction for a folder of complexes, using the authors' `predict.py` |
| `test_1a30.py` | Installation test with complex **1a30**, compared with the authors' published results |
| `demo_sfcnn.bat` | One-click Windows demo |

> **Good news:** Sfcnn is the easiest scoring function so far. The weights come with the code, nothing has to be downloaded separately, and the authors published their own predictions. Our installation reproduces them: 1a30 gives exactly the value in their CASF-2016 results file, and their 74 docking poses of 1a30 match within 0.001.
>
> **Things to know**
> - The authors' `build_model()` loads the weights from the **current folder**. If you call it from elsewhere, you get `OSError: Unable to open file`. `predict_sfcnn.py` handles this.
> - The featurization uses Open Babel's atom hybridization, so the Open Babel version matters. Keep 3.1.x. Eaves *et al.* used a much older setup (Python 2.7, Open Babel 2.3.90, TensorFlow 2.1).
> - Unlike OnionNet-2, waters are not an issue here, because CASF-2016 and the authors' test files are identical for 1a30.

---

## Quick demo (Windows, one click)

Double-click `demo_sfcnn.bat` in this folder. It does the following:

1. Activates Miniconda.
2. Creates the `sfcnn` environment if it does not exist. This takes several minutes, because TensorFlow is a large download.
3. Unzips the Sfcnn code and weights from `Funciones_Score_Tabla1\SFCNN.zip`.
4. Checks the MD5 of the weights.
5. Runs `test_1a30.py` with the 74 docking poses.

The window stays open at the end so you can read the result (`RESULT: PASS`).

The default paths match our lab computer. On another computer, set `SF`, `CASF`, `ZIP` or `CONDA` in the Anaconda Prompt and run the script from there.

---

## A. Installation with Miniconda (Windows)

Requirements: Miniconda installed (`C:\Users\Admin\miniconda3`) and about 2 GB of free disk space.

All commands go in the **Anaconda Prompt (miniconda3)**.

### A1. Define the folders

```bat
set PLUGIN=C:\Users\Admin\Desktop\PROYECTO_UNIVERSIDAD\combi_lab_hub_tmp\plugins\sfcnn
set SF=C:\Users\Admin\Desktop\PROYECTO_UNIVERSIDAD\sf
set CASF=C:\Users\Admin\Desktop\SOFTWARE SF\CASF-2016\CASF-2016
mkdir "%SF%"
```

> `set` only lasts for the current window. If you open a new Anaconda Prompt, run the three `set` lines again.

### A2. Create the conda environment

```bat
conda env create -f "%PLUGIN%\environment.yml"
conda activate sfcnn
set TF_CPP_MIN_LOG_LEVEL=2
python -c "import tensorflow as tf, numpy; from openbabel import openbabel as ob; print('tensorflow', tf.__version__, '| numpy', numpy.__version__, '| openbabel', ob.OBReleaseVersion())"
```

Expected output: `tensorflow 2.3.4 | numpy 1.18.5 | openbabel 3.1.1`.

The environment is the same as OnionNet-2's, without scikit-learn. If you already created `onionnet2`, you can also run Sfcnn inside it.

### A3. Get the Sfcnn code and weights (pinned commit)

**Option 1, with Git:**

```bat
git clone https://github.com/bioinfocqupt/Sfcnn.git "%SF%\Sfcnn"
git -C "%SF%\Sfcnn" checkout 30ba8f0f8d54e1860d8e4672beb5fb7920bf7b4d
```

**Option 2, without Git:** unzip `SOFTWARE SF\Funciones_Score_Tabla1\SFCNN.zip`. Its content is identical to that commit. Rename the folder `Sfcnn-HEAD` to `Sfcnn` and move it into `%SF%`.

Check the weights:

```bat
certutil -hashfile "%SF%\Sfcnn\weights_22_112-0.0083.h5" MD5
```

It must print `b1315396dfd1616b4be80fdaeff4a428`.

### A4. Run the installation test (complex 1a30)

```bat
conda activate sfcnn
python "%PLUGIN%\test_1a30.py" --sfcnn-dir "%SF%\Sfcnn" --complex "%CASF%\coreset\1a30" --decoys
```

Expected result (a few seconds):

```
[1] Predicted pKd 1a30: 5.4721 (authors 5.4721, experimental 4.30)
    PASS - matches the authors' prediction

[2] 1a30 docking poses: 74 scored (authors 74), max difference 0.0007
    PASS - matches the authors' test/output2

RESULT: PASS
```

What each check verifies:
- `[1]` The CASF-2016 complex 1a30 gets the same score as in the authors' own CASF-2016 predictions (`Sfcnn/Sfcnn_2016_test.csv`).
- `[2]` The 74 docking poses in `test/1a30_decoys.mol2` get the same scores as the authors' `test/output2`. This shows that Open Babel and TensorFlow behave as in the authors' setup.

Complex 1a30 is over-predicted by Sfcnn too, so 5.47 against the experimental 4.30 is the **expected** behaviour. Omit `--decoys` for a faster test with only check `[1]`.

### A5. Use Sfcnn on your own complexes

Put each complex in its own folder with `<code>_protein.pdb` and `<code>_ligand.mol2` (or `.sdf` / `.pdb`). CASF-2016 folders work as they are.

```bat
python "%PLUGIN%\predict_sfcnn.py" --sfcnn-dir "%SF%\Sfcnn" -d "%CASF%\coreset" -o "%SF%\results_sfcnn\predictions.csv"
```

The output `predictions.csv` has one row per complex (`pdbid`, `pKd_predicted`).

The authors' script also works, from inside the Sfcnn folder:

```bat
cd /d "%SF%\Sfcnn"
python predict.py -p test\1a30_protein.pdb -l test\1a30_ligand.mol2 -o output1
python predict.py -p test\1a30_protein.pdb -l test\1a30_decoys.mol2 -o output2
```

---

## B. Installation with Docker (alternative)

Requirements: Docker Desktop with the WSL2 backend, and internet access during the build (GitHub, Debian mirrors, conda-forge and PyPI). Steps A2–A3 are not needed.

### B1. Build the image

```bat
cd /d C:\Users\Admin\Desktop\PROYECTO_UNIVERSIDAD\combi_lab_hub_tmp\plugins\sfcnn
docker build -t combilab/sfcnn:1.0 .
```

The build fails on purpose if the MD5 of the weights does not match.

### B2. Run the installation test

```bat
docker run --rm -v "C:\Users\Admin\Desktop\SOFTWARE SF\CASF-2016\CASF-2016\coreset\1a30:/complex:ro" combilab/sfcnn:1.0 python /opt/sfcnn/test_1a30.py --sfcnn-dir /opt/Sfcnn --complex /complex --decoys
```

### B3. Predict a set of complexes

```bat
docker run --rm -v "%CASF%\coreset:/input:ro" -v "%SF%\results_sfcnn:/data" combilab/sfcnn:1.0 python /opt/sfcnn/predict_sfcnn.py --sfcnn-dir /opt/Sfcnn -d /input -o /data/predictions.csv
```

---

## Troubleshooting

| Symptom | Cause and fix |
|---|---|
| `OSError: Unable to open file (... weights_22_112-0.0083.h5)` | `build_model()` was called outside the Sfcnn folder. Use `predict_sfcnn.py`, or `cd` into the Sfcnn folder first. |
| `ModuleNotFoundError: No module named 'openbabel'` | Open Babel is missing. Run `conda install -c conda-forge openbabel=3.1.1` in the environment. |
| `TypeError: Descriptors cannot be created directly` | protobuf is too new. Run `pip install protobuf==3.20.3`. |
| `[1]` or `[2]` FAIL with small differences | Different Open Babel version: hybridization assignments changed. Check A2. |
| `certutil` MD5 differs | The zip or clone is incomplete. Get the code again. |

## Uninstall

```bat
conda env remove -n sfcnn
rmdir /s /q "%SF%\Sfcnn"
docker rmi combilab/sfcnn:1.0
```

The last line is only needed if you used Docker.

---
*Prepared for CombiLabHUB (combi-lab). Tested on 19/10/2026 on Linux with Python 3.8, TensorFlow 2.3.4 (CPU) and Open Babel 3.1: both checks above pass against the authors' published results. On Windows, run step A4, or the demo, to confirm.*
