"""Predict binding affinity (pKd) with BAPA (Seo et al., BMC Bioinformatics 2021) for many complexes.

BAPA is a convolutional neural network with an attention layer. It uses two
inputs for each complex:
  * how many times each of 2,500 selected "descriptors" occurs (small
    protein-ligand atom graphs within 12 A, built from the Sybyl atom types of
    the protein and ligand .mol2 files), and
  * six Vina terms (gauss1, gauss2, repulsion, hydrophobic, hydrogen bond and
    the number of rotatable bonds) computed by rf-extract (RF-Score v3) from
    the .pdbqt files.
The trained network is in the repository (module/network, TensorFlow 1).

Steps for each complex (one sub-folder per complex), as the authors' scripts:
  1. convert_to_PDBQT.py: waters removed from <code>_protein.pdb; protein .pdb
     and ligand .mol2 -> .pdbqt with Open Babel 2.4.1 ("babel"). Open Babel 3
     writes the receptor atoms in another order, which changes the hydrophobic
     Vina term, so Open Babel 2.4.1 is required.
  2. get_Vina_terms.py: rf-extract <protein.pdbqt> <ligand.pdbqt>, columns
     36-40 and 46. The original RF-Score repository (HongjianLi/RF-Score) is no
     longer on GitHub; the fork github.com/lachrymator/RF-Score gives the same
     values for the authors' example.
  3. get_descriptors_occurrence_count.py, with the protein .mol2. The authors
     make it with UCSF Chimera ("write format mol2"). --protein-mol2 casf (default)
     uses the <code>_protein.mol2 that comes with CASF-2016/PDBbind; chimera runs
     Chimera if it is installed; obabel uses Open Babel (gives different values).
  4. predict.py: the trained network (TensorFlow 1.12).

Usage (inside the bapa environment)
  python predict_bapa.py --bapa-dir <BAPA repository folder> -d <complexes folder> [-o predictions.csv]

Each complex needs <code>_protein.pdb and <code>_ligand.mol2 (and <code>_protein.mol2
for --protein-mol2 casf).
"""
import argparse
import os
import pickle
import shutil
import subprocess
import sys
import tempfile
import warnings

HERE = os.path.dirname(os.path.abspath(__file__))
VINA_COLUMNS = [36, 37, 38, 39, 40, 46]  # as in the authors' get_Vina_terms.py


class Bapa:
    """The authors' code and trained network, loaded once."""

    def __init__(self, bapa_dir, rf_extract=None):
        self.root = os.path.abspath(bapa_dir)
        if not os.path.isfile(os.path.join(self.root, "module", "network", "BAPA_network.meta")):
            sys.exit("ERROR: %s does not look like the BAPA repository (module/network missing)" % bapa_dir)
        if self.root not in sys.path:
            sys.path.insert(0, self.root)
        warnings.filterwarnings("ignore")
        os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "2")
        self.rf_extract = rf_extract or find_rf_extract()
        self.babel = shutil.which("babel") or shutil.which("obabel")
        if self.babel is None:
            sys.exit("ERROR: Open Babel (babel) not found: activate the bapa environment")
        cwd = os.getcwd()
        os.chdir(self.root)  # the authors' modules read ./module/... files
        try:
            import get_descriptors_occurrence_count as desc
            from module.helper import get_descriptors_index, test_normalization
            with open(os.path.join("module", "normalized_parameters.pkl"), "rb") as f:
                pickle.load(f)  # fail early if missing
        finally:
            os.chdir(cwd)
        self.desc = desc
        self.get_descriptors_index = get_descriptors_index
        self.test_normalization = test_normalization

    def _babel_cmd(self, in_fmt, src, out_fmt, dst):
        """'babel -ipdb in -opdbqt out' (authors' command) or the obabel equivalent."""
        if os.path.basename(self.babel).lower().startswith("babel"):
            return [self.babel, in_fmt, src, out_fmt, dst]
        return [self.babel, in_fmt, src, out_fmt, "-O", dst]

    # -- step 1 -----------------------------------------------------------
    def pdbqt(self, protein_pdb, ligand_mol2, work):
        os.makedirs(work, exist_ok=True)
        nowater = os.path.join(work, "protein_remove_water.pdb")
        with open(protein_pdb) as fi, open(nowater, "w") as fo:  # authors' remove_water()
            for line in fi:
                line = line.strip()
                if "HETATM" in line and len(line.split()) > 3 and "HOH" in line.split()[3]:
                    continue
                fo.write(line + "\n")
        prot, lig = os.path.join(work, "protein.pdbqt"), os.path.join(work, "ligand.pdbqt")
        for args in (["-ipdb", nowater, "-opdbqt", prot], ["-imol2", ligand_mol2, "-opdbqt", lig]):
            out = args[3]
            r = subprocess.run(self._babel_cmd(*args), stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
            if not os.path.isfile(out) or os.path.getsize(out) == 0:
                raise RuntimeError("Open Babel failed: " + (r.stderr or "").strip()[-300:])
        return prot, lig

    # -- step 2 -----------------------------------------------------------
    def vina_terms(self, protein_pdbqt, ligand_pdbqt):
        import numpy as np
        r = subprocess.run([self.rf_extract, protein_pdbqt, ligand_pdbqt], stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
        lines = [l for l in (r.stdout or "").splitlines() if l.strip()]
        if r.returncode != 0 or len(lines) < 2:
            raise RuntimeError("rf-extract failed: " + (r.stderr or r.stdout or "no output").strip()[-300:])
        values = lines[-1].strip().split(",")
        return np.array(values, dtype=np.float32)[VINA_COLUMNS]

    # -- step 3 -----------------------------------------------------------
    def descriptors(self, protein_mol2, ligand_mol2):
        cwd = os.getcwd()
        os.chdir(self.root)
        try:
            graphs, _ = self.desc.read_complexes([protein_mol2], [ligand_mol2], [1.0])
            data = self.desc.make_data(graphs)
        finally:
            os.chdir(cwd)
        return list(data.values())[0]

    # -- step 4 -----------------------------------------------------------
    def predict(self, data_rows, vina_rows):
        """Authors' run_test(): normalization + trained network."""
        import numpy as np
        import tensorflow as tf
        data = np.array(data_rows, dtype=np.float32)
        vina = np.array(vina_rows, dtype=np.float32)
        cwd = os.getcwd()
        os.chdir(self.root)
        try:
            data, vina = self.test_normalization(data, vina)
            index = self.get_descriptors_index(len(data), 2500)
            saver_dir = os.path.join(self.root, "module", "network")
            tf.reset_default_graph()
            with tf.Session() as sess:
                saver = tf.train.import_meta_graph(os.path.join(saver_dir, "BAPA_network.meta"))
                saver.restore(sess, os.path.join(saver_dir, "BAPA_network"))
                DESCRIPTORS_INDEX, DESCRIPTION_MATRIX, VINA_TERMS, _, keep_prob = tf.get_collection("input_variables")
                predicted = tf.get_collection("predict")
                out = sess.run(predicted[1], feed_dict={DESCRIPTORS_INDEX: index, DESCRIPTION_MATRIX: data,
                                                       VINA_TERMS: vina, keep_prob: 1.0})
        finally:
            os.chdir(cwd)
        return [float(x) for x in np.asarray(out).flatten()]


def find_rf_extract():
    """rf-extract: next to this file (rf-extract.exe on Windows), or in the PATH."""
    names = ["rf-extract.exe"] if os.name == "nt" else ["rf-extract"]
    for n in names:
        for p in (os.path.join(HERE, "bin", n), os.path.join(HERE, n)):
            if os.path.isfile(p):
                return p
        p = shutil.which(n)
        if p:
            return p
    sys.exit("ERROR: rf-extract not found (Windows: bin\\rf-extract.exe in this folder; Linux: build RF-Score, see INSTALL.md)")


def chimera_mol2(protein_pdb, out_mol2):
    exe = shutil.which("chimera") or shutil.which("chimera.exe")
    if exe is None:
        raise RuntimeError("--protein-mol2 chimera needs UCSF Chimera in the PATH")
    script = out_mol2 + ".cmd"
    with open(script, "w") as f:
        f.write("open %s\nwrite format mol2 0 %s\nstop\n" % (protein_pdb, out_mol2))
    with open(script) as f:
        subprocess.run([exe, "--nogui"], stdin=f, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if not os.path.isfile(out_mol2):
        raise RuntimeError("Chimera did not write " + out_mol2)
    return out_mol2


def protein_mol2_for(model, mode, code, folder, work):
    pdb = os.path.join(folder, code + "_protein.pdb")
    if mode == "casf":
        p = os.path.join(folder, code + "_protein.mol2")
        if not os.path.isfile(p):
            raise RuntimeError("%s not found (use --protein-mol2 chimera or obabel)" % os.path.basename(p))
        return p
    out = os.path.join(work, code + "_protein.mol2")
    if mode == "chimera":
        return chimera_mol2(pdb, out)
    subprocess.run(model._babel_cmd("-ipdb", pdb, "-omol2", out), stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
    if not os.path.isfile(out):
        raise RuntimeError("Open Babel could not write the protein .mol2")
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--bapa-dir", required=True, help="BAPA repository folder (contains module/network)")
    ap.add_argument("-d", "--directory", required=True, help="folder with one sub-folder per complex")
    ap.add_argument("-o", "--output", default="predictions.csv", help="output CSV (default: predictions.csv)")
    ap.add_argument("--protein-mol2", choices=("casf", "chimera", "obabel"), default="casf",
                    help="source of the protein .mol2 (default: casf, the <code>_protein.mol2 of the folder)")
    ap.add_argument("--rf-extract", help="path of the rf-extract program (default: bin/ of this folder or PATH)")
    args = ap.parse_args()

    import pandas as pd
    model = Bapa(args.bapa_dir, args.rf_extract)
    tmp = tempfile.mkdtemp(prefix="bapa_")
    codes, data, vina = [], [], []
    for code in sorted(os.listdir(args.directory)):
        folder = os.path.abspath(os.path.join(args.directory, code))
        prot = os.path.join(folder, code + "_protein.pdb")
        lig = os.path.join(folder, code + "_ligand.mol2")
        if not (os.path.isfile(prot) and os.path.isfile(lig)):
            continue
        try:
            work = os.path.join(tmp, code)
            p_qt, l_qt = model.pdbqt(prot, lig, work)
            v = model.vina_terms(p_qt, l_qt)
            d = model.descriptors(protein_mol2_for(model, args.protein_mol2, code, folder, work), lig)
        except Exception as e:  # keep going with the other complexes
            print("Skipping %s: %s" % (code, e))
            continue
        codes.append(code)
        data.append(d)
        vina.append(v)
        print("%s\tfeatures ready" % code)
    shutil.rmtree(tmp, ignore_errors=True)
    if not codes:
        sys.exit("ERROR: no complexes prepared in " + args.directory)
    preds = model.predict(data, vina)
    rows = [[c, round(p, 4)] + [round(float(x), 4) for x in v] for c, p, v in zip(codes, preds, vina)]
    cols = ["pdbid", "pKd_predicted", "gauss1", "gauss2", "repulsion", "hydrophobic", "hbond", "nrot"]
    pd.DataFrame(rows, columns=cols).to_csv(args.output, index=False)
    for c, p in zip(codes, preds):
        print("%s\t%.4f" % (c, p))
    print("Done: %d complexes (protein .mol2: %s) -> %s" % (len(codes), args.protein_mol2, os.path.abspath(args.output)))


if __name__ == "__main__":
    main()
