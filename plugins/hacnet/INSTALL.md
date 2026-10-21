# HAC-Net — Installation guide (inference only)

**HAC-Net** (Hybrid Attention-Based Convolutional Neural Network) predicts protein–ligand binding affinity as the average of three models: a **3D-CNN with channel-wise (squeeze-and-excitation) attention** on a voxelised pocket + ligand, and **two gated graph neural networks** with attention-based aggregation. Its features include **EqEq partial charges** of the pocket atoms.

| | |
|---|---|
| Authors | G. W. Kyro, R. I. Brent, V. S. Batista — *J. Chem. Inf. Model.* 63(7), 1947–1960 (2023) |
| Code | <https://github.com/gregory-kyro/HAC-Net>, pinned commit `def30e100ea9eeca3fafb0658823446b97e07ec2` (licence MIT), and the official package **HACNet 1.4.3** from PyPI |
| Trained models | `HACNet/parameter_files/` in the repository: `CNN_parameters.pt` (MD5 `7a16badb6abcdbf9075aea5f69b5acdf`), `GCN0_parameters.pt` (`dd12042a2b43aef2ba047e04116a9b07`), `GCN1_parameters.pt` (`04f8f791e2c14e667ca09ba292cca390`), `MLP_parameters.pt` (`91df31324dd88524d5278d017f57e2dd`) |
| Pocket charges | EqEq, from the **ACC2 web service** (<https://acc2.ncbr.muni.cz>, needs internet) or, offline, from **ChargeFW2** 3.0.0 (<https://github.com/sb-ncbr/ChargeFW2>, the program ACC2 runs; included in the Docker image) |
| Hardware | CPU is enough (a few seconds per complex, plus the ACC2 round trip) |
| Reported CASF-2016 PCC | 0.846 (paper); 0.83 with the package's own preprocessing (`predict_pkd_info.txt`) — **Eaves et al. 2026 obtain 0.777** ("runnable, not reproducible"; see note 2) |

Files in this folder:

| File | Purpose |
|---|---|
| `environment.yml` | Python 3.10 + PyTorch 2.2.2 + PyG 2.5.3 + Open Babel 3.1.1 + PyMOL 3.1.0 + HACNet 1.4.3 |
| `Dockerfile` | Self-contained image (CPU PyTorch 2.3.1 + PyG from conda-forge) **with ChargeFW2**, works offline |
| `predict_hacnet.py` | Scores a folder of complexes with the official `predict_pkd()` (see notes) |
| `test_1a30.py` | Installation test with complex **1a30** |
| `demo_hacnet.bat` | One-click Windows demo |

> **What to know before using HAC-Net**
>
> 1. **Use the PyPI package, not the repository's `functions.py`.** The official `predict_pkd()` (HACNet 1.4.3 on PyPI) is self-contained: it defines its own CNN (attention layers named `SE_block`, loaded with `strict=True`), the two GCNs and the final linear model. The repository's `HACNet/functions.py` calls classes it never defines, and its `MLP.py` does not even compile on Python 3 (mixed tabs and spaces). The trained parameters and `element_features.xml` are only in the repository, so you need both.
> 2. **Why Eaves et al. may get 0.777.** Their CLI (fork <https://github.com/jeavesj/HAC-Net>) copies the Colab notebook, which imports the CNN from the repository's `CNN.py`. There the attention layers are named `se_block`, while the parameter file says `SE_block`, and the weights are loaded with `strict=False`. So the 6 attention weight matrices of the CNN **keep random values** instead of the trained ones, and the CNN third of every prediction changes from run to run. The notebook also changes the GCN aggregation (note 4).
> 3. **The original charge server is gone.** The package posts the pocket to `http://78.128.250.156`, which no longer answers. `predict_hacnet.py --charges acc2` uses the current ACC2 API with the same settings as the Eaves et al. fork (EqEq, read HETATM, ignore water, permissive types). `--charges chargefw2` runs ChargeFW2 locally with the same settings; ChargeFW2 has no Windows build, so on Windows use ACC2, or the Docker image. (Open Babel also has an "eqeq" model, but it is meant for crystals and fails on proteins.)
> 4. **Small changes for current PyTorch Geometric, without changing the model.** The package creates the gated graph layer with `aggregation=…`, an argument old PyG ignored. So the GCNs were trained with the default "add" aggregation: the saved parameters have no aggregation module inside that layer, and they load with `strict=True` only that way. Recent PyG rejects the argument, so it is removed. PyG's `DataParallel` now requires CUDA; a CPU stand-in that only batches the graphs is used. The package's Colab paths (`/content/…`) are replaced by a temporary folder. These changes are applied when the code is loaded; no file is modified.
> 5. **No published per-complex values.** For 1a30 our value is **4.9114** (charges from ChargeFW2 3.0.0; experimental 4.30), and repeated runs give exactly the same number.

---

## Quick demo (Windows, one click)

Double-click `demo_hacnet.bat` in this folder. It does the following:

1. Activates Miniconda.
2. Creates the `hacnet` environment if it does not exist (several minutes, PyTorch is a large download).
3. Unzips the repository (parameters) from `Funciones_Score_Tabla1\HAC-Net.zip`.
4. Checks the MD5 of `CNN_parameters.pt`.
5. Runs `test_1a30.py` with the ACC2 web service (**internet needed**). The window must end with `RESULT: PASS`.

---

## A. Installation with Miniconda (Windows)

Open an **Anaconda Prompt**.

### A1. Define the folders

```bat
set PLUGIN=C:\Users\Admin\Desktop\PROYECTO_UNIVERSIDAD\combi_lab_hub_tmp\plugins\hacnet
set SF=C:\Users\Admin\Desktop\PROYECTO_UNIVERSIDAD\sf
set CASF=C:\Users\Admin\Desktop\SOFTWARE SF\CASF-2016\CASF-2016
mkdir "%SF%"
```

### A2. Create the conda environment

```bat
conda env create -f "%PLUGIN%\environment.yml"
conda activate hacnet
python -W ignore -c "import torch, torch_geometric; from importlib.metadata import version; print('torch', torch.__version__, '| pyg', torch_geometric.__version__, '| HACNet', version('HACNet'))"
```

Expected output: `torch 2.2.2+cpu | pyg 2.5.3 | HACNet 1.4.3`.

### A3. Get the repository (pinned commit) for the trained parameters

**Option 1, with Git:**

```bat
git clone https://github.com/gregory-kyro/HAC-Net.git "%SF%\HAC-Net"
git -C "%SF%\HAC-Net" checkout def30e100ea9eeca3fafb0658823446b97e07ec2
```

**Option 2, without Git:** unzip `SOFTWARE SF\Funciones_Score_Tabla1\HAC-Net.zip`. Its content is identical to that commit. Rename `HAC-Net-HEAD` to `HAC-Net` and move it into `%SF%`.

```bat
certutil -hashfile "%SF%\HAC-Net\HACNet\parameter_files\CNN_parameters.pt" MD5
```

It must print `7a16badb6abcdbf9075aea5f69b5acdf`.

### A4. Run the installation test (needs internet for ACC2)

```bat
conda activate hacnet
python -W ignore "%PLUGIN%\test_1a30.py" --hacnet-dir "%SF%\HAC-Net" --complex "%CASF%\coreset\1a30" --charges acc2
```

Expected output (end):

```
[1] HACNet package 1.4.3 (expected 1.4.3); parameter files: MD5 OK
    PASS

Scoring 1a30 (pocket charges: acc2) ...

[2] Predicted pKd 1a30: 4.91.. (reference 4.9114 with ChargeFW2, experimental 4.30; difference 0.00..)
    PASS

RESULT: PASS
```

If ACC2 runs a different ChargeFW2 version than ours the difference may not be exactly 0; up to 0.05 is accepted. Please note the value you get: it tells us whether ACC2 and the local ChargeFW2 agree.

### A5. Use HAC-Net on CASF-2016 or your own complexes

Each complex in its own folder, with `<code>_protein.pdb` and `<code>_ligand.mol2`:

```bat
python -W ignore "%PLUGIN%\predict_hacnet.py" --hacnet-dir "%SF%\HAC-Net" -d "%CASF%\coreset" -o "%SF%\results_hacnet\predictions.csv" --charges acc2
```

Output columns: `pdbid, pKd_predicted, charges, error`. With ACC2, each complex is a round trip to the server; be considerate with large sets.

---

## B. Installation with Docker (alternative, offline)

The image includes ChargeFW2, so no web service is needed.

### B1. Build the image

```bat
cd /d "%PLUGIN%"
docker build -t combilab/hacnet:1.0 .
```

The build compiles ChargeFW2 and takes a while.

### B2. Run the installation test

```bat
docker run --rm -v "C:\Users\Admin\Desktop\SOFTWARE SF\CASF-2016\CASF-2016\coreset\1a30:/complex:ro" combilab/hacnet:1.0 python /opt/hacnet/test_1a30.py --hacnet-dir /opt/HAC-Net --complex /complex --charges chargefw2
```

It must print `[2] Predicted pKd 1a30: 4.9114 …` and `RESULT: PASS`.

### B3. Score the CASF-2016 core set

```bat
docker run --rm -v "C:\Users\Admin\Desktop\SOFTWARE SF\CASF-2016\CASF-2016\coreset:/coreset:ro" -v "C:\Users\Admin\Desktop\PROYECTO_UNIVERSIDAD\sf\results_hacnet:/data" combilab/hacnet:1.0 python /opt/hacnet/predict_hacnet.py --hacnet-dir /opt/HAC-Net -d /coreset -o /data/predictions.csv --charges chargefw2
```

---

## Troubleshooting

| Problem | Cause / fix |
|---|---|
| `TabError: inconsistent use of tabs and spaces` in `MLP.py` | Something imported the repository's `HACNet` folder instead of the PyPI package. Use `predict_hacnet.py`. |
| `Missing key(s) in state_dict: "se_block1.2.weight" …` | The repository's `CNN.py` was used (note 2). Use `predict_hacnet.py`. |
| `got an unexpected keyword argument 'aggregation'` | The package was run directly with PyG ≥ 2.3 (note 4). Use `predict_hacnet.py`. |
| `IndexError: list index out of range` in `data_parallel.py` | PyG `DataParallel` without a GPU (note 4). Use `predict_hacnet.py`. |
| Windows dialog *python.exe – No se encuentra el punto de entrada del procedimiento libintl_dgettext* (…`fontconfig-1.dll`) | `libglib` came from the Anaconda `defaults` channel and overwrote `intl-8.dll`. Run `fix_env_hacnet.bat` (installs glib 2.86.4 from conda-forge and restores libintl), or recreate the environment with the current `environment.yml`. |
| `ACC2 ...` errors, `ConnectionError` | No internet, or the ACC2 service is down. Retry later, or use Docker with `--charges chargefw2`. |
| `chargefw2 not found` | `--charges chargefw2` outside Docker: set `CHARGEFW2` to the executable, or use `--charges acc2`. |

## Uninstall

```bat
conda deactivate
conda env remove -n hacnet
rmdir /s /q "%SF%\HAC-Net"
```

---

*Prepared for CombiLabHUB (combi-lab). Tested on 21/10/2026 on Linux with Python 3.10, PyTorch 2.3.1 (CPU), PyG 2.5.3, Open Babel 3.1.1, PyMOL 3.1.0, HACNet 1.4.3 and ChargeFW2 3.0.0 (built from commit `579bf42`): 1a30 gives 4.9114, identical on repeated runs. The ACC2 web service could not be reached from the test computer, so the `--charges acc2` path is untested; on Windows, run step A4, or the demo, to confirm.*
