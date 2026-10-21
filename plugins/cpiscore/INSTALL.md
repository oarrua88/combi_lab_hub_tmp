# CPIScore — not runnable for inference

**Status: discarded (21/10/2026).** CPIScore cannot be used as a trained scoring function. Only the code and one checkpoint (`result/model.pkl`) are public. Even with them, the model cannot reproduce any prediction.

| | |
|---|---|
| Code | <https://github.com/liang2508/CPIScore>, commit `d67dd2dfd4d55c6c49d1503e9d785228baf77ed5` (licence in `LICENSE.txt`) |
| Checkpoint | `result/model.pkl` (a whole pickled `model.Model`) |
| Reported CASF-2016 PCC | 0.74 (our project table). Not in Eaves et al. 2026 |

## Why it cannot be run

1. **Missing word2vec models.** Two of the model's inputs are mean word2vec embeddings of the SMILES (3-character words) and of the protein sequence. `w2v.py` loads them from `./result/gensim-model-256dim-smiles` and `./result/gensim-model-512dim-protein`. Neither file is in the repository. They were trained on ChEMBL SMILES (`./data/chembl.smi`, also missing) and on the authors' protein sequences. Training them again would be retraining, and word2vec training is not reproducible anyway. The commented training code even saves a *128*-dimensional SMILES model, while the loader expects a *256*-dimensional one.
2. **Part of the network is never saved.** `Model.forward()` creates a new `Transformer(...)` (ligand–protein cross-attention) **on every call**, with fresh random weights. Those weights are not in `model.pkl`: its 31 parameter tensors are only the GCN, the dense layers and the final layers. So the transformer branch is random at training time and at prediction time, and the same input gives a different pKd on each run.
3. **Other problems.** Every script starts with `os.chdir('F:\\DTI\\CPIScore\\model')`, and the README only explains training (`data_process.py`, `train.py`). There is no prediction script.

Because of points 1 and 2, no installation can reproduce the published model. CPIScore was moved to the "discarded" list in `docs/CombiLabHUB_etapas.xlsx`.
