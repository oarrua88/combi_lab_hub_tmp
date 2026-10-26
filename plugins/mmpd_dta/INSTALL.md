# MMPD-DTA — Installation guide (inference only)

**MMPD-DTA** predicts protein–ligand binding affinity from three inputs: the **full protein sequence** (Transformer encoder), the **2D graph of the ligand** (GIN) and a **pocket–drug graph** (GraphSAGE) made of the pocket atoms and the ligand atoms. The three embeddings are concatenated and an MLP gives the pKd.

| | |
|---|---|
| Authors | G. Wang, H. Zhang, M. Shao, S. Sun, C. Cao — *J. Chem. Inf. Model.* 65(3), 1615–1630, 2025, <https://doi.org/10.1021/acs.jcim.4c01528> |
| Code | <https://github.com/zhc-moushang/MMPD-DTA>, pinned commit `69926361c8155fdd40ea2aef7df0aa3fd7de1353` |
| Trained model | `result/best/best_model.pt`, 4 MB, **included in the repository**, MD5 `366d95ccc2f7fdf87ae70746cb03ce39` |
| Authors' test sets | `data/processed/data.zip` (graphs already built): `test2016.pt` = PDBbind2016 core set (285, includes 1a30), MD5 `a1e8f977283476ec8b301aa444e493ac` |
| Hardware | CPU is enough |
| Reported PCC (PDBbind2016 test set) | **0.850** (`result/best/result.txt` in the repository: CORR 0.8498) |
| Origin | **Lista 2** of CombiLabHUB (systematic review of Transformer models, `Apresentação.pdf`, slides 22–23) — *selected* in the review |

Files in this folder:

| File | Purpose |
|---|---|
| `environment.yml` | Python 3.10 + PyTorch 2.2.2 + PyG 2.5.3 + RDKit 2023.09.6 |
| `Dockerfile` | Self-contained image (CPU PyTorch 2.3.1 + PyG 2.5.3), code, model and `test2016.pt` with MD5 checks |
| `predict_mmpd_dta.py` | Builds the inputs of each complex from the raw files and scores them |
| `test_1a30.py` | Installation test with complex **1a30** |
| `demo_mmpd_dta.bat` | One-click Windows demo (conda) |
| `docker_mmpd_dta.bat` / `docker_mmpd_dta.sh` | Builds the Docker image (first time) and runs the test (Windows / Linux) |

> **What to know before using MMPD-DTA**
>
> 1. **The authors do not publish how to build the inputs of a new complex** — only their test sets already converted to graphs. CombiLabHUB rebuilds them (`build_inputs` in `predict_mmpd_dta.py`) with the atom featuriser of the same authors (`create_data.py` of their DeepTGIN repository, deleted there on 24/01/2025, recovered from the git history) and the rules found by reading the authors' `test2016.pt`:
>    - **ligand graph:** `<code>_ligand.mol2` read by RDKit (hydrogens removed), 108 atom features divided by their sum, bonds in both directions;
>    - **pocket–drug graph:** heavy atoms of `<code>_pocket.pdb` **without waters**, then the ligand atoms; covalent bonds of both (both directions) plus **one edge pocket atom → ligand atom for every pair closer than 6.0 Å**;
>    - **protein:** one letter per residue of `<code>_protein.pdb` (ATOM records, chains in file order), dictionary `ABCDEFGHIKLMNOPQRSTUVWXYZ` → 1…25, padded to 1000.
>
>    For **1a30 the rebuilt inputs are bit-identical** to the authors' ones (383/26 nodes, 1367/50 edges in the same order, 198-residue sequence); `test_1a30.py` checks it every time.
> 2. **RDKit version matters** for the atom features (implicit valence, hybridization). 2023.09.6 reproduces the authors' graphs; keep it.
> 3. **Non-standard residues** in the protein become `X`. The authors' choice for them is unknown (1a30 has none).
> 4. **Versions.** The authors used PyTorch 1.12 + PyG 2.1 (CUDA 11.6). The state_dict loads unchanged with PyTorch 2.2/2.3 + PyG 2.5.3 on CPU. It is loaded with `torch.load(..., weights_only=True)`. The authors' `test.py` forces `cuda`; the wrapper does not use it.
> 5. **Reference value for 1a30.** The authors only publish metrics for the whole set, not per complex. The reference `REF_PKD = 5.3879` (experimental 4.30) was recorded on 23/10/2026 and is identical with Windows conda and Docker.

---

## Quick demo (Windows, one click)

Double-click `demo_mmpd_dta.bat`. It activates Miniconda, creates the `mmpd_dta` environment (several minutes the first time), downloads the code at the pinned commit (GitHub zip, about 22 MB, with the model), extracts `test2016.pt` from `data.zip`, shows the model MD5 and runs `test_1a30.py`.

On another computer, set `SF`, `CASF` or `CONDA` in the Anaconda Prompt first.

---

## A. Installation with Miniconda (Windows)

```bat
set PLUGIN=C:\Users\Admin\Desktop\PROYECTO_UNIVERSIDAD\combi_lab_hub_tmp\plugins\mmpd_dta
set SF=C:\Users\Admin\Desktop\PROYECTO_UNIVERSIDAD\sf
set CASF=C:\Users\Admin\Desktop\SOFTWARE SF\CASF-2016\CASF-2016
```

### A1. Environment

```bat
conda env create -f "%PLUGIN%\environment.yml"
conda activate mmpd_dta
python -c "import torch, torch_geometric, rdkit; print(torch.__version__, torch_geometric.__version__, rdkit.__version__)"
```

Expected: `2.2.2+cpu 2.5.3 2023.09.6`.

### A2. Code and model (pinned commit)

```bat
git clone https://github.com/zhc-moushang/MMPD-DTA.git "%SF%\MMPD-DTA"
git -C "%SF%\MMPD-DTA" checkout 69926361c8155fdd40ea2aef7df0aa3fd7de1353
tar -xf "%SF%\MMPD-DTA\data\processed\data.zip" -C "%SF%\MMPD-DTA\data\processed" test2016.pt
certutil -hashfile "%SF%\MMPD-DTA\result\best\best_model.pt" MD5
```

The MD5 must be `366d95ccc2f7fdf87ae70746cb03ce39`. Without Git, download `https://github.com/zhc-moushang/MMPD-DTA/archive/69926361c8155fdd40ea2aef7df0aa3fd7de1353.zip`, unzip it and rename the folder to `MMPD-DTA`.

### A3. Installation test (complex 1a30)

```bat
python "%PLUGIN%\test_1a30.py" --mmpd-dir "%SF%\MMPD-DTA" --complex "%CASF%\coreset\1a30"
```

Expected (a few seconds):

```
[1] Model ...\best_model.pt
    PASS - MD5 366d95ccc2f7fdf87ae70746cb03ce39

[2] Inputs rebuilt from the CASF-2016 files: complex graph 383 nodes / 1367 edges, ligand graph 26 nodes / 50 edges, sequence 198 residues
    PASS - identical to the authors' 1a30 in test2016.pt

[3] Prediction with the rebuilt inputs: pKd 5.3879 (experimental 4.30)
    with the authors' inputs:          pKd 5.3879
    PASS

[4] pKd 5.3879 vs CombiLabHUB reference 5.3879
    PASS - matches the reference

RESULT: PASS
```

### A4. Your own complexes

```bat
python "%PLUGIN%\predict_mmpd_dta.py" --mmpd-dir "%SF%\MMPD-DTA" -d <folder> -o "%SF%\results_mmpd_dta\predictions.csv"
```

Each complex in its own sub-folder with `<code>_protein.pdb`, `<code>_pocket.pdb` and `<code>_ligand.mol2`. Output: `pdbid, pKd_predicted`.

---

## B. Installation with Docker (alternative)

Double-click `docker_mmpd_dta.bat`, or:

```bat
cd /d C:\Users\Admin\Desktop\PROYECTO_UNIVERSIDAD\combi_lab_hub_tmp\plugins\mmpd_dta
docker build -t combilab/mmpd_dta:1.0 .
docker run --rm -v "C:\Users\Admin\Desktop\SOFTWARE SF\CASF-2016\CASF-2016\coreset\1a30:/complex:ro" combilab/mmpd_dta:1.0 python /opt/mmpd_dta/test_1a30.py --mmpd-dir /opt/MMPD-DTA --complex /complex
```

The build fails on purpose if the MD5 of the model or of `test2016.pt` does not match.

---

## Troubleshooting

| Symptom | Cause and fix |
|---|---|
| `[2] FAIL - differs from the authors' graphs` | Different RDKit version. Recreate the environment from `environment.yml` (RDKit 2023.09.6). |
| `[2] FAIL - authors' test2016.pt not found` | Extract it from `data\processed\data.zip` (step A2). |
| `RDKit cannot read ...` | The `.mol2` of the ligand or the pocket `.pdb` cannot be parsed. Check the file. |
| `Error(s) in loading state_dict` | PyG version very different from 2.5.3. Use `environment.yml`. |

## Uninstall

```bat
conda env remove -n mmpd_dta
rmdir /s /q "%SF%\MMPD-DTA"
docker rmi combilab/mmpd_dta:1.0
```

---
*Prepared for CombiLabHUB (combi-lab) on 23/10/2026. Tested on 23/10/2026 on the lab computer: 1a30 test PASS with Windows + conda (PyTorch 2.2.2, PyG 2.5.3, RDKit 2023.09.6) and with Docker (`combilab/mmpd_dta:1.0`, PyTorch 2.3.1 CPU): rebuilt inputs identical to the authors' and pKd 5.3879 in both.*
