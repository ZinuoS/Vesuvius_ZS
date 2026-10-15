# Headless grow / render / inspect on the Mac (PHerc1447)

Everything runs from Terminal on the Mac, which is where VC3D and the S3 bucket are reachable.
Run log, wall times and failures land in `logs/`. This is the "documented end-to-end run" progress-prize artefact.

## 0. One-time
    cd ~/Desktop/Projects/vesuvius
    python3 -m pip install zarr fsspec aiohttp requests imageio numpy tifffile
    /Applications/VC3D.app/Contents/MacOS/vc_grow_seg_from_seed --help | head   # confirms the CLIs are in the bundle

## 1. Positive control (seeds.txt already holds 3 centre vertices of the team's published 1447 patches)
    ./run.sh
Expected: three `patches/seed_*` folders (x/y/z.tif + meta.json), three `renders/seed_*.zarr`,
and `renders/seed_*_max.png / _mid.png / _sheet.png`. Open the PNGs: horizontal + vertical fibres visible = good patch.
Time: a few minutes per seed on the Air at 35 generations; first run streams chunks, later runs hit the cache.

## 2. New seeds anywhere on the surface prediction (level-3 pyramid, ~2 MB read)
    source config.env; export SURF_URL
    python3 seeds.py --z 22000 24600 --n 8 --min-sep 600 --append
    ./run.sh
Grow bigger by raising GENERATIONS in config.env (and "generations" in params.json; keep both equal).

## 3. Ink inference
On the Air: `./ink.sh <name>` (MPS, see `setup_ink.sh`). On the MIT ORCD cluster: see `orcd/README.md`.
Original recipe, for reference:
Copy `renders/<name>.zarr` to the GPU machine and follow the ink_9um recipe in the First Letters workflow post:
    vesuvius.ink_detection.inference.infer <name>.zarr checkpoints/ink_9um/hybrid_3d2d-seed42/step-075000.pth out.tif --direction both

## Files
config.env   scroll / volume / surface-prediction URLs, normal-grid cache path, generations, slice count
params.json  tracer parameters passed to vc_grow_seg_from_seed (same tracer the GUI GrowPatch uses)
seeds.py     picks spaced seed voxels from the m7 recto prediction
run.sh       grow -> render 28-layer surface volume -> composite PNGs, per seed
composite.py max-intensity / middle-layer / 3x3 contact sheet from a rendered zarr
