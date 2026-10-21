"""DeepBindGCN_RG installation test with complex 1a30 (HIV-1 protease).

  [1] The trained model loads and its weights go into the authors' GCNNet. On a
      symmetric graph our copy of the PyTorch Geometric 1.x GCNConv must give the same
      output as the current GCNConv (checks the weight transfer); on the directed pocket
      graph they differ, as expected (see predict_deepbindgcn.py).
  [2] CASF-2016 complex 1a30 must give pKd 4.4640. This value is ours (Linux,
      21/10/2026); neither the authors nor Eaves et al. publish per-complex values.
      The experimental value of 1a30 is 4.30.

Usage (inside the deepbindgcn environment)
  python test_1a30.py --dbg-dir <DeepBindGCN folder> --model <full_model_out2000_RG.model> --complex <...\\coreset\\1a30>

Exit code 0 = PASS, 1 = FAIL.
"""
import argparse
import hashlib
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import predict_deepbindgcn as W  # noqa: E402

import numpy as np  # noqa: E402

MODEL_MD5 = "aaa694546e7cf41c9d2c3417df197d17"
REF_1A30 = 4.4640
EXPERIMENTAL_PKD = 4.30
TOL = 0.01


def md5(path):
    h = hashlib.md5()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dbg-dir", required=True, help="DeepBindGCN folder (contains DeepBindGCN_RG_example/)")
    ap.add_argument("--model", required=True, help="full_model_out2000_RG.model")
    ap.add_argument("--complex", required=True, help="CASF-2016 folder of complex 1a30")
    a = ap.parse_args()
    dd, cx = os.path.abspath(a.dbg_dir), os.path.abspath(a.complex)
    need = [os.path.abspath(a.model), os.path.join(dd, W.RG, "aa_vec_dic.npy"), os.path.join(dd, W.RG, "models", "gcn.py"),
            os.path.join(cx, "1a30_protein.pdb"), os.path.join(cx, "1a30_ligand.mol2")]
    for f in need:
        if not os.path.isfile(f):
            sys.exit("ERROR: file not found: " + f)
    import torch
    from torch_geometric.nn import GCNConv
    ok = True

    m = md5(need[0])
    net = W.load_model(dd, need[0])
    torch.manual_seed(0)
    x = torch.rand(6, 30)
    ei = torch.tensor([[0, 1, 1, 2, 2, 3, 3, 4, 4, 5], [1, 0, 2, 1, 3, 2, 4, 3, 5, 4]])
    old = net.conv1_xt
    new = GCNConv(old.weight.shape[0], old.weight.shape[1])
    new.lin.weight.data = old.weight.data.t().clone()
    new.bias.data = old.bias.data.clone()
    with torch.no_grad():
        d = float((old(x, ei) - new(x, ei)).abs().max())
    good = m == MODEL_MD5 and d < 1e-5
    ok = ok and good
    print("[1] Model MD5 %s (%s); OldGCNConv vs current GCNConv on a symmetric graph: max difference %.2e"
          % (m, "OK" if m == MODEL_MD5 else "expected " + MODEL_MD5, d))
    print("    PASS" if good else "    FAIL - wrong model file, or PyTorch / PyTorch Geometric problem")

    aa = np.load(need[1], allow_pickle=True).item()
    smi, src = W.ligand_smiles(cx, "1a30")
    p, nres, _ = W.predict_complex(net, aa, need[3], need[4], smi)
    good = abs(p - REF_1A30) <= TOL
    ok = ok and good
    print("\n[2] Predicted pKd 1a30: %.4f (reference %.4f, experimental %.2f; %d pocket residues, ligand from %s)"
          % (p, REF_1A30, EXPERIMENTAL_PKD, nres, src))
    print("    PASS" if good else "    FAIL - check the RDKit and PyTorch Geometric versions (environment.yml)")
    print("\nRESULT: %s" % ("PASS" if ok else "FAIL"))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
