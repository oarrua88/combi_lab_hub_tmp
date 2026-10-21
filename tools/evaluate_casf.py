"""CASF-2016 scoring power for the CombiLabHUB plugins.

Reads the predictions of every scoring function (one CSV per SF, written by
run_coreset_level1.bat) and the experimental affinities of the core set
(CASF-2016/power_scoring/CoreSet.dat), and computes for each SF:

  n         complexes with a prediction (out of 285)
  PCC       Pearson correlation (the "scoring power" of CASF-2016)
  PCC_CI90  90% bootstrap confidence interval of the PCC (as CASF-2016 does)
  SD        standard deviation of the linear fit (CASF-2016 definition)
  Spearman  rank correlation
  RMSE      root mean squared error between predicted and experimental pKd

and compares the PCC with the value of the original paper and with the value
that Eaves et al. (2026) obtained when they re-ran the code.

Usage:
  python evaluate_casf.py --sf-dir <...\\sf> --coreset-dat <...\\power_scoring\\CoreSet.dat>
                          [-o <...\\sf\\resultados_casf2016>]

Only needs numpy and pandas.
"""
import argparse
import os
import sys

import numpy as np
import pandas as pd

# name shown, results folder, PCC in the original paper, PCC reproduced by Eaves et al.
SFS = [
    ("ET-Score",       "results_et",             0.827, None),
    ("GB-Score",       "results_gb",             0.862, None),
    ("OnionNet-2",     "results_onionnet2",      0.864, 0.851),
    ("SFCNN",          "results_sfcnn",          0.793, 0.789),
    ("PLANET",         "results_planet",         0.824, None),
    ("egGNN",          "results_eggnn",          0.860, 0.669),
    ("GIGN",           "results_gign",           0.840, 0.850),
    ("EHIGN-PLA",      "results_ehign_pla",      0.854, 0.851),
    ("saCNN",          "results_sacnn",          0.865, 0.862),
    ("DEAttentionDTA", "results_deattentiondta", 0.845, 0.819),
    ("RFL-Score",      "results_rfl",            None,  None),   # combi-lab; set the paper PCC here
]


def read_coreset(path):
    rows = []
    with open(path) as f:
        for line in f:
            if line.startswith("#") or not line.strip():
                continue
            p = line.split()
            rows.append((p[0].lower(), float(p[3]), int(p[5])))
    return pd.DataFrame(rows, columns=["pdbid", "pKd_exp", "target"]).set_index("pdbid")


def read_predictions(path):
    df = pd.read_csv(path)
    id_col = "pdbid" if "pdbid" in df.columns else df.columns[0]
    for c in ("pKd_predicted", "prediction", "pKd", "pred"):
        if c in df.columns:
            pred_col = c
            break
    else:
        num = [c for c in df.columns if c != id_col and pd.api.types.is_numeric_dtype(df[c])]
        if not num:
            raise ValueError("no numeric prediction column in %s" % path)
        pred_col = num[0]
    out = pd.DataFrame({"pdbid": df[id_col].astype(str).str.strip().str.lower().str[:4],
                        "pKd_pred": pd.to_numeric(df[pred_col], errors="coerce")})
    return out.dropna().drop_duplicates("pdbid").set_index("pdbid")


def pearson(x, y):
    return float(np.corrcoef(x, y)[0, 1])


def metrics(x, y, n_boot=10000, seed=0):
    """x = predicted, y = experimental."""
    r = pearson(x, y)
    b, a = np.polyfit(x, y, 1)                       # y ~ a + b*x
    sd = float(np.sqrt(np.sum((y - (a + b * x)) ** 2) / (len(x) - 1)))
    rho = pearson(pd.Series(x).rank().values, pd.Series(y).rank().values)
    rmse = float(np.sqrt(np.mean((x - y) ** 2)))
    rng = np.random.default_rng(seed)
    idx = rng.integers(0, len(x), size=(n_boot, len(x)))
    xb, yb = x[idx], y[idx]
    xb = xb - xb.mean(1, keepdims=True)
    yb = yb - yb.mean(1, keepdims=True)
    rb = (xb * yb).sum(1) / np.sqrt((xb ** 2).sum(1) * (yb ** 2).sum(1))
    lo, hi = np.percentile(rb, [5, 95])
    return r, (float(lo), float(hi)), sd, rho, rmse


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--sf-dir", required=True, help="folder with the results_<sf> folders")
    ap.add_argument("--coreset-dat", required=True, help="CASF-2016/power_scoring/CoreSet.dat")
    ap.add_argument("-o", "--outdir", help="output folder (default: <sf-dir>/resultados_casf2016)")
    args = ap.parse_args()

    exp = read_coreset(args.coreset_dat)
    outdir = args.outdir or os.path.join(args.sf_dir, "resultados_casf2016")
    os.makedirs(outdir, exist_ok=True)

    rows, merged = [], exp.copy()
    for name, folder, paper, eaves in SFS:
        path = os.path.join(args.sf_dir, folder, "predictions.csv")
        row = {"SF": name, "n": 0, "PCC": None, "PCC_CI90": "", "SD": None, "Spearman": None,
               "RMSE": None, "PCC_paper": paper, "PCC_Eaves": eaves, "diff_vs_paper": None,
               "missing": "", "status": ""}
        if not os.path.exists(path):
            row["status"] = "sin resultados"
            rows.append(row)
            continue
        try:
            pred = read_predictions(path)
        except Exception as e:                     # noqa: BLE001
            row["status"] = "error leyendo: %s" % e
            rows.append(row)
            continue
        merged[name] = pred["pKd_pred"]
        d = exp.join(pred, how="inner")
        missing = sorted(set(exp.index) - set(d.index))
        row["n"] = len(d)
        row["missing"] = " ".join(missing[:20]) + (" ..." if len(missing) > 20 else "")
        if len(d) >= 3:
            r, ci, sd, rho, rmse = metrics(d["pKd_pred"].values, d["pKd_exp"].values)
            row.update(PCC=round(r, 3), PCC_CI90="%.3f-%.3f" % ci, SD=round(sd, 2),
                       Spearman=round(rho, 3), RMSE=round(rmse, 2), diff_vs_paper=round(r - paper, 3) if paper is not None else None)
            row["status"] = "OK" if len(d) == len(exp) else "incompleto (%d/%d)" % (len(d), len(exp))
        rows.append(row)

    table = pd.DataFrame(rows)
    table.to_csv(os.path.join(outdir, "pcc_nivel1.csv"), index=False)
    merged.to_csv(os.path.join(outdir, "predicciones_nivel1.csv"))

    cols = ["SF", "n", "PCC", "PCC_CI90", "SD", "Spearman", "RMSE", "PCC_paper", "PCC_Eaves", "diff_vs_paper", "status"]
    show = table[cols].fillna("")
    lines = ["| " + " | ".join(cols) + " |", "|" + "---|" * len(cols)]
    lines += ["| " + " | ".join(str(v) for v in r) + " |" for r in show.values]
    md = "\n".join(lines)
    with open(os.path.join(outdir, "pcc_nivel1.md"), "w", encoding="utf-8") as f:
        f.write("# CASF-2016 scoring power - Level 1\n\n" + md + "\n")
    print(show.to_string(index=False))
    print("\nResults written to", outdir)


if __name__ == "__main__":
    sys.exit(main())
