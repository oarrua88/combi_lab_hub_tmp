# IGModel — Installation guide (inference only)

**IGModel** predicts, with one network, both the **RMSD of a ligand pose** and the **binding affinity (pKd)**. It encodes two graphs with graph neural networks (EGAT layers): a **protein–ligand interaction graph** and a **pocket graph** (residues around the ligand), and decodes the shared latent space into RMSD and pKd.

| | |
|---|---|
| Authors | Z. Wang, S. Wang, Y. Li, J. Guo, Y. Wei, Y. Mu, L. Zheng, W. Li — *Briefings in Bioinformatics* 25(3), bbae145 (2024) |
| Code | <https://github.com/zchwang/IGModel>, pinned commit `2703fc3a1a2cf45357d990a93141ddeda7f38587` (licence MIT) |
| Trained models | `models/saved_model.pth` (crystal ligand defines the pocket), MD5 `f7f17e91249bed9c90b8a7201c4c2402`, and `models/self-ref_model.pth` (the pose defines the pocket), MD5 `a3931cd4e2d3573a60f7b00e6f645d5e`. Both **included in the repository**. |
| Hardware | CPU is enough (a few seconds per complex) |
| Reported CASF-2016 PCC | 0.831 (paper) — **Eaves et al. 2026 obtain only 0.45** ("runnable, not reproducible"; see note 2) |

Files in this folder:

| File | Purpose |
|---|---|
| `environment.yml` | Python 3.10 + PyTorch 2.2.2 + DGL 2.2.1 + RDKit 2025.09.5 + Open Babel 3.1.1 + spyrmsd 0.9.0 |
| `Dockerfile` | Self-contained image (CPU PyTorch 2.3.1 + conda-forge DGL 2.2.1) |
| `predict_igmodel.py` | Scores a folder of complexes (one per sub-folder) with the authors' featurisers and model |
| `test_1a30.py` | Installation test: the authors' 1bcu example + complex **1a30** |
| `demo_igmodel.bat` | One-click Windows demo |

> **What to know before using IGModel**
>
> 1. **Two modes, two models.** With a reference ligand (the crystal ligand) the pocket is cut around it and `saved_model.pth` is used. Without one, the pocket is cut around the pose itself and the README says to use `self-ref_model.pth`. For CASF-2016 we use the first mode: the crystal ligand is both the reference and the scored pose. For 1a30: `saved_model.pth` → **5.0653**, `self-ref_model.pth` → 5.4664 (experimental 4.30).
> 2. **Why Eaves et al. may get 0.45.** Their script (fork <https://github.com/jeavesj/IGModel>, `run_scoring.sh`) gives no reference ligand but loads `saved_model.pth`, i.e. the self-reference mode with the model meant for the reference mode. For the crystal pose of 1a30 this gives the same value as our mode (5.0653), so it is not obviously the cause; the CASF-2016 run will tell.
> 3. **Read the ligand from the `.mol2`.** RDKit cannot read the CASF-2016 `.sdf` of several complexes, 1a30 among them. The authors' script then prints only `Error: 0` and writes no output. `predict_igmodel.py` uses `<code>_ligand.mol2` (the `.sdf` only if there is no `.mol2`) and prints the real error when a complex fails.
> 4. **The model is a whole pickled network**, not a `state_dict`, so the authors' `scripts/model.py` must be importable when it is loaded. `predict_igmodel.py` takes care of this.
> 5. **No published per-complex values.** The test checks the authors' example (10 docking poses of 1bcu, values printed in their notebook `scripts/scoring-demo.ipynb`) and our own value for 1a30.

---

## Quick demo (Windows, one click)

Double-click `demo_igmodel.bat` in this folder. It does the following:

1. Activates Miniconda.
2. Creates the `igmodel` environment if it does not exist (several minutes, PyTorch is a large download).
3. Unzips the code and models from `Funciones_Score_Tabla1\IGModel.zip`.
4. Checks the MD5 of `saved_model.pth`.
5. Runs `test_1a30.py`. The window must end with `RESULT: PASS`.

---

## A. Installation with Miniconda (Windows)

Open an **Anaconda Prompt**.

### A1. Define the folders

```bat
set PLUGIN=C:\Users\Admin\Desktop\PROYECTO_UNIVERSIDAD\combi_lab_hub_tmp\plugins\igmodel
set SF=C:\Users\Admin\Desktop\PROYECTO_UNIVERSIDAD\sf
set CASF=C:\Users\Admin\Desktop\SOFTWARE SF\CASF-2016\CASF-2016
mkdir "%SF%"
```

### A2. Create the conda environment

```bat
conda env create -f "%PLUGIN%\environment.yml"
conda activate igmodel
set DGLBACKEND=pytorch
python -W ignore -c "import torch, dgl, rdkit; print('torch', torch.__version__, '| dgl', dgl.__version__, '| rdkit', rdkit.__version__)"
```

Expected output: `torch 2.2.2+cpu | dgl 2.2.1 | rdkit 2025.09.5`.

### A3. Get the IGModel code (pinned commit)

**Option 1, with Git:**

```bat
git clone https://github.com/zchwang/IGModel.git "%SF%\IGModel"
git -C "%SF%\IGModel" checkout 2703fc3a1a2cf45357d990a93141ddeda7f38587
```

**Option 2, without Git:** unzip `SOFTWARE SF\Funciones_Score_Tabla1\IGModel.zip`. Its content is identical to that commit. Rename `IGModel-HEAD` to `IGModel` and move it into `%SF%`.

Check the model:

```bat
certutil -hashfile "%SF%\IGModel\models\saved_model.pth" MD5
```

It must print `f7f17e91249bed9c90b8a7201c4c2402`.

### A4. Run the installation test

```bat
conda activate igmodel
python -W ignore "%PLUGIN%\test_1a30.py" --ig-dir "%SF%\IGModel" --complex "%CASF%\coreset\1a30"
```

Open Babel prints valence warnings for 1bcu; they are harmless (the authors' notebook shows them too). Expected output (end):

```
[1] Authors' example 1bcu: 10 poses scored (authors 10), max difference 0.000003
    PASS - matches the authors' notebook

[2] Predicted pKd 1a30: 5.0653 (reference 5.0653, experimental 4.30; predicted RMSD 1.40 A)
    PASS

RESULT: PASS
```

### A5. Use IGModel on CASF-2016 or your own complexes

Each complex in its own folder, with `<code>_protein.pdb` and `<code>_ligand.mol2` (or `.sdf`):

```bat
python -W ignore "%PLUGIN%\predict_igmodel.py" --ig-dir "%SF%\IGModel" -d "%CASF%\coreset" -o "%SF%\results_igmodel\predictions.csv"
```

Output columns: `pdbid, pKd_predicted, pred_rmsd, error`. Add `--mode self-ref` to use `self-ref_model.pth`.

To score docking poses against a crystal ligand, use the authors' script:

```bat
cd /d "%SF%\IGModel"
python scripts\scoring.py -rec_fpath samples\1bcu\1bcu_protein_atom_noHETATM.pdb -ref_lig_fpath samples\1bcu\1bcu_ligand.sdf -pose_fpath samples\1bcu\1bcu_decoys.sdf -model models\saved_model.pth -out_fpath scores.csv
```

---

## B. Installation with Docker (alternative)

### B1. Build the image

```bat
cd /d "%PLUGIN%"
docker build -t combilab/igmodel:1.0 .
```

### B2. Run the installation test

```bat
docker run --rm -v "C:\Users\Admin\Desktop\SOFTWARE SF\CASF-2016\CASF-2016\coreset\1a30:/complex:ro" combilab/igmodel:1.0 python /opt/igmodel/test_1a30.py --ig-dir /opt/IGModel --complex /complex
```

### B3. Score the CASF-2016 core set

```bat
docker run --rm -v "C:\Users\Admin\Desktop\SOFTWARE SF\CASF-2016\CASF-2016\coreset:/coreset:ro" -v "C:\Users\Admin\Desktop\PROYECTO_UNIVERSIDAD\sf\results_igmodel:/data" combilab/igmodel:1.0 python /opt/igmodel/predict_igmodel.py --ig-dir /opt/IGModel -d /coreset -o /data/predictions.csv
```

---

## Troubleshooting

| Problem | Cause / fix |
|---|---|
| The authors' `scoring.py` prints `Error: 0` and writes nothing | RDKit could not read the `.sdf` (note 3). Use the `.mol2`, or `predict_igmodel.py`. |
| `ModuleNotFoundError: No module named 'model'` when loading the `.pth` | The model was loaded without `scripts/` on the path (note 4). Use `predict_igmodel.py`. |
| `Warnning: psi feats calculate failed ...` | Printed by the authors' pocket featuriser for some residues; also in their notebook. Harmless. |
| `No module named 'torchdata.datapipes'` | torchdata ≥ 0.10 was installed. `pip install torchdata==0.7.1`. |

## Uninstall

```bat
conda deactivate
conda env remove -n igmodel
rmdir /s /q "%SF%\IGModel"
```

---

*Prepared for CombiLabHUB (combi-lab). Tested on 21/10/2026 on Linux with Python 3.10, PyTorch 2.3.1 (CPU), DGL 2.2.1, RDKit 2025.09.5 and Open Babel 3.1.1 (also 3.2.1, same values): the 10 poses of 1bcu match the authors' notebook (max difference 0.000003) and 1a30 gives 5.0653. The Windows environment was checked to solve for win-64. On Windows, run step A4, or the demo, to confirm.*
