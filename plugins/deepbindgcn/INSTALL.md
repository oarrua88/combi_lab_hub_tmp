# DeepBindGCN — Installation guide (inference only, DeepBindGCN_RG)

**DeepBindGCN** predicts protein–ligand binding without using the docked pose. It combines a graph convolutional network on the ligand's **2D molecular graph** (built from a SMILES string) with another on a **residue graph of the pocket** (Cα atoms closer than 5 Å, with pre-computed residue vectors). The repository has two models: **DeepBindGCN_RG** (regression, predicts pKd, used here) and DeepBindGCN_BC (binder / non-binder classification).

| | |
|---|---|
| Authors | H. Zhang et al. (2023); contact hp.zhang@siat.ac.cn (from the README) |
| Code | <https://github.com/haiping1010/DeepBindGCN>, pinned commit `830a195df5be7edde2d8d6de8ff57d952532dde7` (licence Apache-2.0) |
| Trained model | `full_model_out2000_RG.model`, 34 MB, GitHub release **v1.0.0**, MD5 `aaa694546e7cf41c9d2c3417df197d17` (not in the repository) |
| Hardware | CPU is enough (well under 1 s per complex) |
| Reported CASF-2016 PCC | 0.75 (our project table). Not in Eaves et al. 2026 |

Files in this folder:

| File | Purpose |
|---|---|
| `environment.yml` | Python 3.10 + PyTorch 2.2.2 + PyTorch Geometric 2.5.3 + RDKit 2025.03.6 |
| `Dockerfile` | Self-contained image (CPU PyTorch 2.3.1 + PyG from conda-forge), downloads the model |
| `predict_deepbindgcn.py` | Scores a folder of complexes (one per sub-folder) |
| `test_1a30.py` | Installation test with complex **1a30** |
| `demo_deepbindgcn.bat` | One-click Windows demo |

> **What to know before using DeepBindGCN**
>
> 1. **The authors' scripts only work on their example folders.** They read fixed file names with `glob`, chain several shell scripts that run in the background (`nohup … &`), and need a GPU (`torch.cuda.get_device_name(0)`). `predict_deepbindgcn.py` re-implements their steps line by line for any complex: the 8 Å pocket (`pocket/extract_pocket.py`), the pocket graph (`pdb_graph` in `read_smi_protein_nnn_usage.py`), the ligand graph (`smile_to_graph` in `all_file/read_smi_protein_nnn.py`) and the forward pass of `models/gcn.py`, one complex at a time. The architecture is imported from the authors' `models/gcn.py`.
> 2. **The model needs the old graph-convolution layer — this changes the result a lot.** The model file is a whole pickled network from PyTorch Geometric 1.4. In that version `GCNConv` normalises each edge by the degree of its *source* node; current PyG uses the *target* node. The pocket graph is directed (the authors only add the pair i→j with i<j), so the two give different numbers. For 1a30: **4.4640** with the original layer, 6.4782 with the current one. `predict_deepbindgcn.py` uses an exact copy of the PyG 1.4.3 layer, checked against its source code, and loads the trained weights into it.
> 3. **Ligand as SMILES.** CASF-2016 has no SMILES. The SMILES is read from `<code>_ligand.smi` if present, otherwise generated with RDKit from `<code>_ligand.mol2` (written to the output). The 3D pose is only used to find the pocket.
> 4. **Eval mode.** The model was saved in training mode; it is switched to eval mode (no dropout), as in the authors' prediction script.
> 5. **No published per-complex values.** The 1a30 reference is ours.

---

## Quick demo (Windows, one click)

Double-click `demo_deepbindgcn.bat` in this folder. It does the following:

1. Activates Miniconda.
2. Creates the `deepbindgcn` environment if it does not exist (several minutes, PyTorch is a large download).
3. Unzips the code from `Funciones_Score_Tabla1\DeepBindGCN.zip`.
4. Downloads the trained model (34 MB) from the GitHub release and checks its MD5.
5. Runs `test_1a30.py`. The window must end with `RESULT: PASS`.

---

## A. Installation with Miniconda (Windows)

Open an **Anaconda Prompt**.

### A1. Define the folders

```bat
set PLUGIN=C:\Users\Admin\Desktop\PROYECTO_UNIVERSIDAD\combi_lab_hub_tmp\plugins\deepbindgcn
set SF=C:\Users\Admin\Desktop\PROYECTO_UNIVERSIDAD\sf
set CASF=C:\Users\Admin\Desktop\SOFTWARE SF\CASF-2016\CASF-2016
mkdir "%SF%"
```

### A2. Create the conda environment

```bat
conda env create -f "%PLUGIN%\environment.yml"
conda activate deepbindgcn
python -W ignore -c "import torch, torch_geometric, rdkit; print('torch', torch.__version__, '| pyg', torch_geometric.__version__, '| rdkit', rdkit.__version__)"
```

Expected output: `torch 2.2.2+cpu | pyg 2.5.3 | rdkit 2025.03.6`.

### A3. Get the code (pinned commit) and the trained model

**Option 1, with Git:**

```bat
git clone https://github.com/haiping1010/DeepBindGCN.git "%SF%\DeepBindGCN"
git -C "%SF%\DeepBindGCN" checkout 830a195df5be7edde2d8d6de8ff57d952532dde7
```

**Option 2, without Git:** unzip `SOFTWARE SF\Funciones_Score_Tabla1\DeepBindGCN.zip` (identical to that commit), rename `DeepBindGCN-HEAD` to `DeepBindGCN` and move it into `%SF%`.

Then the model:

```bat
set MODEL=%SF%\DeepBindGCN\DeepBindGCN_RG_example\full_model_out2000_RG.model
powershell -Command "Invoke-WebRequest -Uri 'https://github.com/haiping1010/DeepBindGCN/releases/download/v1.0.0/full_model_out2000_RG.model' -OutFile '%MODEL%'"
certutil -hashfile "%MODEL%" MD5
```

It must print `aaa694546e7cf41c9d2c3417df197d17`.

### A4. Run the installation test

```bat
conda activate deepbindgcn
python -W ignore "%PLUGIN%\test_1a30.py" --dbg-dir "%SF%\DeepBindGCN" --model "%MODEL%" --complex "%CASF%\coreset\1a30"
```

Expected output:

```
[1] Model MD5 aaa694546e7cf41c9d2c3417df197d17 (OK); OldGCNConv vs current GCNConv on a symmetric graph: max difference 0.00e+00
    PASS

[2] Predicted pKd 1a30: 4.4640 (reference 4.4640, experimental 4.30; 55 pocket residues, ligand from mol2)
    PASS

RESULT: PASS
```

### A5. Use DeepBindGCN on CASF-2016 or your own complexes

Each complex in its own folder, with `<code>_protein.pdb` and `<code>_ligand.mol2` (optionally `<code>_ligand.smi`):

```bat
python -W ignore "%PLUGIN%\predict_deepbindgcn.py" --dbg-dir "%SF%\DeepBindGCN" --model "%MODEL%" -d "%CASF%\coreset" -o "%SF%\results_deepbindgcn\predictions.csv"
```

Output columns: `pdbid, pKd_predicted, pocket_residues, ligand_source, smiles, error`.

---

## B. Installation with Docker (alternative)

### B1. Build the image

```bat
cd /d "%PLUGIN%"
docker build -t combilab/deepbindgcn:1.0 .
```

### B2. Run the installation test

```bat
docker run --rm -v "C:\Users\Admin\Desktop\SOFTWARE SF\CASF-2016\CASF-2016\coreset\1a30:/complex:ro" combilab/deepbindgcn:1.0 python -W ignore /opt/deepbindgcn/test_1a30.py --dbg-dir /opt/DeepBindGCN --model /opt/DeepBindGCN/DeepBindGCN_RG_example/full_model_out2000_RG.model --complex /complex
```

### B3. Score the CASF-2016 core set

```bat
docker run --rm -v "C:\Users\Admin\Desktop\SOFTWARE SF\CASF-2016\CASF-2016\coreset:/coreset:ro" -v "C:\Users\Admin\Desktop\PROYECTO_UNIVERSIDAD\sf\results_deepbindgcn:/data" combilab/deepbindgcn:1.0 python -W ignore /opt/deepbindgcn/predict_deepbindgcn.py --dbg-dir /opt/DeepBindGCN --model /opt/DeepBindGCN/DeepBindGCN_RG_example/full_model_out2000_RG.model -d /coreset -o /data/predictions.csv
```

---

## Troubleshooting

| Problem | Cause / fix |
|---|---|
| `AssertionError: Torch not compiled with CUDA enabled` / `get_device_name` errors | You ran the authors' `training_nn3_load_name.py`, which needs a GPU. Use `predict_deepbindgcn.py`. |
| `ModuleNotFoundError: No module named 'models'` when loading the model | The model is a pickled network: `DeepBindGCN_RG_example` must be importable. `predict_deepbindgcn.py` takes care of this. |
| The prediction for 1a30 is 6.48 | The current `GCNConv` was used instead of the PyG 1.4 layer (note 2). |
| `RDKit cannot read …_ligand.mol2` | Give the SMILES in `<code>_ligand.smi`. |

## Uninstall

```bat
conda deactivate
conda env remove -n deepbindgcn
rmdir /s /q "%SF%\DeepBindGCN"
```

---

*Prepared for CombiLabHUB (combi-lab). Tested on 21/10/2026 on Linux with Python 3.10, PyTorch 2.3.1 (CPU), PyTorch Geometric 2.5.3 and RDKit 2025.03.6: both checks pass. On Windows, run step A4, or the demo, to confirm.*
