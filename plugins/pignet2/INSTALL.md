# PIGNet2 — Installation guide (inference only)

**PIGNet2** is a physics-informed graph neural network. It predicts the binding free energy of a protein–ligand complex (kcal/mol) as the sum of four physics-like terms: van der Waals, hydrogen bond, metal–ligand and hydrophobic. It uses the ligand and the pocket (protein residues within 5 Å of the ligand). The authors convert energy to pKd with **pKd = energy / −1.36**.

| | |
|---|---|
| Authors | S. Moon, S.-Y. Hwang, J. Lim, W. Y. Kim — *Digital Discovery* 2024, 3, 287–299 |
| Code | <https://github.com/ACE-KAIST/PIGNet2>, pinned commit `f621aaaa9fe781e67763c8adbffff6faca6db95b` (licence MIT) |
| Trained models | Four checkpoints (trained with positive and negative data augmentation, the paper's best setting) **included in the repository**, in `src/ckpt/pda_{0,1,2,3}.pt`. MD5: pda_0 `5d0f378dc68caee224502348513b6f8f`, pda_1 `e5392f8dedcb05de4b8d45ad1bdf8592`, pda_2 `4ff275ddcaf2b02a99197979f846c35d`, pda_3 `e5ec13dcf8dadf8c5629cb43986cfdd2` |
| Authors' prepared data | `CASF-2016_scoring.tar.xz` on Zenodo (10.5281/zenodo.8091220, 0.6 MB, MD5 `2373a301dba79e90a985ea48341ed50c`). It holds the 285 CASF-2016 complexes already prepared as RDKit molecules. It is **not needed** to run PIGNet2; we only used it to validate our preparation. |
| Hardware | CPU is enough (well under 1 s per complex). It was placed in Level 3 for its GPU-oriented requirements (CUDA 11.1), but no GPU is needed for inference. |
| Reported CASF-2016 PCC | 0.747 (paper, 4-model ensemble). Eaves et al. 2026 obtained 0.505 ("runnable, not reproducible") |
| **Our check** | With the authors' prepared 285 complexes: PCC **0.751 / 0.714 / 0.742 / 0.710** (pda_0..3) and **0.7467** for the mean of the four, the value of the paper |

Files in this folder:

| File | Purpose |
|---|---|
| `environment.yml` | Environment `pignet2`: Python 3.9 + PyTorch 2.2.2 CPU + PyG 2.0.3 + torch_scatter/torch_sparse + RDKit 2022.03.4 + PyMOL + Open Babel + Dimorphite-DL |
| `Dockerfile` | Self-contained image (CPU PyTorch 2.3.1) |
| `predict_pignet2.py` | Scores a folder of complexes (one per sub-folder) with the authors' functions |
| `test_1a30.py` | Installation test with complex **1a30** |
| `demo_pignet2.bat` | One-click Windows demo (conda) |
| `docker_pignet2.bat` / `docker_pignet2.sh` | Docker test on Windows / Linux |

> **What to know before using PIGNet2**
>
> 1. **The ligand is read from the `.mol2`, with its hydrogens.** The CASF-2016 `_ligand.sdf` files do not pass RDKit sanitization (1a30 fails), so the wrapper uses `_ligand.mol2`. CASF ligands are already protonated: our 1a30 ligand is the same molecule as the authors' prepared one (same SMILES, charge −2). For other ligands, `--protonate-ligand` re-protonates at pH 7.4 with Dimorphite-DL, as the authors' `predict.py` does.
> 2. **The pocket is made with the authors' code.** `generate_data.extract()` uses PyMOL to keep the residues within 5 Å of the ligand and removes the hydrogens. For 1a30, our pocket (160 atoms) is identical to the authors' one: same atoms, charges and coordinates.
> 3. **`reduce` is not needed.** The authors' `predict.py` re-protonates the protein with the program `reduce`, which has no conda or Windows package. Because the pocket keeps no hydrogens, the result is the same without it (checked for 1a30: identical energies). `--protonate-protein` uses it if it is in the PATH.
> 4. **Four models, one answer.** `predict_pignet2.py` reports the **mean pKd of the four models** as `pKd_predicted` (the paper's ensemble), and also writes each model's pKd and energy. `--model 0` runs a single one.
> 5. **PyG 2.0.3 is required.** The authors' code reads `Data.keys` as a property; PyG 2.4 and later turned it into a method (`TypeError: 'method' object is not iterable`). PyG 2.0.3 also needs `torch_sparse`.
> 6. **PIGNet2 predicts low values.** For 1a30 the four models give pKd 1.94–2.26 against an experimental 4.30. Its strength is ranking (PCC), not the absolute value.

---

## Quick demo (Windows, one click)

Double-click `demo_pignet2.bat` in this folder. It does the following:

1. Activates Miniconda.
2. Creates the `pignet2` environment if it does not exist. This takes several minutes.
3. Unzips the PIGNet2 code and checkpoints from `Funciones_Score_Tabla1\PIGNet2.zip`.
4. Checks the MD5 of the pda_0 checkpoint.
5. Runs `test_1a30.py`.

The window stays open at the end so you can read the result (`RESULT: PASS`).

The default paths match our lab computer. On another computer, set `SF`, `CASF`, `ZIP` or `CONDA` in the Anaconda Prompt and run the script from there.

---

## A. Installation with Miniconda (Windows)

Requirements: Miniconda installed (`C:\Users\Admin\miniconda3`) and about 2 GB of free disk space.

All commands go in the **Anaconda Prompt (miniconda3)**.

### A1. Define the folders

```bat
set PLUGIN=C:\Users\Admin\Desktop\PROYECTO_UNIVERSIDAD\combi_lab_hub_tmp\plugins\pignet2
set SF=C:\Users\Admin\Desktop\PROYECTO_UNIVERSIDAD\sf
set CASF=C:\Users\Admin\Desktop\SOFTWARE SF\CASF-2016\CASF-2016
mkdir "%SF%"
```

> `set` only lasts for the current window. If you open a new Anaconda Prompt, run the three `set` lines again.

### A2. Create the conda environment

```bat
conda env create -f "%PLUGIN%\environment.yml"
conda activate pignet2
python -W ignore -c "import torch, torch_geometric, torch_scatter, torch_sparse, rdkit, pymol, dimorphite_dl; print('torch', torch.__version__, '| pyg', torch_geometric.__version__, '| rdkit', rdkit.__version__)"
```

Expected output: `torch 2.2.2+cpu | pyg 2.0.3 | rdkit 2022.03.4`.

### A3. Get the PIGNet2 code (pinned commit)

**Option 1, with Git:**

```bat
git clone https://github.com/ACE-KAIST/PIGNet2.git "%SF%\PIGNet2"
git -C "%SF%\PIGNet2" checkout f621aaaa9fe781e67763c8adbffff6faca6db95b
```

**Option 2, without Git:** unzip `SOFTWARE SF\Funciones_Score_Tabla1\PIGNet2.zip`. Its content is identical to that commit. Rename the folder `PIGNet2-HEAD` to `PIGNet2` and move it into `%SF%`.

Check the checkpoints:

```bat
cd /d "%SF%\PIGNet2\src\ckpt"
for %F in (pda_*.pt) do certutil -hashfile "%F" MD5
```

The four values must be the ones in the table at the top.

### A4. Run the installation test (complex 1a30)

```bat
conda activate pignet2
python -W ignore "%PLUGIN%\test_1a30.py" --pignet2-dir "%SF%\PIGNet2" --complex "%CASF%\coreset\1a30"
```

Expected result (a few seconds):

```
[1] 1a30: ligand 26 heavy atoms (charge -2), pocket 160 heavy atoms
    PASS - same as the authors' prepared 1a30

[2] Trained models (experimental pKd 4.30):
    model pda_0: -2.865 kcal/mol (reference -2.865) -> pKd 2.1063 PASS
    model pda_1: -2.897 kcal/mol (reference -2.897) -> pKd 2.1299 PASS
    model pda_2: -3.068 kcal/mol (reference -3.068) -> pKd 2.2557 PASS
    model pda_3: -2.637 kcal/mol (reference -2.637) -> pKd 1.9390 PASS
    mean       : pKd 2.1077 (reference 2.1077)

RESULT: PASS
```

What each check verifies:
- `[1]` RDKit and PyMOL prepare 1a30 as the authors did.
- `[2]` The four trained models, PyTorch and PyG give the energies that the authors' own `test.py` gives with their prepared 1a30.

### A5. Use PIGNet2 on CASF-2016 or your own complexes

**CASF-2016 core set (285 complexes):**

```bat
python -W ignore "%PLUGIN%\predict_pignet2.py" --pignet2-dir "%SF%\PIGNet2" -d "%CASF%\coreset" -o "%SF%\results_pignet2\predictions.csv"
```

The output CSV has `pdbid, pKd_predicted` (the mean of the four models), `pKd_model0..3` and `energy_model0..3` (kcal/mol).

**Your own complexes:** put each one in its own folder with `<code>_protein.pdb` and `<code>_ligand.mol2`. Add `--protonate-ligand` if the ligand is not protonated. The authors recommend SMINA-optimized poses.

---

## B. Installation with Docker (alternative)

Requirements: Docker Desktop with the WSL2 backend, and internet access during the build (Docker Hub, GitHub, Debian mirrors, conda-forge and PyPI). Steps A2–A3 are not needed. `docker_pignet2.bat` (Windows) or `docker_pignet2.sh` (Linux) do B1 and B2 in one step.

### B1. Build the image

```bat
cd /d C:\Users\Admin\Desktop\PROYECTO_UNIVERSIDAD\combi_lab_hub_tmp\plugins\pignet2
docker build -t combilab/pignet2:1.0 .
```

The build fails on purpose if the MD5 of a checkpoint does not match.

### B2. Run the installation test

```bat
docker run --rm -v "C:\Users\Admin\Desktop\SOFTWARE SF\CASF-2016\CASF-2016\coreset\1a30:/complex:ro" combilab/pignet2:1.0 python -W ignore /opt/pignet2/test_1a30.py --pignet2-dir /opt/PIGNet2 --complex /complex
```

### B3. Score the CASF-2016 core set

```bat
docker run --rm -v "C:\Users\Admin\Desktop\SOFTWARE SF\CASF-2016\CASF-2016\coreset:/coreset:ro" -v "C:\Users\Admin\Desktop\PROYECTO_UNIVERSIDAD\sf\results_pignet2:/data" combilab/pignet2:1.0 python -W ignore /opt/pignet2/predict_pignet2.py --pignet2-dir /opt/PIGNet2 -d /coreset -o /data/predictions.csv
```

---

## Troubleshooting

| Symptom | Cause and fix |
|---|---|
| `TypeError: 'method' object is not iterable` | PyG 2.4 or later is installed. Use `torch_geometric==2.0.3` (A2). |
| `No module named 'torch_sparse'` | PyG 2.0.3 needs it. Install it from `https://data.pyg.org/whl/torch-2.2.0+cpu.html`, as in `environment.yml`. |
| `RDKit cannot read <code>_ligand.mol2` | Unusual valences in the `.mol2`. Check the file. |
| `pocket extraction failed` | No protein atom within 5 Å of the ligand. Check that both files belong to the same complex. |
| `--protonate-protein needs the program 'reduce'` | `reduce` (github.com/rlabduke/reduce) is not installed. It is not needed for CASF-2016. |
| Energies differ from the reference | Different RDKit, PyMOL or PyG version. Check A2. |

## Uninstall

```bat
conda env remove -n pignet2
rmdir /s /q "%SF%\PIGNet2"
docker rmi combilab/pignet2:1.0
```

The last line is only needed if you used Docker.

---
*Prepared for CombiLabHUB (combi-lab). Tested on 22/10/2026 on Linux with Python 3.9, PyTorch 2.3.1 (CPU, conda-forge), PyG 2.0.3, RDKit 2022.03.4, PyMOL 2.5.0 and Dimorphite-DL 1.3.2: the 1a30 test passes, our 1a30 is identical to the authors' one, and the authors' 285 prepared CASF-2016 complexes give PCC 0.7467. The authors' `examples/case1` also gives their value (−3.990 kcal/mol with pda_0). All Windows packages in `environment.yml` exist for Python 3.9. The Docker image could not be built on the test machine (no access to Docker Hub): on Windows, run the demo and `docker_pignet2.bat` to confirm.*
