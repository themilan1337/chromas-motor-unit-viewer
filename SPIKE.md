# Spike: does CHROMAS run, and what is "motion covariance" in the lab's code

Date of the runs: 8 to 9 Nov 2026, one Apple-silicon Mac, no GPU, Python 3.12.13. Logs of every run are in `runs/`.

## What runs

The lab's public code is CHROMAS 0.1.1 (PyPI, BSD 3-Clause; GitLab https://gitlab.mpcdf.mpg.de/mpibr/laur/cuttlefish/chromas, the clone we read is commit a1fe9de, 24 Nov 2025). Its `chromas/source` tree is identical to the installed 0.1.1 wheel except for build artefacts (checked with `diff -rq`). The tutorial video `sepia_example.mp4` (1000 x 1000, 1000 frames, 20 fps), the segmentation weights and the training data are the lab's CC0 Edmond deposit, https://doi.org/10.17617/3.MJI3HA (`fetch_data.sh`).

| Step (lab's CLI, unmodified) | Result | Log |
|---|---|---|
| `chunk` | 3 chunks | `runs/chunk.log` |
| `segment` with the lab's weights | ok, 41.5 min on MPS | `runs/segment.log`, `runs/chain.txt` |
| `register`, `stitch`, `area` | ok; 52 chromatophores in the stitched reference | `runs/register.log`, `runs/stitch.log`, `runs/area.log` |
| `slice` with default flags | **fails: 0 motion markers** (needs 4) | `runs/slice_default_flags_0_markers.log` |
| `slice --chunk-selection 0 --max-ecc 0.99 --max-area 1000 --min-num-motion-markers 4` | ok: 28 motion markers, 11 chromatophores sliced | `runs/slice.log` |
| `ica --chunk 0`, `analyse cluster ics --chunk 0` | ok: 49 ICs, 11 clusters | `runs/ica.log`, `runs/analyse.log` |
| same on chunk 1 / chunk 2 (copies of the dataset) | chunk 1: only 2 chromatophores, 8 ICs, 1 cluster; chunk 2: 8 chromatophores, 33 ICs, 6 clusters | `runs/chunk1.pipeline.log`, `runs/chunk2.pipeline.log` |
| `motor_units/cluster_size.py`, `mu_cooccurence.py` on chunk 0 output | run, but 11 chromatophores say nothing | `runs/motor_units_*.txt` |

Four things had to be worked around, all in `shim/` and `cpu_weights.py`, none by editing the lab's files:
1. `segment` calls `.cuda()` unconditionally (segmentation_neuralnet.py lines 110, 176, 345) and builds a half-precision model: the wrapper maps `.cuda()` to MPS.
2. The published weights are CUDA tensors and `torch.load` has no `map_location`: `cpu_weights.py` rewrites the same values as CPU tensors.
3. `decord` has no macOS arm64 wheel: `shim/decord` is a small OpenCV stand-in.
4. `slice` calls `np.cross` on 2-D vectors (slicing.py lines 137 to 139). NumPy 2.0 removed that, and the lab's pyproject asks for numpy ^2.2.2, so the pinned stack raises "Both input arrays must be (arrays of) 3-dimensional vectors" (`runs/slice_unpatched_numpy2_error.log`). The wrapper restores the 2-D result a0*b1 - a1*b0. This looks like a bug in the pinned stack.

Segmentation quality looks right by eye: `out/segmentation_check_frame0.png` (left frame 0, right the segmentation of the lab's weights in red) covers the dark chromatophores and the small orange ones.

## How motion covariance is computed in the lab's code

There is no function or output named covariance of motion in CHROMAS 0.1.1 or in `motor_units/`; the grep for `corrcoef\|pearson` finds only the three corrcoef calls listed below and unrelated pearsonr calls in `motor_units/mu_structure.py` (chromatophore count vs area, not motion). What the code computes, in the order it happens:

1. `chromas/source/ica/ica_utils.py`, `compute_pca_ica`: per chromatophore, the slice-area matrix is detrended, differenced over time, only positive differences (expansion) are kept, smoothed with a Gaussian along the slices, and FastICA gives independent components (ICs). The number of ICs is the PCA elbow (kneed).
2. `chromas/source/analysis/ica_slice_clustering.py`, line 144: `corr = np.abs(np.corrcoef(ICs.data[IC_mask.data]))`. This is the absolute Pearson correlation between the time courses of every pair of ICs from all chromatophores. It is the only matrix that plays the role of "motion covariance".
3. `chromas/source/analysis/clustering_utils.py`, `cluster_correlation`: Affinity Propagation on `corr - 1` (default), or HDBSCAN, or Ward. Each cluster is the putative motor unit.
4. Two siblings with the same idea on other quantities: `areas_clustering.py` line 94 (`np.corrcoef` of chromatophore area time series) and `sliceareas_clustering.py` line 104 (of slice areas).
5. `motor_units/*.py` do not compute a correlation of motion. They read a CSV with the cluster labels (columns `chrom_id`, `label`, `n_ics`, `epicenter_x`, `epicenter_y`) and compute sizes, co-occurrence and distances. CHROMAS 0.1.1 does not write that CSV (no `chrom_all` string in the package), so `mu_viewer.build --csv-dir` writes one in the columns the scripts read. That schema is our reconstruction from reading four scripts.

The eLife paper (https://elifesciences.org/reviewed-preprints/110074, Methods, fetched 9 Nov 2026) says the same in words: ICs are clustered "using pairwise Pearson correlation as the similarity metric" with Affinity Propagation. The lab's wording "the higher the motion covariance (ideally = 1), the better" is therefore best read as this normalised value; that reading is ours, not the lab's definition.

## What the sample data can and cannot say

`runs/within_between.txt` (`python -m mu_viewer.within_between`): chunk 0, mean |r| of IC pairs inside one cluster 0.122 against 0.052 across clusters, largest pair 0.326, none at or above 0.5. Chunk 2: 0.126 against 0.052, largest pair 0.501, one pair at or above 0.5, none at or above 0.9. Within-cluster values sit above between-cluster values, but nowhere near 1. With 8 to 11 chromatophores and 196 frames this is expected and is not evidence about motor units. Two FastICA fits did not converge in chunk 0 (`runs/ica.log`).

## Plan for the viewer (what is built, what is next)

Built (`mu_viewer/`, one self-contained HTML file, no network):
- reads the ICs, labels, epicenters and orientations that `chromas ica` and `chromas analyse cluster ics` stored;
- recomputes the lab's correlation matrix with the lab's own call and re-runs the lab's own clustering function on it; the stored labels come back identical (the check is printed into the page header: "Reproduction check ... True");
- per estimated unit: its chromatophores on the video frame, the radial slices belonging to it, the time courses of its ICs, the |r| matrix, and mean, min and max |r| as a labelled reading aid (the lab defines no per-unit number);
- `units.csv` and the CSV for the lab's `motor_units` scripts.

Next, in order of value:
1. Find out how the lab picks `--max-area`, `--max-cv` and `--max-ecc` for their own video; with defaults the tutorial video gives 0 markers and with our loosened flags only one chunk works. A multi-chunk run needs chromatophores that stay tracked across chunks (the default run over all three chunks found 0 markers; the lab's README example flags `--max-area 400 --max-cv 0.1` were not tried).
2. Run on a recording the lab considers representative (not public as far as we found). Then the numbers can be compared with the paper's cluster sizes (mean 9.0 ICs per unit in the paper's HF+S set).
3. A slice-level view (`analyse cluster slices` output), which is what Figure 1 of the paper shows.
4. A `chromas-mu-viewer <dataset>` entry point and a short test on a tiny stored dataset, so the lab can link it as an extra tool.

Items 2 to 4 are small once item 1 is answered; item 1 depends on the lab.
