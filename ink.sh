#!/usr/bin/env bash
# Ink inference on a rendered 28-layer surface volume, on MPS. usage: ./ink.sh seed_5452_4100_22772
set -euo pipefail; cd "$(dirname "$0")"; name="$1"; mkdir -p predictions logs
export PYTHONPATH="$PWD/villa/vesuvius/src" PYTORCH_ENABLE_MPS_FALLBACK=1
t0=$(date +%s)
.inkenv/bin/python -m vesuvius.ink_detection.inference.infer "renders/$name.zarr" \
  checkpoints/ink_9um/hybrid_3d2d-seed42/step-075000.pth "predictions/$name.tif" \
  --overlap 0.5 --blend-mode hann --batch-size 4 --direction both --no-compile 2>&1 | tee "logs/ink_$name.log"
echo "inference wall time: $(( $(date +%s) - t0 ))s" | tee -a "logs/ink_$name.log"
.inkenv/bin/python - "$name" <<'PY'
import sys, glob, numpy as np, tifffile, imageio.v3 as iio
n = sys.argv[1]
for f in sorted(glob.glob(f"predictions/{n}*.tif")):
    p = tifffile.imread(f).astype(np.float32); p = p / max(p.max(), 1e-6)
    iio.imwrite(f.replace(".tif", "_view.png"), (p * 255).astype(np.uint8))
    print(f"{f}: shape {p.shape}, mean {p.mean():.3f}, >0.5: {(p > 0.5).mean():.3%}")
PY
