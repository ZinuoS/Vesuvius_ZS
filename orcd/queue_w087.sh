#!/usr/bin/env bash
# Queue ink inference for the 48 mm w087 render on Engaging, then pull the maps back and run textness.
# usage (from the Mac Terminal, in the repo):
#   ./orcd/queue_w087.sh push     rsync renders/ctrl172_w087_48mm.zarr to the cluster and sbatch ink_infer (S=2, both directions)
#   ./orcd/queue_w087.sh status   squeue for your jobs
#   ./orcd/queue_w087.sh fetch    rsync predictions back to predictions/orcd/ and run textness.py on rev, fwd and the team window
set -euo pipefail; cd "$(dirname "$0")/.."
U=${ORCD_USER:-zinuos}; H=orcd-login001.mit.edu; R=${VESUVIUS_HOME:-vesuvius}; name=ctrl172_w087_48mm
case "${1:-}" in
  push)
    [ -d renders/$name.zarr ] || { echo "render first: ./render_w087_48mm.sh"; exit 1; }
    rsync -a --info=progress2 orcd/ "$U@$H:$R/orcd/"
    rsync -a --info=progress2 "renders/$name.zarr" "$U@$H:$R/renders/"
    ssh "$U@$H" "cd $R && mkdir -p logs predictions && sbatch orcd/ink_infer.sbatch renders/$name.zarr 2" ;;
  status) ssh "$U@$H" "squeue -u $U -o '%.10i %.12j %.10P %.8T %.10M %.6D %R'" ;;
  fetch)
    mkdir -p predictions/orcd predictions/textness
    rsync -a --info=progress2 "$U@$H:$R/predictions/${name}_S2*.tif" predictions/orcd/
    rsync -a "$U@$H:$R/logs/ink_*.out" logs/ 2>/dev/null || true
    # textness: constrained test at the known line direction (theta 6, L 5-7.5 mm), null 100. Team window for reference:
    # window origin (2400,3000) px / 8 = (300,375) on the team map, width 6070/8 = 759.
    python3 textness.py control172/team_ink_w087_ds8.jpg --um 63.28 --crop 300 375 759 --theta 6 --line-band 5 7.5 --null 100 --name w087_48mm_team
    python3 textness.py predictions/orcd/${name}_S2_reverse.tif --um 7.91 --theta 6 --line-band 5 7.5 --null 100 --name w087_48mm_S2_rev
    python3 textness.py predictions/orcd/${name}_S2.tif         --um 7.91 --theta 6 --line-band 5 7.5 --null 100 --name w087_48mm_S2_fwd
    echo "bar (E16): team window z ~ +13; a model with the rhythm needs z > 3 on rev and not on fwd" ;;
  *) sed -n '2,6p' "$0" ;;
esac
