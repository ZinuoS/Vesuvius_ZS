#!/usr/bin/env bash
# Download the w087 mesh (x/y/z.tif + meta.json) and the team's ink prediction (1/8 scale JPG) for PHerc. 172.
set -euo pipefail; cd "$(dirname "$0")"
B=https://vesuvius-challenge-open-data.s3.us-east-1.amazonaws.com/PHerc0172/segments/20251112000002-w087_20251112000002214_flatboi
D=control172/w087.tifxyz; mkdir -p "$D"
for f in x.tif y.tif z.tif meta.json; do curl -fsS -o "$D/$f" "$B/mesh/20251112000002-on-20241024131838-7.91um.tifxyz/$f" && echo "got $f"; done
curl -fsS -o control172/team_ink_w087_ds8.jpg "$B/ink-detection/downsampled/PHerc0172-20251112000002-7.91um-53keV-volume-20241024131838-20251222202946-timesformer_scroll5_november19-tile64-stride16-ds8.jpg" && echo "got team ink jpg"
ls -la "$D" control172
