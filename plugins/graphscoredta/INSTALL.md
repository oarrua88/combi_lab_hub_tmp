# GraphscoreDTA — Installation guide (inference only)

**GraphscoreDTA** predicts protein–ligand binding affinity with a graph neural network. It combines a heterogeneous graph (ligand atoms, pocket residues and the ligand–pocket interactions, with bitransport information and distance-based gates) with **6 AutoDock Vina energy terms**.

| | |
|---|---|
| Authors | K. Wang, R. Zhou, J. Tang, M. Li — *Bioinformatics* 39(6), btad340 (2023) |
| Code | <https://github.com/CSUBioGroup/GraphscoreDTA>, pinned commit `d7d1230fb33d803f5c8f86e66c1598ab4d7ea68d` (licence GPL-3.0) |
| Trained model | `model/modelp.pth` (used by the authors' `predict.py`), **included in the repository**, MD5 `428d508d75994a853f75fd0cc9c3c4da`. `model/modelc.pth` (MD5 `972eae3b6a29bf764fda37a19fc0fc73`) is also included. |
| Pre-processed CASF-2016 | `all_in_one_graph_test2016.bin`, 35 MB, GitHub release **Data**, MD5 `a8c2ad64c46c2f13a6702a0856bde044` (279 complexes). Vina terms and labels are in the repository (`test_set/`). |
| Hardware | CPU is enough (the 279 complexes take a few seconds) |
| Reported CASF-2016 PCC | 0.831 (paper). With the authors' files we obtain **0.810** on their 279 complexes. Not in Eaves et al. 2026. |

Files in this folder:

| File | Purpose |
|---|---|
| `environment.yml` | Python 3.10 + PyTorch 2.2.2 + DGL 2.2.1 (same pair as the egGNN plugin) |
| `Dockerfile` | Self-contained image (CPU PyTorch 2.3.1 + conda-forge DGL 2.2.1), downloads the graphs too |
| `predict_graphscoredta.py` | Scores the authors' pre-processed CASF-2016 complexes on CPU |
| `test_1a30.py` | Installation test (see note 1: 1a30 cannot be scored) |
| `demo_graphscoredta.bat` | One-click Windows demo |

> **What to know before using GraphscoreDTA**
>
> 1. **It cannot score new complexes, 1a30 included.** The repository has the model and the CASF-2016 inputs already built, but **not the code that builds them** (graph construction and the 6 Vina terms). The authors' set has 279 of the 285 core-set complexes; the 6 missing ones are **1a30**, 2zcr, 2zy1, 3ag9, 3bv9 and 3uri. So the installation test reproduces the authors' own predictions (`result/predict_test2016.csv`) instead of scoring 1a30. Any CASF-2016 PCC will be on 279 complexes, not 285.
> 2. **The authors' code only runs on an NVIDIA GPU.** `ModelNew.forward()` moves every input to `'cuda:0'`, and `predict.py` calls `.cuda()` on the loss. `predict_graphscoredta.py` loads the authors' `src/model.py` with `'cuda:0'` replaced by `'cpu'`; nothing else is changed. It also skips `metrics.py`, which needs numba.
> 3. **Newer PyTorch and DGL than the paper** (PyTorch 1.9 + DGL 0.9.1 with CUDA 10.2). With PyTorch 2.2/2.3 and DGL 2.2.1 the 279 predictions match the authors' file within 0.00005.

---

## Quick demo (Windows, one click)

Double-click `demo_graphscoredta.bat` in this folder. It does the following:

1. Activates Miniconda.
2. Creates the `gsdta` environment if it does not exist (several minutes, PyTorch is a large download).
3. Unzips the code and models from `Funciones_Score_Tabla1\GraphScoreDTA.zip`.
4. Downloads `all_in_one_graph_test2016.bin` (35 MB) and checks its MD5.
5. Runs `test_1a30.py`. The window must end with `RESULT: PASS`.

---

## A. Installation with Miniconda (Windows)

Open an **Anaconda Prompt**.

### A1. Define the folders

```bat
set PLUGIN=C:\Users\Admin\Desktop\PROYECTO_UNIVERSIDAD\combi_lab_hub_tmp\plugins\graphscoredta
set SF=C:\Users\Admin\Desktop\PROYECTO_UNIVERSIDAD\sf
mkdir "%SF%"
```

### A2. Create the conda environment

```bat
conda env create -f "%PLUGIN%\environment.yml"
conda activate gsdta
set DGLBACKEND=pytorch
python -W ignore -c "import torch, dgl; print('torch', torch.__version__, '| dgl', dgl.__version__)"
```

Expected output: `torch 2.2.2+cpu | dgl 2.2.1`.

### A3. Get the code (pinned commit) and the pre-processed graphs

**Option 1, with Git:**

```bat
git clone https://github.com/CSUBioGroup/GraphscoreDTA.git "%SF%\GraphscoreDTA"
git -C "%SF%\GraphscoreDTA" checkout d7d1230fb33d803f5c8f86e66c1598ab4d7ea68d
```

**Option 2, without Git:** unzip `SOFTWARE SF\Funciones_Score_Tabla1\GraphScoreDTA.zip`, rename `GraphscoreDTA-HEAD` to `GraphscoreDTA` and move it into `%SF%`.

Then download the graphs into `test_set`:

```bat
powershell -Command "Invoke-WebRequest -Uri 'https://github.com/CSUBioGroup/GraphscoreDTA/releases/download/Data/all_in_one_graph_test2016.bin' -OutFile '%SF%\GraphscoreDTA\test_set\all_in_one_graph_test2016.bin'"
certutil -hashfile "%SF%\GraphscoreDTA\test_set\all_in_one_graph_test2016.bin" MD5
```

It must print `a8c2ad64c46c2f13a6702a0856bde044`.

### A4. Run the installation test

```bat
conda activate gsdta
python -W ignore "%PLUGIN%\test_1a30.py" --gs-dir "%SF%\GraphscoreDTA"
```

Expected output (end):

```
[1] Is 1a30 in the authors' pre-processed CASF-2016 set? NO
...
[2] 279 complexes scored, 279 in the authors' result file, max difference 0.00005
    PCC on these 279 complexes: 0.810 (paper 0.831 on CASF-2016)
    PASS - matches the authors' predictions

RESULT: PASS
```

### A5. Score CASF-2016

```bat
python -W ignore "%PLUGIN%\predict_graphscoredta.py" --gs-dir "%SF%\GraphscoreDTA" -o "%SF%\results_graphscoredta\predictions.csv"
```

Output columns: `pdbid, pKd_predicted, pKd_experimental` (279 rows).

---

## B. Installation with Docker (alternative)

### B1. Build the image

```bat
cd /d "%PLUGIN%"
docker build -t combilab/graphscoredta:1.0 .
```

### B2. Run the installation test

```bat
docker run --rm combilab/graphscoredta:1.0
```

### B3. Score CASF-2016

```bat
docker run --rm -v "%SF%\results_graphscoredta:/data" combilab/graphscoredta:1.0 python /opt/graphscoredta/predict_graphscoredta.py --gs-dir /opt/GraphscoreDTA -o /data/predictions.csv
```

---

## Troubleshooting

| Problem | Cause / fix |
|---|---|
| `Device API cuda is not enabled` or `Torch not compiled with CUDA enabled` | You ran the authors' `predict.py`. Use `predict_graphscoredta.py` (note 2). |
| `ModuleNotFoundError: No module named 'numba'` | Same: the authors' `metrics.py`. Not needed by our scripts. |
| `ERROR: file not found: ...all_in_one_graph_test2016.bin` | Step A3, download the graphs. |
| `No module named 'torchdata.datapipes'` | torchdata ≥ 0.10 was installed. `pip install torchdata==0.7.1`. |

## Uninstall

```bat
conda deactivate
conda env remove -n gsdta
rmdir /s /q "%SF%\GraphscoreDTA"
```

---

*Prepared for CombiLabHUB (combi-lab). Tested on 21/10/2026 on Linux with Python 3.10, PyTorch 2.3.1 (CPU) and DGL 2.2.1 (conda-forge): the 279 predictions match the authors' `result/predict_test2016.csv` (max difference 0.00005, PCC 0.810). The Windows environment uses the same PyTorch/DGL pair as the egGNN plugin. On Windows, run step A4, or the demo, to confirm.*
