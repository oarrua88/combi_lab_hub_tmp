"""Copy CASF-2016 complexes into the folder layout GB-Score expects.

GB-Score (generate_features.py) takes the FIRST *.mol2 and *.pdb it finds in each complex folder, but the
CASF-2016 folders also contain <code>_ligand_opt.mol2 and <code>_pocket.pdb.
This script keeps only <code>_ligand.mol2 and <code>_protein.pdb.

Usage:  python prepare_casf.py <...\\CASF-2016\\coreset> <output folder> [code ...]
        (no codes = all 285 complexes)
"""
import os
import shutil
import sys

if len(sys.argv) < 3:
    sys.exit(__doc__)
src, dst, codes = sys.argv[1], sys.argv[2], sys.argv[3:]
codes = codes or sorted(d for d in os.listdir(src) if os.path.isdir(os.path.join(src, d)))
for code in codes:
    out = os.path.join(dst, code)
    os.makedirs(out, exist_ok=True)
    for name in (code + "_ligand.mol2", code + "_protein.pdb"):
        shutil.copy(os.path.join(src, code, name), out)
print("Prepared %d complexes in %s" % (len(codes), dst))
