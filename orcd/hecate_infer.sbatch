#!/bin/bash
#SBATCH -J hecate
#SBATCH -p mit_normal_gpu
#SBATCH --gres=gpu:1
#SBATCH -c 8
#SBATCH --mem=48G
#SBATCH -t 02:00:00
#SBATCH -o logs/hecate_%j.out
# usage: sbatch orcd/hecate_infer.sbatch renders/h96_<name>.zarr      (9.6 um render; runs fwd and rev at full overlap)
set -euo pipefail; cd ${VESUVIUS_HOME:-$HOME/vesuvius}; mkdir -p logs predictions/hecate
Z=$1; n=$(basename "$Z" .zarr); export TMPDIR=${TMPDIR:-$PWD/tmp}; mkdir -p "$TMPDIR"
for d in fwd rev; do R=""; [ $d = rev ] && R="--reverse"
  .venv/bin/python checkpoints/hecate/hecate.py --checkpoint checkpoints/hecate/hecate_9.6um.pth --input "$Z" \
    --spacing-um 9.6 --output "predictions/hecate/${n}_$d.png" --device cuda --precision bf16 --batch-size 8 $R
done
