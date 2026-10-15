#!/usr/bin/env bash
# Render a 48 mm x 48 mm window of PHerc.172 w087 at full resolution (7.91 um, 28 layers) for the textness test,
# which needs >= 32 mm of field (docs/notebook.md E16). Window: render px x 2400-8470, y 3000-9070; contains control crop 1.
# Run from Terminal on the Mac (VC3D binaries). Output renders/ctrl172_w087_48mm.zarr, about 1.3 GB. ~10-20 min on the Air.
set -euo pipefail; cd "$(dirname "$0")"; source config.env
CT172=$S3/PHerc0172/volumes/20241024131838-7.910um-53keV-masked.zarr
X0=${1:-2400}; Y0=${2:-3000}; W=${3:-6070}; name=ctrl172_w087_48mm; mkdir -p renders logs; t0=$(date +%s)
[ -d control172/w087.tifxyz ] || ./fetch172.sh
"$BIN/vc_render_tifxyz" --volume "$CT172" -g 0 --scale 1 -s control172/w087.tifxyz --num-slices 28 --slice-step 1 \
  --crop-x $X0 --crop-y $Y0 --crop-width $W --crop-height $W --cache-gb 8 --zarr-output "renders/$name.zarr" 2>&1 | tee "logs/render_$name.log" | tail -3
echo "render: $(( $(date +%s) - t0 ))s  ($(du -sh renders/$name.zarr | cut -f1))" | tee -a "logs/render_$name.log"
python3 composite.py "renders/$name.zarr"
echo "next: ./orcd/queue_w087.sh push      (rsync to Engaging and sbatch)"
