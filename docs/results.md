# Results log (14 Oct 2026)

## 1. Automated pipeline, PHerc1447 (8.64 um volume 20250521151220)
seed -> vc_grow_seg_from_seed (35 gen) -> vc_render_tifxyz (28 layers) -> composite PNGs -> qa.py cross-sections
| seed (x y z)        | grow  | verdict                          |
|---------------------|-------|----------------------------------|
| 5452 4100 22772     | 107 s | clean weave; top third in air (qa.py) |
| 3532 4492 23020     | 375 s | clean; sheet switch lower-left   |
| 2388 3356 22308     | 212 s | mixed                            |
| 3092 6212 22708     |  76 s | mixed                            |
| 7036 4612 24060     | 167 s | reject (compressed mass)         |
| 4020 1948 24284     |  63 s | reject (edge, 11% fill)          |
| 4144 2742 12557     | 145 s | text site from team announcement; 9/9 QA points on-sheet |
Failure modes found: stale seeds off current prediction; surface prediction outside scroll mask; overgrowth into air.
Finding: 66% of m7 surface-prediction voxels lie where masked CT <= 20 (level 3; not yet checked at level 2).

## 2. Ink inference on Apple Silicon (MPS), no C++ build
ink_9um checkpoint (hybrid_3d2d-seed42/step-075000), 86-138 s per patch, both directions.
PHerc1447 patches 5452, 3532, and the text site 4144/2742/12557: no strokes, no rows, either direction.

## 3. Positive control: PHerc.172 w087 vs team ink map (bench172.py / bench_png.py)
| model / setting            | crop 5440,5120 (rev / fwd)     | crop 1200,9200 (rev / fwd) |
|----------------------------|--------------------------------|----------------------------|
| ink_9um default (S6)       | 0.363 / 0.053  (AUC .727/.566) | 0.240 / 0.021              |
| ink_9um S2 window          | 0.398 / 0.102  (AUC .746)      | 0.266 / -0.007             |
| Hecate 9.6um, stride 64    | 0.240 / 0.102  (AUC .706/.602) | not run                    |
| Hecate 9.6um, stride 32    | 0.211 rev (AUC .717)           | not run                    |
(corr = Pearson vs team map at 1/8 scale; reverse = inked side)

## 4. Depth-window scan (crop 5440,5120, reverse), block bootstrap vs S6
S2 +0.036 [-0.001,+0.073]; S4 +0.028; S8 +0.007; S0 -0.021; S10 -0.077 [-0.125,-0.032]; S11 -0.115 [-0.171,-0.059]
Crop 2 S2-S6 +0.026 [-0.023,+0.073]; pooled +0.031 [+0.000,+0.062].
Reading: small direction-replicated gain at S2; robust cliff when window moves away from inked face; wrong side dead at all depths.

## Where things are
patches/      grown meshes (tifxyz)           renders/   surface volumes + _mid/_max/_sheet/_qa PNGs (not in git); comparison figures in docs/figures/
predictions/  ink_9um maps (+ scan/, hecate/) logs/      every run's log with timings
control172/   w087 mesh + team ink map        scripts:   run.sh seeds.py near.py qa.py ink.sh depthscan.sh bench172.py hecate_run.sh
