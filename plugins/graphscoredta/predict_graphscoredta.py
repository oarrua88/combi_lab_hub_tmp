"""GraphscoreDTA - prediction with the authors' pre-processed CASF-2016 graphs (CPU).

GraphscoreDTA (Wang et al., Bioinformatics 2023) scores a complex from a DGL graph
(ligand atoms, pocket residues and their interactions) plus 6 AutoDock Vina terms.
The authors published the model and the inputs already built for CASF-2016
(test_set/all_in_one_graph_test2016.bin + Vina_terms2016.pkl, 279 complexes),
but NOT the code that builds them, so new complexes cannot be featurised.

This script runs the authors' model (src/model.py, model/modelp.pth) on those inputs,
on CPU and without numba/IPython, and writes pdbid, pKd_predicted.

Usage (inside the gsdta environment)
  python predict_graphscoredta.py --gs-dir <GraphscoreDTA folder> [-o predictions.csv] [--model modelp|modelc]
"""
import argparse
import os
import pickle
import sys

os.environ.setdefault("DGLBACKEND", "pytorch")
import warnings
warnings.filterwarnings("ignore")

import numpy as np
import pandas as pd
import torch


def load_model_class(path):
    """Import the authors' src/model.py with its hard-coded 'cuda:0' replaced by 'cpu'.

    ModelNew.forward() moves every input to 'cuda:0', so the authors' code cannot run
    on a computer without an NVIDIA GPU. Only the device string is changed.
    """
    import types
    src = open(path, encoding="utf-8").read().replace("cuda:0", "cpu")
    mod = types.ModuleType("gsdta_model")
    mod.__file__ = path
    exec(compile(src, path, "exec"), mod.__dict__)
    return mod.ModelNew


def predict(gs_dir, model_name="modelp", batch_size=32):
    import dgl
    sys.path.insert(0, os.path.join(gs_dir, "src"))
    from dataset import SepDataset, collate_fn   # authors' code
    ModelNew = load_model_class(os.path.join(gs_dir, "src", "model.py"))
    ts = os.path.join(gs_dir, "test_set")
    graphs = dgl.load_graphs(os.path.join(ts, "all_in_one_graph_test2016.bin"))[0]
    labels = pd.read_csv(os.path.join(ts, "labels_test2016.csv"), dtype={"id": str})
    with open(os.path.join(ts, "Vina_terms2016.pkl"), "rb") as f:
        vina = pickle.load(f)
    if len(graphs) != len(labels):
        raise RuntimeError("graphs (%d) and labels (%d) differ" % (len(graphs), len(labels)))
    ds = SepDataset(graphs, [vina[i] for i in labels.id], list(labels.id), list(labels.affinity),
                    ["a_conn", "r_conn", "int_l"])
    loader = torch.utils.data.DataLoader(ds, batch_size=batch_size, shuffle=False, collate_fn=collate_fn)
    model = ModelNew()
    ck = torch.load(os.path.join(gs_dir, "model", model_name + ".pth"), map_location="cpu")
    model.load_state_dict(ck["model"])
    model.eval()
    names, preds, exp = [], [], []
    with torch.no_grad():
        for data in loader:
            ga, gr, gi, aff = data[0]
            y = model(ga, gr, gi, data[1]).reshape(-1)
            preds += y.numpy().tolist()
            exp += aff.reshape(-1).numpy().tolist()
            names += list(data[2])
    return pd.DataFrame({"pdbid": names, "pKd_predicted": np.round(preds, 4), "pKd_experimental": exp})


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--gs-dir", required=True, help="GraphscoreDTA folder (src/, model/, test_set/)")
    ap.add_argument("-o", "--output", default="predictions.csv")
    ap.add_argument("--model", default="modelp", choices=("modelp", "modelc"),
                    help="modelp = the authors' predict.py model (default)")
    a = ap.parse_args()
    df = predict(os.path.abspath(a.gs_dir), a.model)
    df.to_csv(a.output, index=False)
    print("Done: %d complexes -> %s" % (len(df), a.output))


if __name__ == "__main__":
    main()
