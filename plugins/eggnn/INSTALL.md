# egGNN — Installation guide (inference only)

**egGNN** (Edge-Gated Graph Neural Network) predicts protein–ligand binding affinity from two graphs: the **2D molecular graph of the ligand**, built from a SMILES string, and a **residue graph of the binding pocket** (one node per residue, edges between residue centres closer than 11 Å, with AAindex features). It does not use the ligand's 3D pose.

| | |
|---|---|
| Authors | Q. Jiao, Z. Qiu, Y. Wang, C. Chen, Z. Yang, X. Cui — IEEE BIBM 2021, <https://ieeexplore.ieee.org/document/9669846> |
| Code | <https://github.com/xfcui/egGNN>, pinned commit `5c66443e2bd5b4a9e8301db960cd58fb69db10a6` (licence GPL-3.0) |
| Trained model | `egGNN/checkpoint/16-8596.sav`, 11.7 MB, **included in the repository**, MD5 `4f8bd6d4e50adfe7dddf5e9f40146ad8` (the one the authors' pipeline uses). A second checkpoint, `16-8412.sav` (MD5 `e3def659ae76cc2e91123bf731d3a6cf`), is also in the repository. |
| Hardware | CPU is enough (well under 1 s per complex) |
| Reported CASF-2016 PCC | 0.86 (paper) — **Eaves et al. 2026 reproduce only 0.669** ("runnable, not reproducible") |

Files in this folder:

| File | Purpose |
|---|---|
| `environment.yml` | Python 3.10 + PyTorch 2.2.2 + DGL 2.2.1 + dgllife 0.3.2 + RDKit 2025.3.6 (pip versions checked for Windows) |
| `Dockerfile` | Self-contained image (CPU PyTorch 2.3.1 + conda-forge DGL 2.2.1) |
| `predict_eggnn.py` | Scores a folder of complexes (one protein–ligand pair per sub-folder) with the authors' graph builder and checkpoint |
| `test_1a30.py` | Installation test with complex **1a30** |
| `demo_eggnn.bat` | One-click Windows demo |

> **What to know before using egGNN**
>
> 1. **Give it the pocket, not the whole protein.** The authors' README says `--protein **.pdb`, but egGNN builds its residue graph from every residue in the file. With the full protein, Eaves et al. obtained PCC **0.071** on CASF-2016; with `<code>_pocket.pdb` they obtained **0.669**. Our wrapper uses `_pocket.pdb` by default. For 1a30: pocket → pKd 5.1040, full protein → 6.5326.
> 2. **The ligand is a SMILES string.** CASF-2016 has no `.smi` files, so the wrapper converts `<code>_ligand.mol2` to SMILES with RDKit (the `.sdf` files of several complexes, 1a30 among them, cannot be read by RDKit). For 1a30 this gives exactly the SMILES that Eaves et al. used (protonated form, e.g. `[NH3+]`, `C(=O)[O-]`). If a `<code>_ligand.smi` exists, it is used instead.
> 3. **The checkpoint needs two fixes to load.** It is a whole pickled model from 2021: its classes are stored as `__main__.EGG`, `__main__.GraphBlock`, …, and newer PyTorch expects two attributes (`GELU.approximate`, `ParameterList._size`) that did not exist then. `predict_eggnn.py` redirects the class names to `egGNN.model` and adds the attributes (the second fix is the same as in the Eaves et al. fork, <https://github.com/jeavesj/egGNN>). The weights are not changed.
> 4. **DGL versions.** DGL 2.2.1 is the last release with Windows wheels on PyPI, and it only works with PyTorch versions it ships a library for (2.1.x, 2.2.x, 2.3.0) and with `torchdata` older than 0.10. That is why `environment.yml` pins PyTorch 2.2.2 and torchdata 0.7.1. On Linux there is no PyPI wheel; the Dockerfile uses the conda-forge build, which requires PyTorch 2.3.1.
> 5. **Known quirk in the authors' featuriser (kept as is).** `feat.py` groups pocket atoms into residues by consecutive residue *name*, not residue number, so two identical residues in a row (e.g. Gly-Gly) become one node. We keep it because the model was trained this way.

---

## Quick demo (Windows, one click)

Double-click `demo_eggnn.bat` in this folder. It does the following:

1. Activates Miniconda.
2. Creates the `eggnn` environment if it does not exist. This takes several minutes, because PyTorch is a large download.
3. Unzips the egGNN code and checkpoints from `Funciones_Score_Tabla1\egGNN.zip`.
4. Checks the MD5 of `16-8596.sav`.
5. Runs `test_1a30.py`.

The window stays open at the end so you can read the result (`RESULT: PASS`).

The default paths match our lab computer. On another computer, set `SF`, `CASF`, `ZIP` or `CONDA` in the Anaconda Prompt and run the script from there.

---

## A. Installation with Miniconda (Windows)

Requirements: Miniconda installed (`C:\Users\Admin\miniconda3`) and about 2 GB of free disk space.

All commands go in the **Anaconda Prompt (miniconda3)**.

### A1. Define the folders

```bat
set PLUGIN=C:\Users\Admin\Desktop\PROYECTO_UNIVERSIDAD\combi_lab_hub_tmp\plugins\eggnn
set SF=C:\Users\Admin\Desktop\PROYECTO_UNIVERSIDAD\sf
set CASF=C:\Users\Admin\Desktop\SOFTWARE SF\CASF-2016\CASF-2016
mkdir "%SF%"
```

> `set` only lasts for the current window. If you open a new Anaconda Prompt, run the three `set` lines again.

### A2. Create the conda environment

```bat
conda env create -f "%PLUGIN%\environment.yml"
conda activate eggnn
set DGLBACKEND=pytorch
python -W ignore -c "import torch, dgl, rdkit; print('torch', torch.__version__, '| dgl', dgl.__version__, '| rdkit', rdkit.__version__)"
```

Expected output: `torch 2.2.2+cpu | dgl 2.2.1 | rdkit 2025.03.6`. On Windows, the PyPI builds of PyTorch and DGL are CPU-only.

### A3. Get the egGNN code (pinned commit)

**Option 1, with Git:**

```bat
git clone https://github.com/xfcui/egGNN.git "%SF%\egGNN"
git -C "%SF%\egGNN" checkout 5c66443e2bd5b4a9e8301db960cd58fb69db10a6
```

**Option 2, without Git:** unzip `SOFTWARE SF\Funciones_Score_Tabla1\egGNN.zip`. Its content is identical to that commit. Rename the folder `egGNN-HEAD` to `egGNN` and move it into `%SF%`.

Check the checkpoint:

```bat
certutil -hashfile "%SF%\egGNN\egGNN\checkpoint\16-8596.sav" MD5
```

It must print `4f8bd6d4e50adfe7dddf5e9f40146ad8`.

### A4. Run the installation test (complex 1a30)

```bat
conda activate eggnn
python "%PLUGIN%\test_1a30.py" --eggnn-dir "%SF%\egGNN" --complex "%CASF%\coreset\1a30"
```

Expected result (a few seconds):

```
[1] Ligand SMILES from 1a30_ligand.mol2:
    CC(C)C[C@H](NC(=O)[C@H](CC(=O)[O-])NC(=O)[C@@H]([NH3+])CCC(=O)[O-])C(=O)[O-]
    PASS - same SMILES as Eaves et al.

[2] SMILES + 1a30_pocket.pdb (recommended): pKd 5.1040 (reference 5.1040, experimental 4.30)
    PASS - matches the reference

[3] SMILES + 1a30_protein.pdb (full protein): pKd 6.5326 (reference 6.5326, experimental 4.30)
    PASS - matches the reference

RESULT: PASS
```

What each check verifies:
- `[1]` RDKit converts the CASF-2016 `.mol2` to the same SMILES Eaves et al. used.
- `[2]` The model, PyTorch, DGL and dgllife give **exactly** the value of Eaves et al. for 1a30 (`5.103977…` in `casf2016_egGNN_preds_and_times.csv` of their fork).
- `[3]` Shows how much the full protein changes the prediction (note 1 above).

### A5. Use egGNN on CASF-2016 or your own complexes

**CASF-2016 core set (285 complexes):**

```bat
python "%PLUGIN%\predict_eggnn.py" --eggnn-dir "%SF%\egGNN" -d "%CASF%\coreset" -o "%SF%\results_eggnn\predictions.csv"
```

The output CSV has `pdbid, pKd_predicted, ligand_source, smiles`.

**Your own complexes:** put each one in its own folder with `<code>_pocket.pdb` and one of `<code>_ligand.smi` (first word = SMILES), `<code>_ligand.mol2` or `<code>_ligand.sdf`. Options:
- `--protein-file protein` uses `<code>_protein.pdb` instead of the pocket (not recommended).
- `--checkpoint 16-8412.sav` uses the other checkpoint in the repository.

---

## B. Installation with Docker (alternative)

Requirements: Docker Desktop with the WSL2 backend, and internet access during the build (GitHub, Debian mirrors, conda-forge and PyPI). Steps A2–A3 are not needed.

### B1. Build the image

```bat
cd /d C:\Users\Admin\Desktop\PROYECTO_UNIVERSIDAD\combi_lab_hub_tmp\plugins\eggnn
docker build -t combilab/eggnn:1.0 .
```

The build fails on purpose if the MD5 of a checkpoint does not match.

### B2. Run the installation test

```bat
docker run --rm -v "C:\Users\Admin\Desktop\SOFTWARE SF\CASF-2016\CASF-2016\coreset\1a30:/complex:ro" combilab/eggnn:1.0 python /opt/eggnn/test_1a30.py --eggnn-dir /opt/egGNN --complex /complex
```

### B3. Score the CASF-2016 core set

```bat
docker run --rm -v "C:\Users\Admin\Desktop\SOFTWARE SF\CASF-2016\CASF-2016\coreset:/coreset:ro" -v "C:\Users\Admin\Desktop\PROYECTO_UNIVERSIDAD\sf\results_eggnn:/data" combilab/eggnn:1.0 python /opt/eggnn/predict_eggnn.py --eggnn-dir /opt/egGNN -d /coreset -o /data/predictions.csv
```

---

## Troubleshooting

| Symptom | Cause and fix |
|---|---|
| `AttributeError: Can't get attribute 'EGG' on <module '__main__'>` | The checkpoint was loaded with plain `torch.load`. Use `predict_eggnn.py`, which redirects the class names (note 3). |
| `AttributeError: 'GELU' object has no attribute 'approximate'` | Same cause: old pickled model on new PyTorch. Use `predict_eggnn.py`. |
| `Cannot find DGL C++ graphbolt library` | PyTorch version not supported by DGL 2.2.1. Recreate the environment from `environment.yml` (PyTorch 2.2.2). |
| `No module named 'torchdata.datapipes'` | torchdata 0.10 or newer. Install `torchdata==0.7.1` (Windows) or `0.8.0` (Docker). |
| `Skipping <code>: no readable ligand` | RDKit could not read the `.mol2` nor the `.sdf`. Write the SMILES into `<code>_ligand.smi`. |
| `error in get aaindex2` / crash in `construct_pocket_graph` | The pocket `.pdb` has no standard amino acids, or RDKit could not read it. |
| Predictions differ from the reference | Different RDKit, PyTorch or DGL version. Check A2. |

## Uninstall

```bat
conda env remove -n eggnn
rmdir /s /q "%SF%\egGNN"
docker rmi combilab/eggnn:1.0
```

The last line is only needed if you used Docker.

---
*Prepared for CombiLabHUB (combi-lab). Tested on 20/10/2026 on Linux with Python 3.10, PyTorch 2.3.1 (CPU), DGL 2.2.1, dgllife 0.3.2 and RDKit 2025.03.6: all three checks pass and 1a30 matches Eaves et al. to every printed digit. All Windows packages in `environment.yml` were checked to exist for Python 3.10. On Windows, run step A4, or the demo, to confirm.*
