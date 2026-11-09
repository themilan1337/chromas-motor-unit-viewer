"""python -m mu_viewer.within_between <dataset> <ica-group> <ref-chunk>
Sanity numbers for a run: mean |r| of IC pairs inside one CHROMAS cluster vs across clusters, and how many pairs reach 0.5 / 0.9."""
import sys

import numpy as np

from .build import load_dataset
from .core import lab_ic_correlation

ds, grp, ref = sys.argv[1], sys.argv[2], int(sys.argv[3])
d = load_dataset(ds, grp, ref)
C, L = lab_ic_correlation(d["ics"]), d["labels"]
iu = np.triu_indices(len(L), 1)
same, v = (L[:, None] == L[None])[iu], C[iu]
print(f"{ds} {grp}: ICs {len(L)}, chromatophores {len(set(d['ic_chrom'].tolist()))}, clusters {len(set(L.tolist()))}, IC pairs {len(v)}")
print(f"  within-cluster pairs {same.sum()}: mean |r| {v[same].mean():.3f}; between-cluster pairs {(~same).sum()}: mean |r| {v[~same].mean():.3f}")
print(f"  max |r| of any pair {v.max():.3f}; pairs with |r|>=0.5: {int((v >= .5).sum())}; >=0.9: {int((v >= .9).sum())}")
