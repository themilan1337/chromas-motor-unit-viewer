"""Numbers behind the viewer. Pure numpy, no CHROMAS import, so it is testable without the pipeline.

What is the lab's and what is ours:
  lab_ic_correlation  = the matrix CHROMAS builds in chromas/source/analysis/ica_slice_clustering.py line 144,
                        corr = np.abs(np.corrcoef(ICs.data[IC_mask.data])), then clusters with Affinity Propagation.
                        Nothing else in CHROMAS 0.1.1 or in the motor_units folder computes a covariance or correlation of motion.
  unit_stats          = OURS. Summary of that same matrix inside one cluster (mean, min, max of the pairwise values).
                        The lab does not define a per-motor-unit number; this is a reading aid, not their definition.
"""
import numpy as np


def lab_ic_correlation(ics: np.ndarray) -> np.ndarray:
    """ics: (n_ic, n_time), one row per independent component. Same call as the lab."""
    return np.abs(np.corrcoef(ics))


def unit_stats(corr: np.ndarray, labels: np.ndarray, ic_chrom: np.ndarray) -> list[dict]:
    """One dict per cluster label (>= 0): size, chromatophores, and summary of the within-cluster |Pearson r|.

    corr: (n_ic, n_ic) from lab_ic_correlation; labels: (n_ic,) cluster id per IC; ic_chrom: (n_ic,) chromatophore id per IC.
    """
    out = []
    for lab in sorted(set(labels.tolist())):
        if lab < 0:
            continue
        idx = np.flatnonzero(labels == lab)
        sub = corr[np.ix_(idx, idx)]
        off = sub[np.triu_indices(len(idx), k=1)]
        out.append({
            "unit": int(lab),
            "n_ics": len(idx),
            "n_chroms": len(set(ic_chrom[idx].tolist())),
            "ic_index": idx.tolist(),
            "chroms": sorted(set(int(c) for c in ic_chrom[idx])),
            "r_mean": float(off.mean()) if off.size else None,
            "r_min": float(off.min()) if off.size else None,
            "r_max": float(off.max()) if off.size else None,
            "r_nan": bool(np.isnan(off).any()),
        })
    return out
