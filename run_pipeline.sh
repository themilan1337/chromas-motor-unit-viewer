#!/usr/bin/env bash
# Runs the lab's CHROMAS CLI step by step on the tutorial video. Usage: ./run_pipeline.sh <step> [extra args]
# Needs: .venv (see README), work/sepia_example.mp4, work/sepia_2classes_cpu.pth (see fetch_data.sh)
set -euo pipefail
cd "$(dirname "$0")"
export PYTHONPATH="$PWD/shim"        # decord stand-in, macOS arm64 has no decord wheel
export PYTORCH_ENABLE_MPS_FALLBACK=1
step=$1; shift
DS=work/sepia_example.dataset
mkdir -p runs
case $step in
  chunk)    cmd=(chunk work/sepia_example.mp4 "$@") ;;
  segment)  cmd=(segment $DS -w work/sepia_2classes_cpu.pth "$@") ;;
  analyse)  cmd=(analyse cluster ics $DS "$@") ;;
  *)        cmd=("$step" $DS "$@") ;;
esac
.venv/bin/python shim/chromas_nocuda.py "${cmd[@]}" 2>&1 | grep -v -E "UserWarning|self\.(make_parser|parse_args)|parser = |pieces = " | tee "runs/$step.log"
