"""python -m mu_viewer.build <dataset.zarr dir> --out viewer.html [--ica-group ica|ica_chunk_0] [--ref-chunk 0]

Reads what `chromas ica` and `chromas analyse cluster ics` stored in the dataset, recomputes the IC correlation matrix with the lab's own
call (it is not stored by CHROMAS), checks it against the stored labels, and writes one self-contained HTML file.
"""
import argparse
import csv
from pathlib import Path

import numpy as np

from .core import lab_ic_correlation, unit_stats
from .render import png_data_uri, render


def assemble(ics, labels, ic_chrom, ic_comp, chrom_ids, xy, orient, slice_labels, image, n_slices, source=""):
    """Pure function: arrays in, payload dict out (tested on synthetic data)."""
    corr = lab_ic_correlation(ics)
    stats = unit_stats(corr, labels, ic_chrom)
    for u in stats:
        idx = u["ic_index"]
        sub = corr[np.ix_(idx, idx)]
        u["corr"] = [[None if np.isnan(v) else round(float(v), 4) for v in row] for row in sub]
        u["members"] = [{"chrom": int(ic_chrom[i]), "comp": int(ic_comp[i]), "series": [round(float(v), 5) for v in ics[i]]} for i in idx]
        for k in ("r_mean", "r_min", "r_max"):
            u[k] = None if u[k] is None or np.isnan(u[k]) else round(u[k], 4)
        del u["ic_index"]
    pts = np.asarray(xy, float)
    d = np.sqrt(((pts[:, None] - pts[None]) ** 2).sum(-1)) + np.eye(len(pts)) * 1e9
    wedge_r = float(0.45 * np.median(d.min(1))) if len(pts) > 1 else 10.0
    return {
        "meta": {"source": source},
        "image": png_data_uri(image),
        "size": list(image.shape[:2]),
        "n_slices": int(n_slices),
        "wedge_r": wedge_r,  # display only
        "chroms": [{"id": int(c), "x": float(p[1]), "y": float(p[0]), "orient": float(o)} for c, p, o in zip(chrom_ids, pts, orient)],
        "slice_labels": {str(int(c)): [int(v) for v in sl] for c, sl in zip(chrom_ids, slice_labels)},
        "units": stats,
    }


def load_dataset(dataset, ica_group, ref_chunk):
    """Mirror of the first half of CHROMAS ica_slice_cluster(): same loop, same masks."""
    import cv2
    import xarray as xr

    ica = xr.open_zarr(dataset, group=ica_group)
    chroms = np.asarray(ica.chroms2analyse.data.compute() if hasattr(ica.chroms2analyse.data, "compute") else ica.chroms2analyse.data)
    n_ic = ica.elbow_point.sel(chrom_id=chroms).data.compute().astype(int)
    src = ica.ica_sources.sel(chrom_id=chroms).data.compute()  # (chrom, diff, component)
    ics, ic_chrom, ic_comp = [], [], []
    for i, c in enumerate(chroms):
        for k in range(n_ic[i]):
            ics.append(src[i, :, k]); ic_chrom.append(c); ic_comp.append(k)
    labels_2d = ica.IC_labels.sel(chrom_id=chroms).data.compute()
    labels = np.array([labels_2d[list(chroms).index(c), k] for c, k in zip(ic_chrom, ic_comp)])
    chunk = xr.open_zarr(dataset, group=f"chunk_{ref_chunk}")
    centers = chunk.centers.sel(frame=0, non_motion_marker=chroms).compute().data
    orient = chunk.orientation_angles.sel(frame=0, non_motion_marker=chroms).compute().data
    slice_labels = ica.slice_labels.sel(chrom_id=chroms).compute().data
    path = chunk.segmentation.attrs["chunk_path"]
    if not Path(path).exists():
        path = str(Path(dataset).parent / Path(path).name)
    cap = cv2.VideoCapture(path); ok, frame = cap.read(); assert ok, path
    return dict(ics=np.array(ics), labels=labels, ic_chrom=np.array(ic_chrom), ic_comp=np.array(ic_comp), chrom_ids=chroms,
                xy=centers, orient=orient, slice_labels=slice_labels, image=cv2.cvtColor(frame, cv2.COLOR_BGR2RGB),
                n_slices=slice_labels.shape[1])


def lab_csv_rows(ic_chrom, ic_comp, labels, chrom_ids, xy):
    """One row per IC with the columns the lab's motor_units scripts read (chrom_id, label, n_ics, epicenter_x, epicenter_y).

    RECONSTRUCTED schema: CHROMAS 0.1.1 writes no ics_chunk_*_chrom_all.csv, so the columns were read off cluster_size.py, mu_cooccurence.py,
    distances.py and mu_structure.py. Epicenter x is the column coordinate, y the row coordinate (same as the viewer).
    """
    pos = {int(c): p for c, p in zip(chrom_ids, xy)}
    n_ics = {int(c): int((np.asarray(ic_chrom) == c).sum()) for c in chrom_ids}
    return [[int(c), int(k), int(lab), n_ics[int(c)], float(pos[int(c)][1]), float(pos[int(c)][0])]
            for c, k, lab in zip(ic_chrom, ic_comp, labels)]


def check_against_lab_clustering(corr, labels):
    """Re-run the lab's own clustering on our recomputed matrix; the labels must come back identical (up to renaming)."""
    from chromas.source.analysis.clustering_utils import cluster_correlation

    again = cluster_correlation(corr, "AffinityPropagation", damping=0.5, max_iter=200, convergence_iter=15)
    pairs = set(zip(labels.tolist(), again.tolist()))
    return len(pairs) == len(set(labels.tolist())) == len(set(again.tolist()))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("dataset"); ap.add_argument("--out", default="viewer.html")
    ap.add_argument("--ica-group", default="ica"); ap.add_argument("--ref-chunk", type=int, default=0)
    ap.add_argument("--csv-dir", default=None, help="also write units.csv and ics_chunk_chrom_all.csv (the input of the lab's motor_units scripts) here")
    ap.add_argument("--source", default="")
    a = ap.parse_args()
    d = load_dataset(a.dataset, a.ica_group, a.ref_chunk)
    corr = lab_ic_correlation(d["ics"])
    same = check_against_lab_clustering(corr, d["labels"])
    print(f"{len(d['ics'])} ICs, {len(set(d['labels'].tolist()))} clusters; lab clustering reproduced from recomputed matrix: {same}")
    payload = assemble(**d, source=a.source + f" Reproduction check (recomputed matrix gives the stored clustering): {same}.")
    print("wrote", render(payload, a.out))
    if a.csv_dir:
        out = Path(a.csv_dir); out.mkdir(parents=True, exist_ok=True)
        with open(out / "units.csv", "w", newline="") as f:
            w = csv.writer(f); w.writerow(["unit", "n_chroms", "n_ics", "r_abs_mean", "r_abs_min", "r_abs_max", "chrom_ids"])
            for u in payload["units"]:
                w.writerow([u["unit"], u["n_chroms"], u["n_ics"], u["r_mean"], u["r_min"], u["r_max"], " ".join(map(str, u["chroms"]))])
        with open(out / "ics_chunk_chrom_all.csv", "w", newline="") as f:
            w = csv.writer(f); w.writerow(["chrom_id", "ic", "label", "n_ics", "epicenter_x", "epicenter_y"])
            w.writerows(lab_csv_rows(d["ic_chrom"], d["ic_comp"], d["labels"], d["chrom_ids"], d["xy"]))


if __name__ == "__main__":
    main()
