"""Make ET-Score's generate_feature.py work on Linux/macOS (used by the Dockerfile).

Upstream builds file paths with a Windows backslash: glob.glob(folder + "\\" + "*.mol2").
On Linux that pattern never matches, so we replace it with os.path.join.
"""
import sys

path = sys.argv[1]
src = open(path).read()
new = (src.replace('glob.glob(protein_folder+"\\\\"+"*.mol2")', 'glob.glob(os.path.join(protein_folder, "*.mol2"))')
          .replace('glob.glob(protein_folder+"\\\\"+"*.pdb")', 'glob.glob(os.path.join(protein_folder, "*.pdb"))'))
n = src.count('protein_folder+"\\\\"+')
if n != 2 or new == src:
    sys.exit("patch_glob: expected 2 Windows-only glob calls, found %d - upstream code changed?" % n)
open(path, "w").write(new)
print("patch_glob: patched", path)
