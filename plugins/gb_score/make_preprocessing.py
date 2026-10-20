"""Rebuild reference/gb_score_preprocessing.csv from the authors' Figshare files.

Reproduces preprocessing() from the authors' analysis.ipynb on total_set_2019.csv
(PDBbind 2019 general + refined set features, core set included):
  - drop columns with variance <= 0.01
  - drop columns with |correlation| > 0.95 to an earlier column
  - keep the mean and std of the remaining columns for standardization

Usage:  python make_preprocessing.py <total_set_2019.csv> [output.csv]
Only needed to audit or regenerate the table; the result is already in the repository.
"""
import sys

import numpy as np
import pandas as pd

if len(sys.argv) < 2:
    sys.exit(__doc__)
out = sys.argv[2] if len(sys.argv) > 2 else "gb_score_preprocessing.csv"
data = pd.read_csv(sys.argv[1], index_col=0)
data = data.loc[:, data.var(axis=0) > 0.01]
corr = data.corr().abs()
upper = corr.where(np.triu(np.ones(corr.shape), k=1).astype(bool))
data = data.drop([c for c in upper.columns if any(upper[c] > 0.95)], axis=1)
table = pd.DataFrame({"mean": data.mean(), "std": data.std()})
table.index.name = "feature"
table.to_csv(out, float_format="%.10g")
print("%d features kept -> %s" % (len(table), out))
