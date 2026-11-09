# CHROMAS motor unit viewer

A viewer for the output of the CHROMAS pipeline (Ukrow, Renard et al.; https://gitlab.mpcdf.mpg.de/mpibr/laur/cuttlefish/chromas). It reads what `chromas ica` and `chromas analyse cluster ics` stored and shows, for each estimated motor unit, its chromatophores on the video frame, their radial slices, the time courses of its independent components and the pairwise |Pearson r| between them.

Live example on the lab's tutorial video: https://chromas-viewer.gorislavetsmilan123.workers.dev/

For a plain-language guide to the page, see `EXPLAINER.md`. What runs of the lab's code, and how "motion covariance" is computed there, is in `SPIKE.md`.

## What it does

- `mu_viewer/` writes one self-contained HTML file per run (no network, no CDN). It recomputes the correlation matrix with the lab's own call, re-runs the lab's own clustering function on it and checks that the stored labels come back; the result is printed in the page header.
- Per estimated unit it shows the chromatophores on the frame, the radial slices belonging to it, the time courses of its ICs, the |r| matrix, and the mean, min and max |r|. The per-unit summary is ours, a reading aid: the lab defines no per-unit number.
- It also writes `units.csv` and a CSV in the columns the lab's `motor_units` scripts read (`chrom_id`, `label`, `n_ics`, `epicenter_x`, `epicenter_y`). CHROMAS 0.1.1 writes no such file, so this schema is our reconstruction from reading four scripts.
- `shim/` and `cpu_weights.py` let the unmodified CHROMAS 0.1.1 run on a Mac (no CUDA, no decord wheel, NumPy 2 `np.cross`). None of the lab's files is edited. On a CUDA machine run the `chromas` commands directly.

## How to run

```
uv sync                      # Python 3.12, versions pinned in uv.lock (chromas==0.1.1)
./fetch_data.sh              # 227 MB CC0 deposit from Edmond, checks the sha256, makes CPU weights
./run_all.sh                 # the lab's CLI steps, then the viewer; about 50 min on an Apple-silicon Mac (41 min is `segment`)
uv run pytest -q             # 5 tests, synthetic data only, no network
python -m mu_viewer.build <dataset> --out viewer.html --ica-group ica_chunk_0 --ref-chunk 0 --csv-dir out/chunk0
python -m mu_viewer.within_between <dataset> ica_chunk_0 0
```

For your own recordings, run `chromas ica` and `chromas analyse cluster ics` first, then point `mu_viewer.build` at the dataset. Chunks 1 and 2 were run on copies of the dataset with the same `slice` flags and `--chunk 1` / `--chunk 2` (`runs/chunk1.pipeline.log`, `runs/chunk2.pipeline.log`).

## Results

All from saved logs in `runs/`, on the lab's tutorial video (`sepia_example.mp4`, 1000 frames in 3 chunks) and its published weights.

- The lab's pipeline runs end to end up to `analyse cluster ics`, with the flags and patches in `SPIKE.md`. With default flags `slice` finds 0 motion markers (`runs/slice_default_flags_0_markers.log`).
- Chunk 0: 28 motion markers, 11 chromatophores analysed, 49 ICs, 11 clusters. Chunk 2: 8 chromatophores, 33 ICs, 6 clusters. Chunk 1: 2 chromatophores, too few.
- Chunk 0: mean |r| of IC pairs 0.122 inside a cluster, 0.052 between clusters, largest pair 0.326. Chunk 2: 0.126 and 0.052, largest 0.501 (`runs/within_between.txt`). Nothing near 1.
- The viewer reproduces the lab's stored cluster labels from its recomputed matrix (shown in the page header). Tests: 5 passed (`runs/pytest.txt`).

## Limitations

- The tutorial video gives few analysable chromatophores per chunk, so these clusters test the code path and say nothing about motor units. We have no recording like the ones in the paper.
- One chunk at a time: across all three chunks the default and our loosened flags leave 0 to 1 motion markers.
- We did not try the lab's README example flags (`--max-area 400 --max-cv 0.1`).
- Two FastICA fits did not converge in chunk 0 (`runs/ica.log`).
- The viewer shows the IC-cluster level only, not the slice-level clustering of the paper's Figure 1.
- "Motion covariance" is read here as the absolute Pearson correlation of independent components (`ica_slice_clustering.py`, line 144), which is how the code and the paper's Methods describe it.
- Checked on macOS arm64 and in Chrome only.

## Next

1. Run on a representative recording, then compare cluster sizes with the paper.
2. A slice-level view (`analyse cluster slices` output).
3. A `chromas-mu-viewer <dataset>` entry point and a tiny stored test dataset.

## Sources and licence

- CHROMAS 0.1.1 (BSD 3-Clause), https://gitlab.mpcdf.mpg.de/mpibr/laur/cuttlefish/chromas.
- Tutorial video and weights: https://doi.org/10.17617/3.MJI3HA (Edmond, CC0).
- Renard et al., eLife 15:RP110074, https://elifesciences.org/reviewed-preprints/110074 (Methods: Affinity Propagation on pairwise Pearson correlation of FastICA components).
- This repository: MIT, see `LICENSE`.
