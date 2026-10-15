#!/usr/bin/env bash
# POSITIVE CONTROL on PHerc1447 itself: grow + render + QA + ink at the location where the team
# announced readable text (Discord #announcements, 24 Sep 2026): ~(4144, 2742, 12557), 8.64 um volume.
set -euo pipefail; cd "$(dirname "$0")"; source config.env; export SURF_URL CT_URL
python3 near.py 4144 2742 12557 --n 3 --out seeds_1447text.txt
SEEDS=seeds_1447text.txt ./run.sh
while read -r x y z; do n="seed_${x}_${y}_${z}"; [ -d "renders/$n.zarr" ] && ./ink.sh "$n"; done < seeds_1447text.txt
