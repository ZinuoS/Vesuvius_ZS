#!/usr/bin/env bash
# Headless grow + render + composite for every seed in seeds.txt. Logs commands, wall time, failures.
set -u; cd "$(dirname "$0")"; source config.env
export SURF_URL CT_URL  # seeds.py also needs CT_URL
sed "s#NORMAL_GRIDS_PLACEHOLDER#$NORMAL_GRIDS#" params.json > .params.json
mkdir -p patches renders logs; LOG=logs/run_$(date +%Y%m%d_%H%M%S).log
echo "build: $(defaults read /Applications/VC3D.app/Contents/Info CFBundleVersion 2>/dev/null || plutil -extract CFBundleShortVersionString raw /Applications/VC3D.app/Contents/Info.plist 2>/dev/null)" | tee -a "$LOG"
while read -r x y z; do
  [ -z "${x:-}" ] && continue
  name="seed_${x}_${y}_${z}"; t0=$(date +%s)
  echo "== $name  $(date)" | tee -a "$LOG"
  before=$(ls -d patches/auto_grown_* 2>/dev/null)
  grow() { "$BIN/vc_grow_seg_from_seed" -v "$SURF_URL" -t patches -p .params.json --seed "$x" "$y" "$z" >> "$LOG" 2>&1; }
  grow; rc=$?
  if [ $rc -eq 137 ]; then echo "   killed at launch (exit 137), retrying once" | tee -a "$LOG"; sleep 2; grow; rc=$?; fi
  [ $rc -ne 0 ] && { echo "   GROW FAILED (exit $rc)" | tee -a "$LOG"; continue; }
  seg=$(comm -13 <(echo "$before") <(ls -d patches/auto_grown_*) | tail -1)
  [ -z "$seg" ] && { echo "   no new patch written" | tee -a "$LOG"; continue; }
  mv "$seg" "patches/$name"; seg="patches/$name"
  echo "   grown -> $seg  ($(( $(date +%s) - t0 ))s)" | tee -a "$LOG"
  "$BIN/vc_render_tifxyz" --volume "$CT_URL" -g 0 --scale 1 -s "$seg" --num-slices "$NUM_SLICES" --slice-step 1 \
      --cache-gb 8 --zarr-output "renders/$name.zarr" >> "$LOG" 2>&1 \
    || { echo "   RENDER FAILED (exit $?)" | tee -a "$LOG"; continue; }
  python3 composite.py "renders/$name.zarr" 2>&1 | tee -a "$LOG"
  python3 qa.py "$seg" 2>&1 | tee -a "$LOG"
  # make the patch visible in VC3D (Volume Package -> Reload Surfaces)
  cp -R "$seg" "$HOME/.VC3D/remote_cache/open_data/segments/$SCROLL/${VOLID}_editable/" 2>/dev/null
  echo "   done in $(( $(date +%s) - t0 ))s" | tee -a "$LOG"
done < "${SEEDS:-seeds.txt}"
echo "all done: $LOG"
