"""ConBAP installation test.

  [1] The authors' toy-set complex 1bcu (their data/toy_set/ligand/1bcu.sdf and
      protein/1bcu_protein.pdb), featurised from scratch, must give the same pKd as the
      graphs the authors ship pre-built in data/toy_set/1bcu/ (4.8575).
  [2] CASF-2016 complex 1a30, ligand read and sanitized by RDKit (the .sdf cannot be
      sanitized, so the .mol2 is used), must give pKd 5.9318 (our value, Linux,
      21/10/2026). The experimental value of 1a30 is 4.30.
  [3] The same complex with the .sdf read WITHOUT sanitizing, as in the Eaves et al.
      fork, must give their published value 7.7406 (CASF2016_ConBAP_preds_and_times.csv).
      This checks that the environment is equivalent to theirs, and shows why their
      PCC is low (see INSTALL.md, note 1).

Usage (inside the conbap environment)
  python test_1a30.py --conbap-dir <ConBAP folder> --complex <...\\coreset\\1a30>

Exit code 0 = PASS, 1 = FAIL.
"""
import argparse
import os
import shutil
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import predict_conbap as W  # noqa: E402

REF_1BCU = 4.8575      # authors' pre-built graphs, data/toy_set/1bcu
REF_1A30 = 5.9318      # ours, sanitized ligand (.mol2)
REF_EAVES = 7.7406     # Eaves et al., unsanitized .sdf
EXPERIMENTAL_PKD = 4.30
TOL = 0.01


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--conbap-dir", required=True, help="ConBAP folder (with supervised/ and unsupervised/)")
    ap.add_argument("--complex", required=True, help="CASF-2016 folder of complex 1a30")
    a = ap.parse_args()
    cb = os.path.abspath(a.conbap_dir)
    cx = os.path.abspath(a.complex)
    toy = os.path.join(cb, "supervised", "data", "toy_set")
    need = [os.path.join(cb, W.UNSUP), os.path.join(cb, W.SUP),
            os.path.join(toy, "ligand", "1bcu.sdf"), os.path.join(toy, "protein", "1bcu_protein.pdb"),
            os.path.join(toy, "1bcu", "ConBAP-1bcu_complex_8A.pyg"),
            os.path.join(cx, "1a30_protein.pdb"), os.path.join(cx, "1a30_ligand.mol2"), os.path.join(cx, "1a30_ligand.sdf")]
    for f in need:
        if not os.path.isfile(f):
            sys.exit("ERROR: file not found: " + f)

    print("Loading model ...")
    net = W.load(cb)
    ok = True

    authors = dict(W.score(net, toy, ["1bcu"]))["1bcu"]
    tmp = tempfile.mkdtemp(prefix="conbap_test_")
    try:
        os.makedirs(os.path.join(tmp, "1bcu"))
        shutil.copy(need[2], os.path.join(tmp, "1bcu", "1bcu_ligand.sdf"))
        shutil.copy(need[3], os.path.join(tmp, "1bcu", "1bcu_protein.pdb"))
        mine = float(W.predict_folder(cb, tmp, "sdf", net, verbose=False).pKd_predicted.iloc[0])
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    good = abs(authors - REF_1BCU) <= TOL and abs(mine - authors) <= TOL
    ok = ok and good
    print("\n[1] Toy-set 1bcu: our featurisation %.4f, authors' pre-built graphs %.4f (expected %.4f)"
          % (mine, authors, REF_1BCU))
    print("    PASS - same as the authors' graphs" if good else
          "    FAIL - check the PyTorch, PyG, torch_scatter, GVP, RDKit and PyMOL versions")

    root = os.path.dirname(cx)
    tmp = tempfile.mkdtemp(prefix="conbap_test_")
    try:
        shutil.copytree(cx, os.path.join(tmp, "1a30"))
        p = W.predict_folder(cb, tmp, "auto", net, verbose=False)
        p_e = W.predict_folder(cb, tmp, "sdf-nosanitize", net, verbose=False)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    v, src = float(p.pKd_predicted.iloc[0]), p.ligand_source.iloc[0]
    good = abs(v - REF_1A30) <= TOL
    ok = ok and good
    print("\n[2] Predicted pKd 1a30: %.4f, ligand from %s (reference %.4f, experimental %.2f)"
          % (v, src, REF_1A30, EXPERIMENTAL_PKD))
    print("    PASS" if good else "    FAIL - the CASF-2016 pipeline gives a different value")

    ve = float(p_e.pKd_predicted.iloc[0])
    good = abs(ve - REF_EAVES) <= TOL
    ok = ok and good
    print("\n[3] 1a30 with the .sdf NOT sanitized (Eaves et al.): %.4f (Eaves %.4f)" % (ve, REF_EAVES))
    print("    PASS - same as Eaves et al." if good else "    FAIL")
    print("\nRESULT: %s" % ("PASS" if ok else "FAIL"))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
