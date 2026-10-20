# PLANET — Installation guide (inference only)

**PLANET** (Protein-Ligand Affinity prediction NETwork) is a graph neural network. It takes two inputs: the 3D binding pocket of the protein (residues around a reference ligand) and the **2D molecular graph** of the ligand. It does not use the ligand's 3D pose. It was trained on PDBbind v2020 with three related tasks: affinity, protein–ligand contact map and intra-ligand distances. Because it does not need a docked pose, the authors also use it for fast virtual screening.

| | |
|---|---|
| Authors | ComputArtCMCG group — see the repository for the paper reference |
| Code | <https://github.com/ComputArtCMCG/PLANET>, pinned commit `2e49ae820ae9eb7427d12af1f4cbd03abeb92cdb` |
| Trained parameters | `PLANET.param`, 18.5 MB, **included in the repository**, MD5 `e9c74b412e99367865a1eeb9fbd95feb` |
| Prepared CASF-2016 core set | `core.tar.bz2`, 25 MB, **included in the repository** (285 complexes, protein `.pdb` + ligand `.sdf`), MD5 `11259e3e37635600dbcab4d50308e7d4` |
| Hardware | CPU is enough |
| Reported CASF-2016 PCC | 0.824 |

Files in this folder:

| File | Purpose |
|---|---|
| `environment.yml` | Python 3.11 + PyTorch 2.2.2 + RDKit 2023.9.5 (pip versions checked for Windows) |
| `Dockerfile` | Self-contained image (CPU-only PyTorch) |
| `predict_planet.py` | Scores a folder of complexes (one protein–ligand pair per sub-folder) with the authors' classes |
| `test_1a30.py` | Installation test with complex **1a30** |
| `demo_planet.bat` | One-click Windows demo |

> **What to know before using PLANET**
>
> 1. **Use the authors' prepared CASF-2016 files.** Several CASF-2016 `.sdf` files from PDBbind cannot be read by RDKit. For example, `1a30_ligand.sdf` fails with *"Explicit valence for atom # 6 C, 6, is greater than permitted"*. The authors ship all 285 core-set complexes already fixed in `core.tar.bz2`.
> 2. **The input format changes the prediction.** For 1a30, reading the ligand from the authors' `.sdf` gives pKd **5.8930**. Reading it from the CASF-2016 `.mol2` gives **5.6216**, even though both have the same SMILES and use the same pocket. PLANET builds its graph from RDKit atom features, which depend on how the file is parsed.
> 3. **The demo output in the repository is outdated.** `demo/result.csv` dates from September 2022, but `PLANET.param` was replaced twice afterwards (January and April 2023). Today's model gives different scores for the demo molecules, so `result.csv` cannot be used to validate an installation. Our test uses our own reference values instead.
> 4. The repository was migrated in April 2026 from Python 3.6/conda to Python 3.11/uv. The migration only touched device handling and `torch.load`, not the model.

---

## Quick demo (Windows, one click)

Double-click `demo_planet.bat` in this folder. It does the following:

1. Activates Miniconda.
2. Creates the `planet` environment if it does not exist. This takes several minutes, because PyTorch is a large download.
3. Unzips the PLANET code, parameters and prepared core set from `Funciones_Score_Tabla1\PLANET.zip`.
4. Checks the MD5 of `PLANET.param`.
5. Runs `test_1a30.py`.

The window stays open at the end so you can read the result (`RESULT: PASS`).

The default paths match our lab computer. On another computer, set `SF`, `CASF`, `ZIP` or `CONDA` in the Anaconda Prompt and run the script from there.

---

## A. Installation with Miniconda (Windows)

Requirements: Miniconda installed (`C:\Users\Admin\miniconda3`) and about 2 GB of free disk space.

All commands go in the **Anaconda Prompt (miniconda3)**.

### A1. Define the folders

```bat
set PLUGIN=C:\Users\Admin\Desktop\PROYECTO_UNIVERSIDAD\combi_lab_hub_tmp\plugins\planet
set SF=C:\Users\Admin\Desktop\PROYECTO_UNIVERSIDAD\sf
set CASF=C:\Users\Admin\Desktop\SOFTWARE SF\CASF-2016\CASF-2016
mkdir "%SF%"
```

> `set` only lasts for the current window. If you open a new Anaconda Prompt, run the three `set` lines again.

### A2. Create the conda environment

```bat
conda env create -f "%PLUGIN%\environment.yml"
conda activate planet
python -c "import torch, rdkit, numpy; print('torch', torch.__version__, '| rdkit', rdkit.__version__, '| numpy', numpy.__version__)"
```

Expected output: `torch 2.2.2+cpu | rdkit 2023.09.5 | numpy 1.26.4`. On Windows, the PyPI build of PyTorch is CPU-only.

### A3. Get the PLANET code (pinned commit)

**Option 1, with Git:**

```bat
git clone https://github.com/ComputArtCMCG/PLANET.git "%SF%\PLANET"
git -C "%SF%\PLANET" checkout 2e49ae820ae9eb7427d12af1f4cbd03abeb92cdb
```

**Option 2, without Git:** unzip `SOFTWARE SF\Funciones_Score_Tabla1\PLANET.zip`. Its content is identical to that commit. Rename the folder `PLANET-HEAD` to `PLANET` and move it into `%SF%`.

Check the parameters:

```bat
certutil -hashfile "%SF%\PLANET\PLANET.param" MD5
```

It must print `e9c74b412e99367865a1eeb9fbd95feb`.

### A4. Run the installation test (complex 1a30)

```bat
conda activate planet
python "%PLUGIN%\test_1a30.py" --planet-dir "%SF%\PLANET" --complex "%CASF%\coreset\1a30"
```

Expected result (a few seconds):

```
[1] Authors' prepared 1a30 (core.tar.bz2): pKd 5.8930 (reference 5.8930, experimental 4.30)
    PASS - matches the reference

[2] CASF-2016 1a30 (ligand from 1a30_ligand.mol2): pKd 5.6216 (reference 5.6216, experimental 4.30)
    PASS - matches the reference

RESULT: PASS
```

What each check verifies:
- `[1]` Uses 1a30 exactly as the authors prepared it, which checks the model, PyTorch and RDKit.
- `[2]` Uses the CASF-2016 files from PDBbind. The pocket comes from the CASF `.sdf` (read without sanitizing, as the authors' code does), and the ligand graph comes from the `.mol2`, because RDKit rejects that `.sdf`.

The difference between `[1]` and `[2]` is explained in note 2 above. Complex 1a30 is over-predicted by PLANET too, so 5.6–5.9 against the experimental 4.30 is the **expected** behaviour.

### A5. Use PLANET on CASF-2016 or your own complexes

**CASF-2016 (recommended input):** extract the authors' core set once, then score it:

```bat
cd /d "%SF%\PLANET"
tar -xjf core.tar.bz2
python "%PLUGIN%\predict_planet.py" --planet-dir "%SF%\PLANET" -d "%SF%\PLANET\core" -o "%SF%\results_planet\predictions.csv"
```

**Your own complexes:** put each one in its own folder with `<code>_protein.pdb` and `<code>_ligand.sdf`. Residues around this ligand form the pocket. If RDKit cannot sanitize the `.sdf`, the script reads the ligand graph from `<code>_ligand.mol2` and says so in the output column `ligand_source`.

For virtual screening (one protein, many molecules), use the authors' script:

```bat
cd /d "%SF%\PLANET\demo"
python ..\PLANET_run.py -p adrb2.pdb -l adrb2_ligand.sdf -m mols.sdf --prefix my_result
```

---

## B. Installation with Docker (alternative)

Requirements: Docker Desktop with the WSL2 backend, and internet access during the build (GitHub, Debian mirrors, conda-forge, PyPI and download.pytorch.org). The image uses CPU-only PyTorch. Steps A2–A3 are not needed.

### B1. Build the image

```bat
cd /d C:\Users\Admin\Desktop\PROYECTO_UNIVERSIDAD\combi_lab_hub_tmp\plugins\planet
docker build -t combilab/planet:1.0 .
```

The build fails on purpose if the MD5 of `PLANET.param` or `core.tar.bz2` does not match.

### B2. Run the installation test

```bat
docker run --rm -v "C:\Users\Admin\Desktop\SOFTWARE SF\CASF-2016\CASF-2016\coreset\1a30:/complex:ro" combilab/planet:1.0 python /opt/planet/test_1a30.py --planet-dir /opt/PLANET --complex /complex
```

---

## Troubleshooting

| Symptom | Cause and fix |
|---|---|
| `Explicit valence for atom ... is greater than permitted` | RDKit cannot read that `.sdf`. Use the authors' `core.tar.bz2` files, or provide a `.mol2` next to it. |
| `ValueError: need at least one array to concatenate` from `PLANET_run.py` | No molecule in the `.sdf` could be read, and the authors' script hides the reason. Check the file with RDKit, or use `predict_planet.py`. |
| `RuntimeError: the protein pdb file need to be fixed` | The protein `.pdb` has residues without an alpha carbon. The authors recommend fixing it with a preparation tool. |
| Predictions differ from the reference | Different RDKit or PyTorch version. Check A2. |

## Uninstall

```bat
conda env remove -n planet
rmdir /s /q "%SF%\PLANET"
docker rmi combilab/planet:1.0
```

The last line is only needed if you used Docker.

---
*Prepared for CombiLabHUB (combi-lab). Tested on 19/10/2026 on Linux with Python 3.11, PyTorch 2.2.2 and RDKit 2023.9.5: both checks above pass and the predictions are deterministic. All Windows packages were checked to exist for Python 3.11. On Windows, run step A4, or the demo, to confirm.*
