#!/usr/bin/env bash
# POSITIVE CONTROL on PHerc. 172 w087: same renderer flags + same ink.sh as the PHerc1447 runs.
# usage: ./control.sh CX CY [W]   (crop origin/size in render pixels; pick CX,CY = 8 x the team-JPG pixel of visible text)
set -euo pipefail; cd "$(dirname "$0")"; source config.env
CT172=$S3/PHerc0172/volumes/20241024131838-7.910um-53keV-masked.zarr
CX=${1:?give CX}; CY=${2:?give CY}; W=${3:-2048}; name=ctrl172_w087_${CX}_${CY}; t0=$(date +%s)
"$BIN/vc_render_tifxyz" --volume "$CT172" -g 0 --scale 1 -s control172/w087.tifxyz --num-slices 28 --slice-step 1 \
  --crop-x $CX --crop-y $CY --crop-width $W --crop-height $W --cache-gb 8 --zarr-output "renders/$name.zarr" 2>&1 | tail -3
echo "render: $(( $(date +%s) - t0 ))s"
python3 composite.py "renders/$name.zarr"
./ink.sh "$name"
