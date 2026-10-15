#!/bin/bash
#SBATCH -J ink_infer
#SBATCH -p mit_normal_gpu
#SBATCH --gres=gpu:1
#SBATCH -c 8
#SBATCH --mem=32G
#SBATCH -t 01:00:00
#SBATCH -o logs/ink_%j.out
# usage: sbatch orcd/ink_infer.sbatch renders/<name>.zarr [layer_start]     (run from ~/vesuvius)
set -euo pipefail; cd ${VESUVIUS_HOME:-$HOME/vesuvius}; mkdir -p logs predictions
Z=$1; S=${2:-2}; n=$(basename "$Z" .zarr)
export PYTHONPATH="$PWD/villa/vesuvius/src"
nvidia-smi --query-gpu=name,memory.total --format=csv,noheader
t0=$(date +%s)
.venv/bin/python -m vesuvius.ink_detection.inference.infer "$Z" checkpoints/ink_9um/hybrid_3d2d-seed42/step-075000.pth \
  "predictions/${n}_S${S}.tif" --overlap 0.5 --blend-mode hann --batch-size 16 --direction both \
  --layer-start $S --layer-end $((S+17)) --amp-dtype bf16
echo "wall: $(( $(date +%s)-t0 ))s"
