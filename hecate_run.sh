#!/usr/bin/env bash
# Render a surface at 9.6 um (all three axes) and run Hecate in both directions on MPS.
# usage: ./hecate_run.sh NAME SEG_DIR CT_URL SRC_UM [CX CY W]    (crop in source-resolution pixels, optional)
set -euo pipefail; cd "$(dirname "$0")"; source config.env
NAME=$1; SEG=$2; CT=$3; SRC=$4; CX=${5:-}; CY=${6:-}; W=${7:-}
read SC SS <<<"$(python3 -c "print(round($SRC/9.6,5), round(9.6/$SRC,5))")"
CROP=""; [ -n "$CX" ] && CROP="--crop-x $(python3 -c "print(int($CX*$SC))") --crop-y $(python3 -c "print(int($CY*$SC))") --crop-width $(python3 -c "print(int($W*$SC))") --crop-height $(python3 -c "print(int($W*$SC))")"
mkdir -p renders predictions/hecate logs; t0=$(date +%s)
echo "render $NAME at 9.6 um: scale $SC, slice-step $SS, 20 slices $CROP"
"$BIN/vc_render_tifxyz" --volume "$CT" -g 0 --scale $SC -s "$SEG" --num-slices 20 --slice-step $SS \
   $CROP --cache-gb 8 --zarr-output "renders/h96_$NAME.zarr" > "logs/h96_render_$NAME.log" 2>&1
grep -i "rendering" "logs/h96_render_$NAME.log" | tail -1; echo "render: $(( $(date +%s)-t0 ))s"
for dir in ${DIRS:-fwd rev}; do
  R=""; [ $dir = rev ] && R="--reverse"
  .inkenv/bin/python hecate/hecate.py --checkpoint hecate/hecate_9.6um.pth --input "renders/h96_$NAME.zarr" \
     --spacing-um 9.6 --output "predictions/hecate/${NAME}_$dir.png" --device mps $R ${HECATE_ARGS:---stride 64 --batch-size 16} > "logs/hecate_${NAME}_$dir.log" 2>&1 \
     || { echo "hecate $dir FAILED:"; tail -5 "logs/hecate_${NAME}_$dir.log"; exit 1; }
  echo "hecate $dir done: $(( $(date +%s)-t0 ))s"
done
