#!/usr/bin/env bash
# The whole run that produced out/: the lab's own CLI steps in order (logs in runs/), then the viewer. About 50 minutes on an Apple-silicon Mac,
# 41 of them in `segment`. Needs ./fetch_data.sh first. Chunks 1 and 2 were run on copies of the dataset, see README "How to run".
set -euo pipefail
cd "$(dirname "$0")"
./run_pipeline.sh chunk
./run_pipeline.sh segment
./run_pipeline.sh register --compute-videos False
./run_pipeline.sh stitch
./run_pipeline.sh area
# the default motion-marker filters find 0 markers on this video across the 3 chunks; these flags and one chunk give 28 (README, Limits)
./run_pipeline.sh slice --chunk-selection 0 --max-ecc 0.99 --max-area 1000 --min-num-motion-markers 4
./run_pipeline.sh ica --chunk 0
./run_pipeline.sh analyse --chunk 0
mkdir -p out/chunk0
.venv/bin/python -m mu_viewer.build work/sepia_example.dataset --out out/chunk0/viewer.html --ica-group ica_chunk_0 --ref-chunk 0 --csv-dir out/chunk0 \
  --source "CHROMAS 0.1.1 on chunk 0 of the lab's tutorial video sepia_example.mp4 (198 frames each)."
.venv/bin/python -m mu_viewer.within_between work/sepia_example.dataset ica_chunk_0 0 | tee runs/within_between_chunk0.txt
