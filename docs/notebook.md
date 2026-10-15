# Vesuvius Challenge lab notebook
Repo root is the working folder. Started 14 Oct 2026. Everything here runs on a MacBook Air (Apple Silicon),
VC3D build afdb836-2026-10-14, streaming from s3://vesuvius-challenge-open-data. No CUDA anywhere.

## 0. Environment
- VC3D.app (Latest, 14 Oct) supplies the CLIs in /Applications/VC3D.app/Contents/MacOS: vc_grow_seg_from_seed, vc_render_tifxyz.
  Note: first launch of an ad-hoc-signed CLI from Terminal can die with exit 137 (macOS first-exec check); run.sh retries once.
- System python3 (3.9) + pip: zarr 2.18, fsspec, tifffile, imageio, numpy, matplotlib, scipy, pillow, imagecodecs.
- .inkenv (uv, Python 3.14): torch (MPS), + the ten packages vesuvius.ink_detection.inference actually imports (no C++ build,
  no nnunetv2/monai). Created by setup_ink.sh. villa/ is a sparse clone of ScrollPrize/villa (vesuvius/ only).
- hecate/: scrollprize/hecate hecate.py + hecate_9.6um.pth (MIT), run with --device mps.
- control172/: PHerc.172 w087 mesh (tifxyz) + the team's ink map (timesformer_scroll5_november19, 1/8 scale JPG).

## 1. Scripts (what / usage)
| script | purpose | usage |
|---|---|---|
| config.env | scroll, volume & surface-prediction URLs, normal-grid cache path, generations, slices | source config.env |
| seeds.py | pick on-surface, in-scroll seeds from the m7 recto prediction (level-3 pyramid) | python3 seeds.py --z Z0 Z1 --n N [--min-sep] [--ct-min 20] [--append] |
| near.py | seeds snapped to the prediction at full res near a target point | python3 near.py X Y Z --n 3 --out seeds_near.txt |
| run.sh | per seed: grow (35 gen) -> render 28 layers -> composite PNGs -> qa.py -> copy into VC3D project | SEEDS=file ./run.sh |
| composite.py | _max/_mid/_sheet PNGs from a rendered zarr; warns if all-zero | python3 composite.py renders/X.zarr |
| qa.py | 3x3 cross-section sheet (XY+YZ CT slices with mesh overlay) | python3 qa.py patches/X [--level 1] |
| setup_ink.sh / ink.sh | slim MPS ink env; ink_9um inference both directions + _view PNGs | ./ink.sh X |
| depthscan.sh | slide the 17-layer window through the 28-layer render; scores vs team map | ./depthscan.sh X [starts] |
| bench172.py / bench_png.py | corr + AUC vs team w087 map (tif / png inputs) | python3 bench172.py pred.tif |
| control.sh / fetch172.sh | render a crop of w087 and run ink.sh (positive control) | ./control.sh CX CY |
| control1447.sh | grow/render/ink at the announced 1447 text site | ./control1447.sh |
| hecate_setup.sh / hecate_run.sh / hecate172.sh | Hecate 9.6um on MPS; 9.6um re-render; 172 benchmark | DIRS=rev HECATE_ARGS=... ./hecate_run.sh ... |
| lockin.py | rev - k*fwd test (dead) | python3 lockin.py |
| holonomy.py | mesh Gaussian curvature / loop holonomy + grid-stretch baseline | python3 holonomy.py patches/X --L 6 |
| tetratic.py | tetratic order |psi4| + regularised disclination charge on a render | python3 tetratic.py renders/X_mid.png |
| textness.py | line-rhythm test on an ink map: projection-profile ACF prominence at 3-8 mm vs block-shuffle null; rot90 asymmetry | python3 textness.py --w087 CX CY [--theta 6 --line-band 5 7.5]; --calib |
Outputs: patches/ (tifxyz), renders/ (zarr + PNGs; figures start with _), predictions/ (+scan/, hecate/), logs/.

## 2. Experiments, in order (14 Oct)
E1  VC3D Stable (fc25b4d) crashed on catalog double-click: uncaught throw in resolveLasagnaForVolume. Fixed in Latest. 
E2  Headless grow from the team's May-2025 patch vertices: seeds land on value 0 of the April-2026 m7 prediction
    -> tracer starts off-surface -> swirly, sheet-crossing patches. Lesson: seed on the *current* prediction.
E3  seeds.py on the prediction alone: first seed (x=1404) grew 1.35 cm2 in 534 s, render all zeros -> outside masked scroll.
    Measured: 39.5M surface voxels at level 3, only 13.2M (34%) where CT>20. Added the CT mask to seeds.py.
E4  Six in-scroll seeds (z 22000-24600): 63-375 s grow each; 2 clean (5452, 3532), 2 mixed, 2 rejects. Contact sheet: docs/figures/_contact_run3.png.
E5  qa.py on 5452: points 1-3 in air (mesh overgrew past the outer wrap) -> ~1/3 of a "clean" patch is not papyrus.
E6  ink_9um on MPS: 86-138 s/patch. 5452 and 3532: blobs, no strokes, both directions. (docs/figures/_ink_5452_compare.png, _ink_3532_compare.png)
E7  Positive control PHerc.172 w087 crop (5440,5120): rev corr 0.363 / AUC 0.727, fwd 0.053 / 0.566 (docs/figures/_ctrl_compare.png).
    Pipeline works; model weak. Second crop (1200,9200): rev 0.240, fwd 0.021.
E8  Discord 24 Sep: team found ~10 letters on 1447 at ~(4144,2742,12557) with a new 9um recipe (+fine-tune); 1447 withdrawn
    from First Letters, still Grand-Prize eligible. Our control there: patch 9/9 on-sheet, ink_9um sees nothing either side.
E9  Depth-window scan (crop 1, rev): S0 .341 S2 .398 S4 .391 S6 .363 S8 .370 S10 .286 S11 .248. Block bootstrap (16x16 cells,
    2000 resamples): S2-S6 +0.036 [-0.001,+0.073]; S10 -0.077 [-0.125,-0.032]; S11 -0.115 [-0.171,-0.059].
    Crop 2: S2 .266 S4 .251 S6 .240; S2-S6 +0.026 [-0.023,+0.073]; pooled +0.031 [+0.000,+0.062].
    Reading: small direction-replicated gain at S2 (adopted); robust cliff away from the inked face; wrong side dead at all depths.
E10 Hecate 9.6um (stride 64, crop 1): rev 0.240/0.706, fwd 0.102/0.602; tiling seams visible (docs/figures/_hecate_fwd_vs_team.png). Stride 32 (full overlap) rev: 0.211 / AUC 0.717 -- seams gone but output is sparse specks; does not beat ink_9um S2 (0.398/0.746). Verdict: ink_9um window S2 stays default (docs/figures/_model_compare_172.png).
E11 Lock-in rev - k*fwd (k fit cross-crop, 0.04-0.17): no change (<0.01). Two-sided veto hurts (0.398->0.312): fwd carries a weak
    ink copy. One-sidedness is global, not pixel-wise. DEAD.
E12 Mesh holonomy (angle deficit, 1 mm loops): ranks patches correctly (4144 cleanest, 3532 worst) but corr 0.6-0.84 with plain
    grid-stretch, and BLIND to the lower-left switch in 3532: a surface drifting smoothly across windings is still flat (K=0).
    Intrinsic curvature is not a sheet-switch test. Retired as a detector; kept as a finding.
E13 Tetratic order |psi4| = |<e^{4 i theta}>| per 128-px tile (structure tensor, sig 2, win 6): separates the 3532 switch
    (0.1-0.3) from clean weave (0.6-0.8) while structure-tensor coherence is flat (0.4-0.6): local anisotropy != order.
    Medians: 3532 .52, 5452 .46, team 1447 patch .39, 4144 text site .32, w087 crops .30/.30.
    Caveat: psi4 is a weave-legibility score; it also drops for real damage (4144) and differs across scans.
E14 Disclination charge: raw winding of 4theta = noise (70-85% tiles nonzero). Regularised (smooth z4 over 16 px, count only
    tiles with |psi4|>=0.25): 5452 3.9% nonzero, 3532 12.7%, 4144 32%, w087 19-23%. Usable.
E15 Is low psi4 an ink signature? corr(|psi4|, team ink) = +0.05 on both w087 crops, CI straddles 0. NO.
E16 Textness (line rhythm) of ink maps, textness.py. Statistic: rotate map, project along lines inside a disc, unbiased ACF,
    prominence c(L) - [c(L/2)+c(3L/2)]/2 maximised over orientation and L in 3-8 mm; null = block shuffle in 1 mm tiles.
    Calibration on the team w087 map: full map z +16.7 (lines at 0 deg, spacing 6.3 mm); central 48 mm z +13.2; 32 mm z +5.2;
    16 mm z +1.9. The test needs >= 32 mm of render; our 16 mm control crops are at the floor.
    Constrained test (theta 6 +- 9 deg, L in 5-7.5 mm, null 200): team crop1 z +6.1, crop2 z +4.8. ink_9um S2 rev: crop1 z +0.8,
    crop2 z +1.8 (p .055). S2 fwd (dead side): crop1 z +2.9 (p .01), crop2 z -2.1 -> z ~ 3 occurs on noise at 16 mm; one-crop
    hits mean nothing. Hecate rev/fwd/s32: z < 1.2. rot90 asymmetry (sector-averaged): team 0.13-0.31, ours 0.13-0.24, no separation.
    Reading: our maps do not carry the line rhythm the team map carries. Bar for a future model: z > 3 at the known orientation
    on >= 32 mm, replicated on both sides' difference (rev - fwd). Figures: docs/figures/_textness_*.png; docs/textness_scores.tsv.
    Lesson in the code: raw periodogram |P1-P2|/(P1+P2) -> 0.5 for noise (exponential bins); sector-average first. And never
    window before projecting: a Hann envelope gives ACF ~0.5 at every lag.

## 3. Open items
- Surface-mask fraction at level 2 and ct-min 10/40 (robustness of the 66% number).
- Depth-profile fit + per-tile surface re-localisation (idea 1).
- Textness on a >= 32 mm render once the GPU runs (inference on the full w087 segment, then rev - fwd rhythm at theta 0).
- Publish: GitHub repo (MIT), Discord show-and-tell, PRs to villa (MPS ink install notes; qa.py; tetratic QA).
- Write-up for the 31 Oct progress-prize form.
