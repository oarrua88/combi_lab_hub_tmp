# CombiLabHUB

CombiLabHUB (combi-lab) runs published protein–ligand **scoring functions (SF)** with their
**already trained models** (inference only, no retraining) and evaluates them on the
**CASF-2016** benchmark (core set, 285 complexes).

Each SF is a *plugin*: a folder with a reproducible environment, an install guide, a batch
prediction script and a one-complex test (1a30). All plugins write the same output,
`predictions.csv` with the columns `pdbid, pKd_predicted`, so results can be compared directly.

## Status

| Level | Scoring functions | Status |
|---|---|---|
| 1 – CPU, trained model available | ET-Score, GB-Score, OnionNet-2, SFCNN, PLANET, egGNN, GIGN, EHIGN-PLA, saCNN, DEAttentionDTA, RFL-Score (combi-lab; features via Docker), AutoDock Vina (Su et al. 2019; Vina 1.1.2 + MGLTools in Docker, Vina 1.2.5 on Windows) | 12/12 installed, 1a30 test passes (AutoDock Vina reproduces the CASF-2016 value, −4.99866 kcal/mol) |
| 2 – extra steps | IGModel, ConBAP, HAC-Net, delta_LinF9_XGB (Linux/Docker), DeepBindGCN, GraphscoreDTA, ΔVinaRF20 (Su et al. 2019; features Linux/Docker) | installed; 1a30 test passes (GraphscoreDTA: only the authors' 279 pre-built complexes, 1a30 not available; ΔVinaRF20 reproduces the CASF-2016 value, 4.78). CPIScore discarded (incomplete model) |
| 3 – heavy (GPU, licences, large databases) | PIGNet2, PointNet/PointTransformer and BAPA (all run on CPU; PointNet makes its point clouds only on Linux/Docker); Dynaformer, TopoFormer, CGraphDTA, EGNA, HydraScreen, P3-Score | PIGNet2, PointNet and BAPA: 1a30 test passes. HydraScreen: local inference needs private Ro5 packages, only the API is left. Dynaformer and TopoFormer: waiting for the model downloads (OneDrive, weilab.math.msu.edu: not reachable from the test machines). CGraphDTA, EGNA, P3-Score pending |
| Lista 2 – Transformer models (systematic review, `Apresentação.pdf` slides 22–23) | Level 1: DeepRLI. Level 2: MMPD-DTA (inputs rebuilt from raw files, identical to the authors'), T-ALPHA, DTITR. Level 3: DTA-GTOmega (needs the OmegaFold weights), DBGT-PLA (needs the authors' IChem interaction graphs). Discarded after checking the repos: PLiSAGE (only the protein pre-training), TransScore (no code or model), GITK (no trained model); SST does not apply (ligand-only model for SARS-CoV-2 receptors) | DeepRLI (pKd 4.1986), MMPD-DTA (pKd 5.3879) and DTITR (pKd 5.0047; sequence-only, trained on Davis kinases): 1a30 test passes with Windows conda and Docker. T-ALPHA (Linux/Docker only, pykeops): 1a30 test passes on Linux with the authors' pre-computed features (pKd 5.7758) and reproduces the paper's CASF-2016 PCC 0.869; Docker test passes on the lab PC (Windows + Docker Desktop). DeepTGIN, MRBDTA and 12 models without code discarded |

AutoDock Vina and ΔVinaRF20 are the two scoring functions of Su et al. 2019 (CASF-2016) that can be downloaded (`Funciones_Score_Su2018`); X-Score needs a signed licence and the others are commercial.

SF from the first survey are **Lista 1**; those from the Transformer review are **Lista 2** (column *Lista* in the sheet).
The detailed plan and progress are in `docs/CombiLabHUB_etapas.xlsx`; the tests still to run on the lab computer are in `docs/LISTA_TESTS_PENDIENTES.md`.

## Repository layout

```
plugins/<sf>/
    INSTALL.md          step-by-step installation (conda on Windows, or Docker)
    environment.yml     conda environment with pinned versions
    Dockerfile          same environment as a container (upstream commit and model MD5 pinned)
    predict_<sf>.py     scores a folder of complexes (one sub-folder per complex)
    test_1a30.py        checks the installation against the authors' value for 1a30
    demo_<sf>.bat       one-click Windows demo (conda): creates the environment and runs the test
    docker_<sf>.bat     Windows + Docker Desktop: builds the image (first time) and runs the test
    docker_<sf>.sh      Linux + Docker: same as docker_<sf>.bat
tools/
    run_coreset_level1.bat   scores the CASF-2016 core set with every Level 1 SF
    evaluate_casf.py         PCC, SD, Spearman and RMSE against CoreSet.dat
    docker_test_all.bat/.sh  builds and tests every plugin's Docker image, one by one, with a summary
docs/
    CombiLabHUB_etapas.xlsx  project stages and status of every SF
    LISTA_TESTS_PENDIENTES.md  tests still to run on the lab computer (1a30 only) and downloads still missing
    Avance_CombiLabHUB_2026-10-30.pptx  progress presentation (Spanish), 30/10/2026
```

## Folders used on the lab computer

| Variable | Default | Contents |
|---|---|---|
| `SF` | `C:\Users\Admin\Desktop\PROYECTO_UNIVERSIDAD\sf` | code and models of each SF, and the `results_<sf>` folders |
| `CASF` | `C:\Users\Admin\Desktop\SOFTWARE SF\CASF-2016\CASF-2016` | CASF-2016 (from PDBbind, registration required) |
| `CONDA` | `%USERPROFILE%\miniconda3` | Miniconda |

All `.bat` files accept these as environment variables, so they work on another computer with
`set SF=...` before running them.

## Quick start

1. Install Miniconda.
2. Install one SF: run `plugins\<sf>\demo_<sf>.bat`. It creates the conda environment, unpacks the
   code, downloads the model if needed and runs the 1a30 test. Details in `plugins\<sf>\INSTALL.md`.
3. Score the CASF-2016 core set and compute the PCC of all Level 1 SF:

   ```bat
   tools\run_coreset_level1.bat
   ```

   or only some of them: `tools\run_coreset_level1.bat gb sfcnn`.
   Results go to `%SF%\resultados_casf2016\` (`pcc_nivel1.csv`, `pcc_nivel1.md`,
   `predicciones_nivel1.csv`, `tiempos.txt`). SF that already finished are skipped.

## Adding a scoring function

1. Create `plugins/<sf>/` with `environment.yml` (pin every version) and a `Dockerfile`.
2. Write `predict_<sf>.py`: arguments `--<sf>-dir`, `-d <folder of complexes>`, `-o predictions.csv`;
   output columns `pdbid, pKd_predicted`. Reuse the authors' feature and model code; document any fix.
3. Write `test_1a30.py`, comparing with a value published by the authors (or by Eaves et al. 2026).
4. Write `INSTALL.md` and `demo_<sf>.bat` following an existing plugin.
5. Add the SF to `tools/run_coreset_level1.bat` and to the `SFS` list in `tools/evaluate_casf.py`.
6. Update `docs/CombiLabHUB_etapas.xlsx`.

## References

- Su M. et al. *Comparative Assessment of Scoring Functions: The CASF-2016 Update.* J. Chem. Inf. Model. 2019.
- Eaves J. et al. 2026, reproducibility study of published scoring functions (corrected versions at github.com/jeavesj).
