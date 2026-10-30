# AutoDock Vina — Installation guide (score only)

**AutoDock Vina** is an empirical scoring function (Gaussian steric terms, repulsion, hydrophobic and hydrogen-bond terms, and a penalty for the rotatable bonds of the ligand). It is one of the classical scoring functions evaluated in CASF-2016. Here it only **rescores the crystal pose** of each complex (`--score_only`): no docking, no minimisation.

| | |
|---|---|
| Authors | O. Trott, A. J. Olson — *J. Comput. Chem.* 2010, 31, 455–461; Vina 1.2: J. Eberhardt et al., *J. Chem. Inf. Model.* 2021 |
| Code | <https://github.com/ccsb-scripps/AutoDock-Vina> (Apache-2.0). `AutoDock-Vina.zip` in `SOFTWARE SF\Funciones_Score_Su2018` is the current source (1.2.x), not 1.1.2 |
| Programs | **Vina 1.1.2** (bioconda `autodock-vina=1.1.2`, Linux) and the official **Vina 1.2.5** binaries of GitHub release v1.2.5: `vina_1.2.5_win.exe` (MD5 `39ff27d9b1f29b4a8e7a1f35e3186861`) and `vina_1.2.5_linux_x86_64` (MD5 `a1a5d276535db56db71f94f403b8939e`) |
| Trained model | none (empirical function, fixed weights) |
| Hardware | CPU; less than 1 s per complex |
| Reported CASF-2016 PCC | 0.604 (Su et al. 2019, scoring power; Vina 1.1.2) |
| Origin | **Lista 1**, scoring functions of Su et al. 2019 (CASF-2016), folder `Funciones_Score_Su2018` |

Files in this folder:

| File | Purpose |
|---|---|
| `environment.yml` | Python 3.10 + Open Babel 3.1.1 (Windows and Linux) |
| `environment_mgltools.yml` | MGLTools 1.5.7 (Python 2.7, Linux only), for the 1.1.2 engine |
| `Dockerfile` | Image with both engines: Vina 1.1.2 + MGLTools, and Vina 1.2.5 + Open Babel |
| `predict_autodock_vina.py` | Scores a folder of complexes (one sub-folder per complex) |
| `test_1a30.py` | Installation test with complex **1a30** |
| `demo_autodock_vina.bat` | One-click Windows demo (conda + Vina 1.2.5) |
| `docker_autodock_vina.bat` / `docker_autodock_vina.sh` | Builds the Docker image (first time) and runs the test with both engines (Windows / Linux) |

> **What to know before using Vina**
>
> 1. **Two engines.** `predict_autodock_vina.py` reads the version from `vina --version` and uses:
>    - **1.1.2** — Vina 1.1.2 with pdbqt files from MGLTools 1.5.7 (`prepare_receptor4.py`, `prepare_ligand4.py`, default options). This is the **CASF-2016 protocol**: for 1a30 it gives **−4.99866 kcal/mol, exactly** the value in `CASF-2016\power_scoring\examples\AutodockVina.dat`. Linux or Docker only: MGLTools and Vina 1.1.2 have no conda build for Windows.
>    - **1.2.5** — the official Vina 1.2.5 binary with pdbqt files from Open Babel 3.1.1 (`obabel -xr` for the receptor). It runs on **Windows**. Vina 1.2 needs a grid box even with `--score_only`, so `--autobox` (the box of the ligand) is added. For 1a30 it gives **−4.999** kcal/mol (Vina 1.2 prints 3 decimals). In 1a30 the pdbqt files of MGLTools and of Open Babel give the same score with both versions.
> 2. **Input.** One sub-folder per complex with `<code>_protein.pdb` and `<code>_ligand.mol2` (CASF-2016 / PDBbind layout). The full protein is used. MGLTools' `prepare_ligand4.py` only finds the ligand when it runs in the ligand's folder, so the files are copied to a temporary folder first.
> 3. **Units.** Vina gives a binding free energy in kcal/mol (`vina_kcal_mol` in the CSV). `pKd_predicted` = −0.73349 × score, the kcal/mol → pKd factor that ΔVinaRF20 uses for the Vina terms (Wang & Zhang 2017). CASF-2016 evaluates the raw score; the PCC is the same.
> 4. **Reference value for 1a30.** CASF-2016 gives −4.99866 kcal/mol for 1a30 (experimental pKd 4.30). `test_1a30.py` accepts a difference of up to 0.0005 with engine 1.1.2 and 0.002 with 1.2.5.

---

## Quick demo (Windows, one click)

Double-click `demo_autodock_vina.bat`. It:

1. Activates Miniconda.
2. Creates the `autodock_vina` environment if it does not exist (a few minutes).
3. Downloads `vina_1.2.5_win.exe` from the GitHub release into `%SF%\AutoDock-Vina` and shows its MD5.
4. Runs `test_1a30.py`.

The window must end with `RESULT: PASS`.

For the exact CASF-2016 protocol (Vina 1.1.2 + MGLTools), double-click `docker_autodock_vina.bat` (Docker Desktop must be running). It tests both engines.

---

## A. Installation with Miniconda (Windows)

Open an **Anaconda Prompt (miniconda3)**.

### A1. Define the folders

```bat
set PLUGIN=C:\Users\Admin\Desktop\PROYECTO_UNIVERSIDAD\combi_lab_hub_tmp\plugins\autodock_vina
set SF=C:\Users\Admin\Desktop\PROYECTO_UNIVERSIDAD\sf
set CASF=C:\Users\Admin\Desktop\SOFTWARE SF\CASF-2016\CASF-2016
mkdir "%SF%\AutoDock-Vina"
```

### A2. Create the conda environment

```bat
conda env create -f "%PLUGIN%\environment.yml"
conda activate autodock_vina
obabel -V
```

### A3. Download Vina 1.2.5

```bat
curl -L -o "%SF%\AutoDock-Vina\vina_1.2.5_win.exe" https://github.com/ccsb-scripps/AutoDock-Vina/releases/download/v1.2.5/vina_1.2.5_win.exe
certutil -hashfile "%SF%\AutoDock-Vina\vina_1.2.5_win.exe" MD5
"%SF%\AutoDock-Vina\vina_1.2.5_win.exe" --version
```

The MD5 must be `39ff27d9b1f29b4a8e7a1f35e3186861` and the version `AutoDock Vina v1.2.5`.

### A4. Test with 1a30

```bat
python "%PLUGIN%\test_1a30.py" --vina "%SF%\AutoDock-Vina\vina_1.2.5_win.exe" --complex "%CASF%\coreset\1a30"
```

Expected end of the output:

```
[3] Vina score of 1a30 (engine 1.2.5): -4.99900 kcal/mol (pKd 3.6667)
    CASF-2016 reference -4.99866, difference 0.00034 (tolerance 0.0020)
    PASS
RESULT: PASS
```

### A5. Score a folder of complexes

```bat
python "%PLUGIN%\predict_autodock_vina.py" -d <folder of complexes> -o predictions_vina.csv --vina "%SF%\AutoDock-Vina\vina_1.2.5_win.exe"
```

---

## B. Docker (Windows with Docker Desktop, or Linux)

```bat
cd /d "%PLUGIN%"
docker build -t combilab/autodock_vina:1.0 .
docker run --rm -v "%CASF%\coreset\1a30:/complex:ro" combilab/autodock_vina:1.0 python /opt/autodock_vina/test_1a30.py --vina vina --complex /complex
docker run --rm -v "%CASF%\coreset\1a30:/complex:ro" combilab/autodock_vina:1.0 python /opt/autodock_vina/test_1a30.py --vina /opt/vina125/vina --complex /complex
```

The first `docker run` uses Vina 1.1.2 + MGLTools (must give −4.99866 exactly); the second one, Vina 1.2.5 + Open Babel. `docker_autodock_vina.bat` (Windows) and `docker_autodock_vina.sh` (Linux) do the same.

To score a folder of complexes with the CASF-2016 protocol:

```bat
docker run --rm -v "<folder of complexes>:/complexes:ro" -v "%CD%:/data" combilab/autodock_vina:1.0 python /opt/autodock_vina/predict_autodock_vina.py -d /complexes -o /data/predictions_vina.csv --vina vina
```

---

## Test record

| Date | Where | Engine | 1a30 | Result |
|---|---|---|---|---|
| 30/10/2026 | Linux (development) | 1.1.2 + MGLTools 1.5.7 | −4.99866 kcal/mol (= CASF-2016) | PASS |
| 30/10/2026 | Linux (development) | 1.2.5 + Open Babel 3.1.1 | −4.999 kcal/mol | PASS |
| — | Lab PC, Windows conda | 1.2.5 | | pending |
| — | Lab PC, Docker | both | | pending |
