"""Python version of MSMS's pdb_to_xyzr (Mike Pique, The Scripps Research Institute).

Reads a PDB file and writes "x y z radius" for every ATOM/HETATM record, with the
radius taken from ./atmtypenumbers (or the file given with --numfile), exactly like the
awk script distributed with MSMS 2.6.1: same patterns, same hydrogen handling,
united-atom radii by default (-h for explicit-hydrogen radii), 0.01 when no pattern matches.
delta_LinF9_XGB needs this script but the MSMS conda package does not ship it.

Usage:  python pdb_to_xyzr.py [-h] file.pdb > file.xyzr
"""
import re
import sys


def read_table(numfile):
    explicit, united, pats = {}, {}, []
    with open(numfile) as f:
        for line in f:
            p = line.split()
            if not p or p[0].startswith("#"):
                continue
            if p[0] == "radius":
                explicit[p[1]] = p[3]
                united[p[1]] = p[3] if len(p) <= 4 or p[4].startswith("#") else p[4]
                continue
            res = ".*" if p[0] == "*" else p[0]
            atm = p[1].replace("_", " ")
            num = p[2]
            if num not in explicit:
                sys.stderr.write("pdb_to_xyzr: error in library file %s entry %s %s %s has no corresponding radius value\n"
                                 % (numfile, p[0], p[1], p[2]))
                explicit[num] = united[num] = "0.01"
            pats.append((re.compile("^" + res + "$"), re.compile("^" + atm + "$"), num))
    return explicit, united, pats


def main(argv):
    explicit_h = False
    numfile = "./atmtypenumbers"
    args = []
    i = 0
    while i < len(argv):
        if argv[i] == "-h":
            explicit_h = True
        elif argv[i] == "--numfile":
            i += 1
            numfile = argv[i]
        else:
            args.append(argv[i])
        i += 1
    explicit, united, pats = read_table(numfile)
    radii = explicit if explicit_h else united
    out = sys.stdout
    for fn in args or ["-"]:
        f = sys.stdin if fn == "-" else open(fn)
        for nr, line in enumerate(f, 1):
            first = line.split()[0] if line.split() else ""
            if first not in ("ATOM", "atom", "HETATM", "hetatm"):
                continue
            line = line.rstrip("\n").ljust(80)
            x, y, z = line[30:38], line[38:46], line[46:54]
            resname = line[17:20]
            aname = line[12:16]
            if re.match(r"[ 0-9][HhDd]", aname[:2]):
                aname = "H"
            if re.match(r"[Hh][^Gg]", aname[:2]):
                aname = "H"
            resnum = line[22:26]
            resname = resname.replace(" ", "")
            aname = aname.replace(" ", "")
            for rp, ap, num in pats:
                if ap.search(aname) and rp.search(resname):
                    # awk prints the coordinate substrings as fields: "x y z r"
                    out.write("%s %s %s %s\n" % (x, y, z, radii[num]))
                    break
            else:
                sys.stderr.write("pdb_to_xyzr: error, file %s line %d residue %s atom pattern %s %s was not found in %s\n"
                                 % (fn, nr, resnum, resname, aname, numfile))
                out.write("%s %s %s 0.01\n" % (x, y, z))
        if f is not sys.stdin:
            f.close()


if __name__ == "__main__":
    main(sys.argv[1:])
