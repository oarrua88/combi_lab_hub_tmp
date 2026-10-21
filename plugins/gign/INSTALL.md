# GIGN — Installation guide (inference only)

**GIGN** (Geometric Interaction Graph Neural Network) predicts protein–ligand binding affinity from the 3D structure of the complex. It builds one graph with the ligand atoms and the pocket atoms (residues within 5 Å of the ligand). The graph has two kinds of edges: covalent bonds and non-covalent contacts (atom pairs closer than 5 Å). Its message passing uses the 3D coordinates.

| | |
|---|---|
| Authors | Z. Yang, W. Zhong, Q. Lv, T. Dong, C. Y.-C. Chen — *J. Phys. Chem. Lett.* 2023, 14, 2020–2033 |
| Code | <https://github.com/guaguabujianle/GIGN>, pinned commit `ef514d326202d71b0674ae20e95456454bf10c6e` (licence MIT) |
| Trained models | Three checkpoints (independent training runs) **included in the repository**, in `GIGN/model/2022112*_GIGN_repeat{0,1,2}/model/*.pt`. MD5: repeat0 `b50f62d129b36c7ae2b4c22f214f2e57`, repeat1 `2789d71b97862ea1663b630de6fec6e5`, repeat2 `66fb93ebe5a51d33715e6e4e458e939c` |
| Authors' prepared data | `GIGN_data.zip` on Zenodo (10.5281/zenodo.7490623, 113 MB, MD5 `8bb40c2cad13ea149048b3cc8e1e4a18`). It holds already-built graphs of the test sets. It is **not needed** to run GIGN; we only used it to validate our preparation. |
| Hardware | CPU is enough (about 1 s per complex, mostly PyMOL and Open Babel) |
| Reported CASF-2016 PCC | 0.840 (paper, mean of the 3 runs) — Eaves et al. 2026 reproduce 0.85 |
| **Our check** | With the authors' prepared graphs of the 285 CASF-2016 complexes: PCC **0.8444 / 0.8432 / 0.8323** (repeat0/1/2), **0.8553** for the mean of the three |

Files in this folder:

| File | Purpose |
|---|---|
| `environment.yml` | Environment `gign`, **shared with EHIGN-PLA**: Python 3.10 + PyTorch 2.2.2 + PyG 2.5.3 + DGL 2.2.1 + RDKit + PyMOL + Open Babel |
| `Dockerfile` | Self-contained image (CPU PyTorch 2.3.1) |
| `predict_gign.py` | Scores a folder of complexes (one per sub-folder): pocket, ligand conversion, graph and prediction with the authors' functions |
| `test_1a30.py` | Installation test with complex **1a30** |
| `demo_gign.bat` | One-click Windows demo |

> **What to know before using GIGN**
>
> 1. **The pocket is made from the protein.** Like the authors' `preprocessing.py`, the wrapper removes waters and hydrogens with PyMOL and keeps the residues within 5 Å of the ligand. It then converts the ligand `.mol2` to `.pdb` without hydrogens with Open Babel (`obabel -d`) and reads both files with RDKit. The CASF `_pocket.pdb` files are not used.
> 2. **Our preparation is identical to the authors'.** For 1a30, the graph we build (node features, covalent and non-covalent edges, coordinates) is exactly the one in the authors' `GIGN_data.zip`. With their 285 prepared graphs, the three models give PCC 0.844 / 0.843 / 0.832, which matches the paper.
> 3. **Three models, one answer.** The repository has three trained runs, and their predictions can differ a lot for a single complex. For 1a30 they give 4.39, 6.34 and 6.44. `predict_gign.py` reports the **mean** as `pKd_predicted` and also writes each model's value. Use `--model 0` to reproduce the authors' `predict.py`, which loads only repeat0.
> 4. **Paths with spaces.** The authors' scripts call Open Babel with `os.system` and break on folders such as `SOFTWARE SF`. Their paths are also written inside the code. The wrapper calls Open Babel safely and works in a temporary folder.
> 5. **Checkpoints were saved on a GPU.** Loading them with plain `torch.load` fails on a CPU-only computer. The wrapper uses `map_location="cpu"`.

---

## Quick demo (Windows, one click)

Double-click `demo_gign.bat` in this folder. It does the following:

1. Activates Miniconda.
2. Creates the `gign` environment if it does not exist. This takes several minutes. The same environment serves EHIGN-PLA.
3. Unzips the GIGN code and checkpoints from `Funciones_Score_Tabla1\GIGN.zip`.
4. Checks the MD5 of the repeat0 checkpoint.
5. Runs `test_1a30.py`.

The window stays open at the end so you can read the result (`RESULT: PASS`).

The default paths match our lab computer. On another computer, set `SF`, `CASF`, `ZIP` or `CONDA` in the Anaconda Prompt and run the script from there.

---

## A. Installation with Miniconda (Windows)

Requirements: Miniconda installed (`C:\Users\Admin\miniconda3`) and about 3 GB of free disk space.

All commands go in the **Anaconda Prompt (miniconda3)**.

### A1. Define the folders

```bat
set PLUGIN=C:\Users\Admin\Desktop\PROYECTO_UNIVERSIDAD\combi_lab_hub_tmp\plugins\gign
set SF=C:\Users\Admin\Desktop\PROYECTO_UNIVERSIDAD\sf
set CASF=C:\Users\Admin\Desktop\SOFTWARE SF\CASF-2016\CASF-2016
mkdir "%SF%"
```

> `set` only lasts for the current window. If you open a new Anaconda Prompt, run the three `set` lines again.

### A2. Create the conda environment (shared with EHIGN-PLA)

Skip this step if you already created `gign` for EHIGN-PLA.

```bat
conda env create -f "%PLUGIN%\environment.yml"
conda activate gign
python -W ignore -c "import torch, torch_geometric, dgl, rdkit, pymol; print('torch', torch.__version__, '| pyg', torch_geometric.__version__, '| dgl', dgl.__version__, '| rdkit', rdkit.__version__)"
obabel -V
```

Expected output: `torch 2.2.2+cpu | pyg 2.5.3 | dgl 2.2.1 | rdkit 2025.03.6`, and an Open Babel 3.1 version line.

### A3. Get the GIGN code (pinned commit)

**Option 1, with Git:**

```bat
git clone https://github.com/guaguabujianle/GIGN.git "%SF%\GIGN"
git -C "%SF%\GIGN" checkout ef514d326202d71b0674ae20e95456454bf10c6e
```

**Option 2, without Git:** unzip `SOFTWARE SF\Funciones_Score_Tabla1\GIGN.zip`. Its content is identical to that commit. Rename the folder `GIGN-HEAD` to `GIGN` and move it into `%SF%`.

Check the checkpoints:

```bat
cd /d "%SF%\GIGN\GIGN\model"
for /r %F in (*.pt) do certutil -hashfile "%F" MD5
```

The three values must be the ones in the table at the top.

### A4. Run the installation test (complex 1a30)

```bat
conda activate gign
python "%PLUGIN%\test_1a30.py" --gign-dir "%SF%\GIGN" --complex "%CASF%\coreset\1a30"
```

Expected result (a few seconds):

```
[1] Graph of 1a30: 26 ligand + 160 pocket atoms, 348 covalent + 530 non-covalent edges
    PASS - same as the authors' prepared graph

[2] Trained models (experimental pKd 4.30):
    model 0: pKd 4.3883 (reference 4.3883) PASS
    model 1: pKd 6.3427 (reference 6.3427) PASS
    model 2: pKd 6.4380 (reference 6.4380) PASS
    mean   : pKd 5.7230 (reference 5.7230)

RESULT: PASS
```

What each check verifies:
- `[1]` PyMOL, Open Babel and RDKit prepare 1a30 exactly as the authors did.
- `[2]` The three trained models, PyTorch and PyG give the same values as the authors' own scripts.

### A5. Use GIGN on CASF-2016 or your own complexes

**CASF-2016 core set (285 complexes):**

```bat
python "%PLUGIN%\predict_gign.py" --gign-dir "%SF%\GIGN" -d "%CASF%\coreset" -o "%SF%\results_gign\predictions.csv"
```

The output CSV has `pdbid, pKd_predicted` (the mean of the three models) and `pKd_model0..2`.

**Your own complexes:** put each one in its own folder with `<code>_protein.pdb` and `<code>_ligand.mol2`. Use `--model 0`, `1` or `2` to run a single model.

---

## B. Installation with Docker (alternative)

Requirements: Docker Desktop with the WSL2 backend, and internet access during the build (GitHub, Debian mirrors, conda-forge and PyPI). Steps A2–A3 are not needed.

### B1. Build the image

```bat
cd /d C:\Users\Admin\Desktop\PROYECTO_UNIVERSIDAD\combi_lab_hub_tmp\plugins\gign
docker build -t combilab/gign:1.0 .
```

The build fails on purpose if the MD5 of a checkpoint does not match.

### B2. Run the installation test

```bat
docker run --rm -v "C:\Users\Admin\Desktop\SOFTWARE SF\CASF-2016\CASF-2016\coreset\1a30:/complex:ro" combilab/gign:1.0 python /opt/gign/test_1a30.py --gign-dir /opt/GIGN --complex /complex
```

### B3. Score the CASF-2016 core set

```bat
docker run --rm -v "C:\Users\Admin\Desktop\SOFTWARE SF\CASF-2016\CASF-2016\coreset:/coreset:ro" -v "C:\Users\Admin\Desktop\PROYECTO_UNIVERSIDAD\sf\results_gign:/data" combilab/gign:1.0 python /opt/gign/predict_gign.py --gign-dir /opt/GIGN -d /coreset -o /data/predictions.csv
```

---

## Troubleshooting

| Symptom | Cause and fix |
|---|---|
| `Attempting to deserialize object on a CUDA device` | The checkpoint was loaded without `map_location`. Use `predict_gign.py`. |
| `Open Babel failed` / `'obabel' is not recognized` | The `gign` environment is not active, or Open Babel is missing. Run `conda activate gign` and `obabel -V`. |
| `RDKit cannot read the ligand` | The converted `.pdb` has unusual valences. Check the `.mol2` file. |
| `Skipping <code>: ...` for a few complexes | The wrapper keeps going and lists them. The authors' scripts would stop. |
| `No module named 'torch_geometric'` | Recreate the environment from `environment.yml`. |
| Predictions differ from the reference | Different RDKit, PyMOL, Open Babel or PyTorch version. Check A2. |

## Uninstall

```bat
conda env remove -n gign
rmdir /s /q "%SF%\GIGN"
docker rmi combilab/gign:1.0
```

Do not remove the `gign` environment if you also use EHIGN-PLA. The last line is only needed if you used Docker.

---
*Prepared for CombiLabHUB (combi-lab). Tested on 20/10/2026 on Linux with Python 3.10, PyTorch 2.3.1 (CPU), PyG 2.5.3, RDKit 2025.03.6, PyMOL 3.1.0 and Open Babel 3.1.1. The 1a30 test passes, our 1a30 graph is identical to the authors' one, and the authors' 285 prepared CASF-2016 graphs give the PCCs above. All Windows packages in `environment.yml` were checked to exist for Python 3.10. On Windows, run step A4, or the demo, to confirm.*
