# ConBAP — Installation guide (inference only)

**ConBAP** predicts protein–ligand binding affinity with a network that is first **pre-trained by contrastive learning** (native vs. re-docked poses of PDBbind 2020) and then fine-tuned on affinities. It combines a ligand atom graph, a pocket atom graph, a residue graph of the pocket encoded with **GVP-GNN** (geometric vector perceptrons) and a ligand–pocket interaction graph processed with an EGNN.

| | |
|---|---|
| Authors | D. Luo, D. Liu, X. Qu, L. Dong, B. Wang — *J. Chem. Inf. Model.* 64(6), 1892–1906 (2024) |
| Code | <https://github.com/ld139/ConBAP>, pinned commit `494817a5207f9bfeba681b1d239898545088789c` (licence MIT) |
| Trained models | Contrastive encoder `unsupervised/model/20240111_193210_ConBAP_repeat3/model/contrastive_no_filtered.pt` (MD5 `0048d622b60c7df895215259659d5f90`) + affinity head `supervised/model/20231007_111336_ConBAP_repeat0/model/epoch-292, ….pt` (MD5 `0256bb84bdf87fb2f0671f0acbd33358`), the pair used by the authors' `predict.py`. **Included in the repository.** |
| Extra dependency | GVP-GNN, <https://github.com/drorlab/gvp-pytorch>, commit `316eea7cd6446dd928e5975634152ec3b28e65f5`, installed without its `atom3d` dependency |
| Hardware | CPU is enough (about 1 s per complex) |
| Reported CASF-2016 PCC | 0.864 (paper) — **Eaves et al. 2026 obtain only 0.424** ("runnable, not reproducible"; see note 1) |

Files in this folder:

| File | Purpose |
|---|---|
| `environment.yml` | Python 3.10 + PyTorch 2.2.2 + PyG 2.5.3 + torch_scatter 2.1.2 + torch_cluster 1.6.3 + RDKit 2025.03.6 + PyMOL 3.1.0 + Biopython 1.85 |
| `Dockerfile` | Self-contained image (CPU PyTorch 2.3.1 + PyG from conda-forge) |
| `predict_conbap.py` | Scores a folder of complexes (one per sub-folder) with the authors' preprocessing, graphs and models |
| `test_1a30.py` | Installation test: the authors' toy-set complex 1bcu + complex **1a30** |
| `demo_conbap.bat` | One-click Windows demo |

> **What to know before using ConBAP**
>
> 1. **Read the ligand with sanitization — this is probably why Eaves et al. get 0.424.** The authors read `<code>.sdf` with RDKit's default (sanitized) reader. RDKit cannot sanitize the CASF-2016 `.sdf` of several complexes, 1a30 among them, and the Eaves et al. fork switched to `sanitize=False` for every ligand. Without sanitization RDKit does not compute implicit valences, hybridization or aromaticity, and these are ConBAP's atom features. For 1a30 we reproduce their value exactly with an unsanitized `.sdf` (**7.7406**), while the sanitized ligand from the `.mol2` gives **5.9318** (experimental 4.30). Their 285 predictions are all high (mean 7.64). `predict_conbap.py` reads the `.sdf` like the authors and falls back to the `.mol2` when RDKit cannot read it (`--ligand auto`, the default). `--ligand sdf-nosanitize` reproduces Eaves et al.
> 2. **The authors' pipeline, unchanged.** Pocket = residues within 8 Å of the ligand, cut with PyMOL after removing waters and hydrogens (`preprocessing.generate_pocket`). Graphs come from the authors' `dataset_ConBAP.mols2graphs`, which also reads the whole protein. Featurising the authors' toy-set complex 1bcu from its raw files gives exactly the same prediction as the graphs they ship pre-built (4.8575). For the 20 toy-set complexes, 19 match exactly; 3bv9 differs slightly (6.52 vs 6.36), probably from a different PyMOL version.
> 3. **GVP-GNN without atom3d.** `gvp-pytorch` lists `atom3d` as a requirement, but ConBAP does not use it and it pulls many packages. Install `gvp` with `pip install --no-deps` (step A2).
> 4. **CPU.** The authors' scripts pick the GPU if there is one; the checkpoints load on CPU without changes.

---

## Quick demo (Windows, one click)

Double-click `demo_conbap.bat` in this folder. It does the following:

1. Activates Miniconda.
2. Creates the `conbap` environment if it does not exist (several minutes, PyTorch is a large download), and installs GVP-GNN.
3. Unzips the code and models from `Funciones_Score_Tabla1\ConBAP.zip` (169 MB).
4. Checks the MD5 of the affinity model.
5. Runs `test_1a30.py`. The window must end with `RESULT: PASS`.

---

## A. Installation with Miniconda (Windows)

Open an **Anaconda Prompt**.

### A1. Define the folders

```bat
set PLUGIN=C:\Users\Admin\Desktop\PROYECTO_UNIVERSIDAD\combi_lab_hub_tmp\plugins\conbap
set SF=C:\Users\Admin\Desktop\PROYECTO_UNIVERSIDAD\sf
set CASF=C:\Users\Admin\Desktop\SOFTWARE SF\CASF-2016\CASF-2016
mkdir "%SF%"
```

### A2. Create the conda environment and install GVP-GNN

```bat
conda env create -f "%PLUGIN%\environment.yml"
conda activate conbap
pip install --no-deps "https://github.com/drorlab/gvp-pytorch/archive/316eea7cd6446dd928e5975634152ec3b28e65f5.zip"
python -W ignore -c "import torch, torch_geometric, torch_scatter, gvp, rdkit, pymol; print('torch', torch.__version__, '| pyg', torch_geometric.__version__, '| rdkit', rdkit.__version__)"
```

Expected output: `torch 2.2.2+cpu | pyg 2.5.3 | rdkit 2025.03.6`.

### A3. Get the ConBAP code (pinned commit)

**Option 1, with Git:**

```bat
git clone https://github.com/ld139/ConBAP.git "%SF%\ConBAP"
git -C "%SF%\ConBAP" checkout 494817a5207f9bfeba681b1d239898545088789c
```

**Option 2, without Git:** unzip `SOFTWARE SF\Funciones_Score_Tabla1\ConBAP.zip`. Its content is identical to that commit. Rename `ConBAP-HEAD` to `ConBAP` and move it into `%SF%`.

### A4. Run the installation test

```bat
conda activate conbap
python -W ignore "%PLUGIN%\test_1a30.py" --conbap-dir "%SF%\ConBAP" --complex "%CASF%\coreset\1a30"
```

Expected output (end):

```
[1] Toy-set 1bcu: our featurisation 4.8575, authors' pre-built graphs 4.8575 (expected 4.8575)
    PASS - same as the authors' graphs

[2] Predicted pKd 1a30: 5.9318, ligand from mol2 (reference 5.9318, experimental 4.30)
    PASS

[3] 1a30 with the .sdf NOT sanitized (Eaves et al.): 7.7406 (Eaves 7.7406)
    PASS - same as Eaves et al.

RESULT: PASS
```

### A5. Use ConBAP on CASF-2016 or your own complexes

Each complex in its own folder, with `<code>_protein.pdb` and `<code>_ligand.sdf` and/or `<code>_ligand.mol2`:

```bat
python -W ignore "%PLUGIN%\predict_conbap.py" --conbap-dir "%SF%\ConBAP" -d "%CASF%\coreset" -o "%SF%\results_conbap\predictions.csv"
```

Output columns: `pdbid, pKd_predicted, ligand_source, error`. `ligand_source` says whether the ligand came from the `.sdf` or the `.mol2`.

---

## B. Installation with Docker (alternative)

### B1. Build the image

```bat
cd /d "%PLUGIN%"
docker build -t combilab/conbap:1.0 .
```

### B2. Run the installation test

```bat
docker run --rm -v "C:\Users\Admin\Desktop\SOFTWARE SF\CASF-2016\CASF-2016\coreset\1a30:/complex:ro" combilab/conbap:1.0 python /opt/conbap/test_1a30.py --conbap-dir /opt/ConBAP --complex /complex
```

### B3. Score the CASF-2016 core set

```bat
docker run --rm -v "C:\Users\Admin\Desktop\SOFTWARE SF\CASF-2016\CASF-2016\coreset:/coreset:ro" -v "C:\Users\Admin\Desktop\PROYECTO_UNIVERSIDAD\sf\results_conbap:/data" combilab/conbap:1.0 python /opt/conbap/predict_conbap.py --conbap-dir /opt/ConBAP -d /coreset -o /data/predictions.csv
```

---

## Troubleshooting

| Problem | Cause / fix |
|---|---|
| `ModuleNotFoundError: No module named 'gvp'` | Step A2, install GVP-GNN. |
| `pip` tries to install `atom3d` | GVP-GNN was installed without `--no-deps` (note 3). Uninstall and repeat step A2. |
| `No module named 'torch_scatter'` / `'torch_cluster'` | The PyG wheels did not install. `pip install torch_scatter==2.1.2 torch_cluster==1.6.3 -f https://data.pyg.org/whl/torch-2.2.0+cpu.html` |
| `Unable to process ligand of ...` with the authors' scripts | RDKit cannot read that `.sdf` (note 1). Use `predict_conbap.py`. |
| Predictions around 7–9 for everything | The ligand was read without sanitization (note 1). |

## Uninstall

```bat
conda deactivate
conda env remove -n conbap
rmdir /s /q "%SF%\ConBAP"
```

---

*Prepared for CombiLabHUB (combi-lab). Tested on 21/10/2026 on Linux with Python 3.10, PyTorch 2.3.1 (CPU), PyG 2.5.3, torch_scatter 2.1.2, torch_cluster 1.6.3, RDKit 2025.03.6, PyMOL 3.1.0 and Biopython 1.85: all three checks pass. The conda part of the Windows environment was checked to solve for win-64; the PyG wheels for torch 2.2 + CPU on Windows come from data.pyg.org. On Windows, run step A4, or the demo, to confirm.*
