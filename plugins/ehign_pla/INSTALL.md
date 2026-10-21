# EHIGN-PLA — Installation guide (inference only)

**EHIGN** (Edge-enhanced Heterogeneous Interaction Graph Network) predicts protein–ligand binding affinity from the 3D structure of the complex. It builds a DGL heterograph with two node types: ligand atoms, and pocket atoms within 5 Å of the ligand. It has four edge types: ligand bonds, pocket bonds, ligand→pocket contacts and pocket→ligand contacts (< 5 Å). Every edge carries 3D geometric features such as angles, areas and distances. The network makes two predictions, one in each direction, and their mean is the pKd.

| | |
|---|---|
| Authors | Z. Yang et al. (same group as GIGN), 2024 — *Interaction-Based Inductive Bias in Graph Neural Networks: Enhancing Protein-Ligand Binding Affinity Predictions from 3D Structures* (see the repository) |
| Code | <https://github.com/guaguabujianle/EHIGN_PLA>, pinned commit `dfd88256318c1a35c7c7adb5534f0c706d9a16f3` (licence MIT) |
| Trained models | Three checkpoints (independent training runs) **included in the repository**, in `model/20230120_*_EHIGN_repeat{0,1,2}/model/*.pt`. MD5: repeat0 `4b0beacc9c4f052e87b9b8d2425c17b0`, repeat1 `efacfb7ad8345205e659f0437c3d48e5`, repeat2 `c4829175b75b69024ff4c3a2f3fe769f` |
| Authors' prepared data | Google Drive file `1oGUP4z7htNXyxTqx95HNSDLsaoxa3fX7` (preprocessed graphs, for training). **Not needed** for inference. |
| Hardware | CPU is enough (about 1 s per complex) |
| Reported CASF-2016 PCC | 0.854 (paper) — Eaves et al. 2026 reproduce 0.851 |

Files in this folder:

| File | Purpose |
|---|---|
| `environment.yml` | Environment `gign`, **shared with GIGN**: Python 3.10 + PyTorch 2.2.2 + DGL 2.2.1 + PyG + RDKit + PyMOL + Open Babel |
| `Dockerfile` | Self-contained image (CPU PyTorch 2.3.1 + conda-forge DGL 2.2.1) |
| `predict_ehign_pla.py` | Scores a folder of complexes (one per sub-folder): pocket, ligand conversion, graph and prediction with the authors' functions |
| `test_1a30.py` | Installation test with complex **1a30** |
| `demo_ehign_pla.bat` | One-click Windows demo |

> **What to know before using EHIGN-PLA**
>
> 1. **Same preparation as GIGN.** PyMOL removes waters and hydrogens and keeps the residues within 5 Å of the ligand. Open Babel converts the ligand `.mol2` to `.pdb` without hydrogens (`obabel -d`), and RDKit reads both files. This is the authors' `preprocess_complex.py`. For GIGN we checked that this preparation reproduces the authors' graphs exactly.
> 2. **The code was written for DGL 0.9.** `NIGConv.py` uses `dgl.function.copy_src`, which was removed in DGL 1.0, so the authors' `test.py` fails with recent DGL (`module 'dgl.function' has no attribute 'copy_src'`). The Eaves et al. fork still runs on DGL 0.9.1 (CUDA, Linux only), so it does not fix this. Our wrapper maps `copy_src` to its new name, `copy_u`, which is the same message function. The weights are not changed.
> 3. **Three models, one answer.** The repository has three trained runs. For 1a30 they give 5.50, 5.81 and 5.09. `predict_ehign_pla.py` reports the **mean** as `pKd_predicted` and also writes each model's value. Use `--model 0` to reproduce the authors' `test.py`, which loads only repeat0, as Eaves et al. did.
> 4. **The model changes its input graph.** The network overwrites the node features of the graph it receives. The wrapper reloads the graph for each model; reusing one graph object for several models gives a shape error.
> 5. **Errors are hidden in the authors' graph builder.** `mols2graphs` catches every error and silently saves nothing. The wrapper reports these complexes as "graph construction failed" and goes on.
> 6. Paths with spaces and CPU-only loading: same fixes as in GIGN (no `os.system`, `map_location="cpu"`).

---

## Quick demo (Windows, one click)

Double-click `demo_ehign_pla.bat` in this folder. It does the following:

1. Activates Miniconda.
2. Creates the `gign` environment if it does not exist. This takes several minutes. The same environment serves GIGN.
3. Unzips the EHIGN-PLA code and checkpoints from `Funciones_Score_Tabla1\EHIGN-PLA.zip`.
4. Checks the MD5 of the repeat0 checkpoint.
5. Runs `test_1a30.py`.

The window stays open at the end so you can read the result (`RESULT: PASS`).

The default paths match our lab computer. On another computer, set `SF`, `CASF`, `ZIP` or `CONDA` in the Anaconda Prompt and run the script from there.

---

## A. Installation with Miniconda (Windows)

Requirements: Miniconda installed (`C:\Users\Admin\miniconda3`) and about 3 GB of free disk space (shared with GIGN).

All commands go in the **Anaconda Prompt (miniconda3)**.

### A1. Define the folders

```bat
set PLUGIN=C:\Users\Admin\Desktop\PROYECTO_UNIVERSIDAD\combi_lab_hub_tmp\plugins\ehign_pla
set SF=C:\Users\Admin\Desktop\PROYECTO_UNIVERSIDAD\sf
set CASF=C:\Users\Admin\Desktop\SOFTWARE SF\CASF-2016\CASF-2016
mkdir "%SF%"
```

> `set` only lasts for the current window. If you open a new Anaconda Prompt, run the three `set` lines again.

### A2. Create the conda environment (shared with GIGN)

Skip this step if you already created `gign` for GIGN.

```bat
conda env create -f "%PLUGIN%\environment.yml"
conda activate gign
set DGLBACKEND=pytorch
python -W ignore -c "import torch, dgl, rdkit, pymol; print('torch', torch.__version__, '| dgl', dgl.__version__, '| rdkit', rdkit.__version__)"
obabel -V
```

Expected output: `torch 2.2.2+cpu | dgl 2.2.1 | rdkit 2025.03.6`, and an Open Babel 3.1 version line.

### A3. Get the EHIGN-PLA code (pinned commit)

**Option 1, with Git:**

```bat
git clone https://github.com/guaguabujianle/EHIGN_PLA.git "%SF%\EHIGN_PLA"
git -C "%SF%\EHIGN_PLA" checkout dfd88256318c1a35c7c7adb5534f0c706d9a16f3
```

**Option 2, without Git:** unzip `SOFTWARE SF\Funciones_Score_Tabla1\EHIGN-PLA.zip`. Its content is identical to that commit. Rename the folder `EHIGN_PLA-HEAD` to `EHIGN_PLA` and move it into `%SF%`.

Check the checkpoints:

```bat
cd /d "%SF%\EHIGN_PLA\model"
for /r %F in (*.pt) do certutil -hashfile "%F" MD5
```

The three values must be the ones in the table at the top.

### A4. Run the installation test (complex 1a30)

```bat
conda activate gign
python "%PLUGIN%\test_1a30.py" --ehign-dir "%SF%\EHIGN_PLA" --complex "%CASF%\coreset\1a30"
```

Expected result (a few seconds):

```
[1] Graph of 1a30: 26 ligand + 160 pocket atoms; edges 50 ligand, 298 pocket, 265 l->p, 265 p->l
    PASS - matches the reference

[2] Trained models (experimental pKd 4.30):
    model 0: pKd 5.5024 (reference 5.5024) PASS
    model 1: pKd 5.8087 (reference 5.8087) PASS
    model 2: pKd 5.0898 (reference 5.0898) PASS
    mean   : pKd 5.4670 (reference 5.4670)

RESULT: PASS
```

What each check verifies:
- `[1]` PyMOL, Open Babel and RDKit prepare 1a30 as expected. The pocket is the same 160 atoms as in GIGN.
- `[2]` The three trained models, PyTorch and DGL give the same values as the authors' own scripts (`preprocess_complex.py` → `graph_constructor.py` → `test.py`, with only the `copy_src` fix).

### A5. Use EHIGN-PLA on CASF-2016 or your own complexes

**CASF-2016 core set (285 complexes):**

```bat
python "%PLUGIN%\predict_ehign_pla.py" --ehign-dir "%SF%\EHIGN_PLA" -d "%CASF%\coreset" -o "%SF%\results_ehign_pla\predictions.csv"
```

The output CSV has `pdbid, pKd_predicted` (the mean of the three models) and `pKd_model0..2`.

**Your own complexes:** put each one in its own folder with `<code>_protein.pdb` and `<code>_ligand.mol2`. Use `--model 0`, `1` or `2` to run a single model.

---

## B. Installation with Docker (alternative)

Requirements: Docker Desktop with the WSL2 backend, and internet access during the build (GitHub, Debian mirrors, conda-forge and PyPI). Steps A2–A3 are not needed.

### B1. Build the image

```bat
cd /d C:\Users\Admin\Desktop\PROYECTO_UNIVERSIDAD\combi_lab_hub_tmp\plugins\ehign_pla
docker build -t combilab/ehign_pla:1.0 .
```

The build fails on purpose if the MD5 of a checkpoint does not match.

### B2. Run the installation test

```bat
docker run --rm -v "C:\Users\Admin\Desktop\SOFTWARE SF\CASF-2016\CASF-2016\coreset\1a30:/complex:ro" combilab/ehign_pla:1.0 python /opt/ehign_pla/test_1a30.py --ehign-dir /opt/EHIGN_PLA --complex /complex
```

### B3. Score the CASF-2016 core set

```bat
docker run --rm -v "C:\Users\Admin\Desktop\SOFTWARE SF\CASF-2016\CASF-2016\coreset:/coreset:ro" -v "C:\Users\Admin\Desktop\PROYECTO_UNIVERSIDAD\sf\results_ehign_pla:/data" combilab/ehign_pla:1.0 python /opt/ehign_pla/predict_ehign_pla.py --ehign-dir /opt/EHIGN_PLA -d /coreset -o /data/predictions.csv
```

---

## Troubleshooting

| Symptom | Cause and fix |
|---|---|
| `module 'dgl.function' has no attribute 'copy_src'` | You ran the authors' `test.py` with DGL ≥ 1.0. Use `predict_ehign_pla.py` (note 2). |
| `mat1 and mat2 shapes cannot be multiplied (..x256 and 35x256)` | The same graph object was passed to a model twice (note 4). Use `predict_ehign_pla.py`. |
| `graph construction failed` | No ligand–pocket contact within 5 Å, or NaN edge features. Check the input files. |
| `Cannot find DGL C++ graphbolt library` | PyTorch version not supported by DGL 2.2.1. Recreate the environment from `environment.yml`. |
| `No module named 'torchdata.datapipes'` | torchdata 0.10 or newer. Install `torchdata==0.7.1` (Windows) or `0.8.0` (Docker). |
| `Open Babel failed` / `'obabel' is not recognized` | The `gign` environment is not active. Run `conda activate gign` and `obabel -V`. |
| Predictions differ from the reference | Different RDKit, PyMOL, Open Babel, PyTorch or DGL version. Check A2. |

## Uninstall

```bat
conda env remove -n gign
rmdir /s /q "%SF%\EHIGN_PLA"
docker rmi combilab/ehign_pla:1.0
```

Do not remove the `gign` environment if you also use GIGN. The last line is only needed if you used Docker.

---
*Prepared for CombiLabHUB (combi-lab). Tested on 20/10/2026 on Linux with Python 3.10, PyTorch 2.3.1 (CPU), DGL 2.2.1, RDKit 2025.03.6, PyMOL 3.1.0 and Open Babel 3.1.1. The 1a30 test passes, and the wrapper gives the same three values as the authors' own pipeline. The full core-set PCC was not computed yet: the authors' prepared graphs are on Google Drive, which is not reachable from our test machine. All Windows packages in `environment.yml` were checked to exist for Python 3.10. On Windows, run step A4, or the demo, to confirm.*
