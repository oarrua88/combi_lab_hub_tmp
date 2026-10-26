# DTITR — Installation guide (inference only)

**DTITR** predicts drug–target binding affinity (pKd) **from sequences only**: two Transformer encoders read the **protein sequence** (subword/BPE tokens) and the **ligand SMILES** (character tokens), a cross-attention Transformer block exchanges information between them and an MLP gives the pKd. It does **not** use the 3D structure of the complex.

| | |
|---|---|
| Authors | N. R. C. Monteiro, J. L. Oliveira, J. P. Arrais — *Comput. Biol. Med.* 147, 105772, 2022, <https://doi.org/10.1016/j.compbiomed.2022.105772> |
| Code | <https://github.com/larngroup/DTITR>, pinned commit `e8d53619a5351bbc8ee992041c91bf014629aa89` |
| Trained model | `model/dtitr_model/` (TensorFlow checkpoint, 54 MB, **included in the repository**): `.data-00000-of-00001` MD5 `69c9aca0c415bb54c63a1c01c3a8da4e`, `.index` MD5 `a30a97cc47db04b22f908191a329e298` |
| Training data | **Davis kinase dataset only** (kinases × 68 inhibitors, 29,187 pairs in the repository's processed file; non-binders set to pKd 5.0) |
| Hardware | CPU is enough |
| Reported results | Davis test set only. **No PDBbind / CASF-2016 result published** |
| Origin | **Lista 2** of CombiLabHUB (systematic review of Transformer models, `Apresentação.pdf`, slides 22–23), Level 2 |

Files in this folder:

| File | Purpose |
|---|---|
| `environment.yml` | Python 3.9 + TensorFlow 2.6.0 CPU + tensorflow-addons 0.14 + subword-nmt + RDKit |
| `Dockerfile` | Self-contained image (same versions), code and model with MD5 checks |
| `predict_dtitr.py` | Builds sequence + SMILES of each complex from the CASF-2016 files and scores them |
| `test_1a30.py` | Installation test (encoding vs the authors', Davis check, complex **1a30**) |
| `demo_dtitr.bat` | One-click Windows demo (conda) |
| `docker_dtitr.bat` / `docker_dtitr.sh` | Builds the Docker image (first time) and runs the test (Windows / Linux) |

> **What to know before using DTITR**
>
> 1. **Out of domain on CASF-2016.** The only trained model was fitted on Davis kinases with kinase inhibitors. CASF-2016 has proteases, nuclear receptors, carbonic anhydrases… and peptide-like ligands. Expect many predictions close to **5.0, the Davis "non-binder" value** (1a30 gives 5.0047). Low correlation on CASF-2016 would be a property of the published model, not an installation problem.
> 2. **Inputs built by CombiLabHUB** (the authors start from a CSV with sequence and SMILES):
>    - **protein:** one letter per standard residue of `<code>_protein.pdb` (ATOM records, **all chains in file order, concatenated**; Davis proteins are single chains). Non-standard residues are skipped: with them the authors' BPE lookup fails and zeroes the whole sequence.
>    - **ligand:** `<code>_ligand.mol2` (or `.sdf`) read by RDKit, hydrogens removed, **charges neutralised** (RDKit Uncharger: the 69 Davis SMILES are all neutral, PDBbind files carry `[NH3+]`, `[O-]`…), canonical SMILES **without stereochemistry**, as in `davis_dataset_processed.csv`.
>    - **encoding:** the authors' own rules (protein BPE, 556 subwords; SMILES with the 26-symbol Davis dictionary, 72 symbols; regression tokens in front). `test_1a30.py` checks it is **identical** to the authors' `dataset_builder` for all 29,187 Davis pairs.
> 3. **Two fixes where the authors' code would stop with an error** (molecules outside Davis): SMILES symbols missing from the Davis dictionary (e.g. `P`, `B`, `+`, `.`) become token 0 (padding), and SMILES longer than 72 symbols are truncated. Every case is listed in `predictions_notes.csv`.
> 4. **Versions.** The authors used TensorFlow 2.6.0 with GPU; the CPU build of 2.6.0 loads the checkpoint and reproduces their Davis evaluation exactly (MSE 0.1920, RMSE 0.4382, CI 0.9065, R² 0.7712, Spearman 0.7122 — `test_1a30.py --full-davis`). The authors' `dtitr_model.py` crashes without a GPU (`physical_devices[0]`); the wrapper does not use that block.
> 5. **Reference value for 1a30** (own value, 24/10/2026): `REF_PKD = 5.0047` (experimental 4.30).

---

## Quick demo (Windows, one click)

Double-click `demo_dtitr.bat`. It activates Miniconda, creates the `dtitr` environment (several minutes the first time), downloads the code at the pinned commit (GitHub zip, about 80 MB, with the model), shows the model MD5 and runs `test_1a30.py`.

On another computer, set `SF`, `CASF` or `CONDA` in the Anaconda Prompt first.

---

## A. Installation with Miniconda (Windows)

```bat
set PLUGIN=C:\Users\Admin\Desktop\PROYECTO_UNIVERSIDAD\combi_lab_hub_tmp\plugins\dtitr
set SF=C:\Users\Admin\Desktop\PROYECTO_UNIVERSIDAD\sf
set CASF=C:\Users\Admin\Desktop\SOFTWARE SF\CASF-2016\CASF-2016
```

### A1. Environment

```bat
conda env create -f "%PLUGIN%\environment.yml"
conda activate dtitr
python -c "import tensorflow as tf, tensorflow_addons, rdkit; print(tf.__version__, rdkit.__version__)"
```

Expected: `2.6.0 2022.09.5`.

### A2. Code and model (pinned commit)

```bat
git clone https://github.com/larngroup/DTITR.git "%SF%\DTITR"
git -C "%SF%\DTITR" checkout e8d53619a5351bbc8ee992041c91bf014629aa89
certutil -hashfile "%SF%\DTITR\model\dtitr_model\.data-00000-of-00001" MD5
```

The MD5 must be `69c9aca0c415bb54c63a1c01c3a8da4e`. Without Git, download `https://github.com/larngroup/DTITR/archive/e8d53619a5351bbc8ee992041c91bf014629aa89.zip`, unzip it and rename the folder to `DTITR`.

### A3. Installation test (complex 1a30)

```bat
python "%PLUGIN%\test_1a30.py" --dtitr-dir "%SF%\DTITR" --complex "%CASF%\coreset\1a30"
```

Expected (1–2 minutes; add `--full-davis` to also run the authors' whole Davis test set, a few more minutes):

```
[1] Model ...\model\dtitr_model
    PASS - MD5 69c9aca0c415bb54c63a1c01c3a8da4e, a30a97cc47db04b22f908191a329e298

[2] Encoding of the 29187 Davis pairs (protein 557, SMILES 73 tokens) vs the authors' dataset_builder
    PASS - identical

[3] Davis test set, first 5 pairs: predicted [5.3902, 5.0025, 6.1794, 5.0338, 5.0109]
    reference [5.3902, 5.0025, 6.1794, 5.0338, 5.0109], experimental [5.3565, 5.0, 6.041, 5.0, 5.0]
    PASS - model loads and matches the reference

[4] 1a30 from the CASF-2016 files: sequence 198 residues, SMILES CC(C)CC(NC(=O)C(CC(=O)O)NC(=O)C(N)CCC(=O)O)C(=O)O
    notes: ligand neutralised
    inputs PASS
    pKd 5.0047 (experimental 4.30) vs CombiLabHUB reference 5.0047
    PASS - matches the reference
    (DTITR was trained only on Davis kinases; ~5.0 is its 'non-binder' value)

RESULT: PASS
```

### A4. Your own complexes

```bat
python "%PLUGIN%\predict_dtitr.py" --dtitr-dir "%SF%\DTITR" -d <folder> -o "%SF%\results_dtitr\predictions.csv"
```

Each complex in its own sub-folder with `<code>_protein.pdb` and `<code>_ligand.mol2` (or `.sdf`). Output: `predictions.csv` (`pdbid, pKd_predicted`) and `predictions_notes.csv` (sequence length, SMILES used and warnings per complex).

---

## B. Installation with Docker (alternative)

Double-click `docker_dtitr.bat`, or:

```bat
cd /d C:\Users\Admin\Desktop\PROYECTO_UNIVERSIDAD\combi_lab_hub_tmp\plugins\dtitr
docker build -t combilab/dtitr:1.0 .
docker run --rm -v "C:\Users\Admin\Desktop\SOFTWARE SF\CASF-2016\CASF-2016\coreset\1a30:/complex:ro" combilab/dtitr:1.0 python /opt/dtitr/test_1a30.py --dtitr-dir /opt/DTITR --complex /complex
```

The build fails on purpose if the MD5 of the model does not match.

---

## Troubleshooting

| Symptom | Cause and fix |
|---|---|
| `IndexError: list index out of range` in `dtitr_model.py` | You ran the authors' script directly without a GPU. Use `predict_dtitr.py` / `test_1a30.py`. |
| `[2] FAIL - differs` | Different `subword-nmt` or `pandas`. Recreate the environment from `environment.yml`. |
| `[1] FAIL - missing` | The model files start with a dot (`.data-00000-of-00001`, `.index`); some unzip tools hide or skip them. Use `tar -xf` or `git clone`. |
| `TypeError` about `typeguard` when importing tensorflow_addons | `typeguard` 3 or newer. Install `typeguard==2.13.3`. |
| Many complexes with notes `SMILES ... truncated` | Long ligands (peptides): the model only accepts 72 SMILES symbols. Expected. |

## Uninstall

```bat
conda env remove -n dtitr
rmdir /s /q "%SF%\DTITR"
docker rmi combilab/dtitr:1.0
```

---
*Prepared for CombiLabHUB (combi-lab) on 24/10/2026. Tested on 24/10/2026 on Linux with the versions of `environment.yml` (TensorFlow 2.6.0 CPU): encoding identical to the authors', their Davis evaluation reproduced, 1a30 test PASS (pKd 5.0047). Pending: test on the lab computer (Windows conda and Docker).*
