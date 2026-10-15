# vesuvius

Working repository for my Vesuvius Challenge entry on PHerc1447: a headless, logged grow / render / QA / ink pipeline
that runs on a MacBook Air (Apple Silicon, no CUDA), with GPU inference and fine-tuning moved to the MIT ORCD
Engaging cluster. Target: the First Letters prize on 1447, or a progress-prize submission (deadline 31 Oct 2026)
documenting the end-to-end run and its failure modes.

Zinuo Shi, Wellesley College. Started 14 Oct 2026.

## Status (14 Oct 2026)
- Pipeline works end to end: seed -> `vc_grow_seg_from_seed` -> `vc_render_tifxyz` -> composites -> cross-section QA -> ink inference on MPS.
- Positive control on PHerc.172 w087 reproduces the team's ink map (corr 0.398 / AUC 0.746, ink_9um, S2 window). The released models see nothing on our 1447 patches, including the announced text site.
- Three QA findings: 66% of the m7 surface prediction lies outside the masked scroll; mesh holonomy does not detect sheet switches; tetratic order |psi4| does.
- Next: Hecate at full overlap on the cluster, then fine-tuning on 172 with held-out windings. See `docs/notebook.md`, section 3.

## Layout
    README.md            this file
    docs/
      pipeline.md        how to run the Mac pipeline (one-time setup, control, new seeds, ink)
      results.md         results tables: patches, ink runs, 172 control, depth-window scan
      notebook.md        lab notebook: environment, script table, experiments E1-E15, open items
      figures/           comparison figures referenced by results.md and notebook.md
    orcd/                MIT ORCD (Engaging) cluster: setup, sbatch scripts, README
    config.env           scroll, volume and surface-prediction URLs; generations; slice count
    params.json          tracer parameters for vc_grow_seg_from_seed
    seeds.txt            seeds grown so far (x y z, 8.64 um volume 20250521151220)
    *.sh *.py            pipeline scripts, flat at the root; each is documented in docs/notebook.md section 1
    patches/             grown meshes (tifxyz, ~90 KB each)
    logs/                every run's log with timings

Not in the repo (regenerate with the scripts): `renders/` (surface volumes, 1.3 GB), `predictions/` (ink maps),
`control172/` (`fetch172.sh`), model checkpoints and `hecate/` (`setup_ink.sh`, `hecate_setup.sh`), the `.inkenv`
virtualenv and the sparse `villa/` clone.

## Quick start (Mac)
    ./setup_ink.sh                      # once: uv venv, villa sparse clone, ink_9um checkpoint
    SEEDS=seeds.txt ./run.sh            # grow, render, composite, QA for each seed
    ./ink.sh seed_5452_4100_22772       # ink inference, both directions, MPS
    ./control.sh 5440 5120              # positive control on PHerc.172 w087
Full instructions: `docs/pipeline.md`. Cluster: `orcd/README.md`.

## Acknowledgements
Built on ScrollPrize's `villa` (vesuvius package, ink_9um checkpoint) and `hecate`, both MIT-licensed, and on the
open data at `s3://vesuvius-challenge-open-data`. The PHerc.172 w087 segment and ink map are the Vesuvius Challenge
team's published artefacts.

## Licence
MIT, see `LICENSE`.
