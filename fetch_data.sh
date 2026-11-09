#!/usr/bin/env bash
# Downloads the lab's public tutorial data (Edmond, CC0, doi:10.17617/3.MJI3HA, file Chromas2025.zip, 227 MB) into raw/ and work/.
# Takes the tutorial video and the segmentation weights and rewrites the weights with CPU tensors (see cpu_weights.py). Needs uv sync first.
set -euo pipefail
cd "$(dirname "$0")"
mkdir -p raw work
ZIP=raw/Chromas2025.zip
[ -f $ZIP ] || curl -L -o $ZIP "https://edmond.mpg.de/api/access/datafile/333866"
echo "94eded49191454b9d2a5134bcbe19e8049a3dbe02bced4e7b952b3c7f5ed2b3c  $ZIP" | shasum -a 256 -c -
unzip -oq $ZIP 'Chromas2025/tutorial_data/example.mp4' 'Chromas2025/model_weights/sepia_2classes_fcn_resnet50.pth' -d raw/ex
cp raw/ex/Chromas2025/tutorial_data/example.mp4 work/sepia_example.mp4
cp raw/ex/Chromas2025/model_weights/sepia_2classes_fcn_resnet50.pth work/sepia_2classes_fcn_resnet50.pth
.venv/bin/python cpu_weights.py work/sepia_2classes_fcn_resnet50.pth work/sepia_2classes_cpu.pth
