#!/usr/bin/env bash
# Hecate on both PHerc.172 w087 control crops, scored against the team map. Baseline to beat (ink_9um, S2):
#   crop 5440_5120 corr 0.398 / AUC 0.746      crop 1200_9200 corr 0.266 / AUC 0.688
set -euo pipefail; cd "$(dirname "$0")"; source config.env
CT172=$S3/PHerc0172/volumes/20241024131838-7.910um-53keV-masked.zarr
for c in "5440 5120" "1200 9200"; do set -- $c
  [ -f predictions/hecate/ctrl172_w087_$1_$2_rev.png ] || ./hecate_run.sh ctrl172_w087_$1_$2 control172/w087.tifxyz "$CT172" 7.91 $1 $2 2048
  for d in fwd rev; do python3 bench_png.py predictions/hecate/ctrl172_w087_$1_$2_$d.png $1 $2 2048; done
done
