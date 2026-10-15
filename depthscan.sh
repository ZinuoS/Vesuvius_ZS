#!/usr/bin/env bash
# Slide the model's 17-layer depth window through the 28-layer render; score each window.
# usage: ./depthscan.sh <render-name> [starts...]   default starts: 0 2 4 6 8 10 11  (6 = default centred window)
set -euo pipefail; cd "$(dirname "$0")"; n="$1"; shift; starts=("${@:-0 2 4 6 8 10 11}")
export PYTHONPATH="$PWD/villa/vesuvius/src" PYTORCH_ENABLE_MPS_FALLBACK=1
mkdir -p predictions/scan logs; t0=$(date +%s)
for S in ${starts[@]}; do
  E=$((S + 17)); echo "== window layers $S..$((E-1))  (offset $((S-6)) from default)"
  .inkenv/bin/python -m vesuvius.ink_detection.inference.infer "renders/$n.zarr" \
    checkpoints/ink_9um/hybrid_3d2d-seed42/step-075000.pth "predictions/scan/${n}_S${S}.tif" \
    --overlap 0.5 --blend-mode hann --batch-size 4 --direction both --no-compile \
    --layer-start $S --layer-end $E > "logs/scan_${n}_S${S}.log" 2>&1
  echo "   done ($(( $(date +%s) - t0 ))s elapsed)"
done
[[ "$n" == ctrl172_w087_* ]] && .inkenv/bin/python bench172.py predictions/scan/${n}_S*.tif | sort -t= -k2 -r
