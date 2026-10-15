# Running on MIT ORCD (Engaging)

## Division of labour
Mac: VC3D GUI, seeding, growing, rendering (streams S3, 6 s per cached crop), QA, figures.   Cluster: ink inference and fine-tuning.
Move renders with rsync (a 28-layer 1440^2 render is ~30 MB):
    rsync -av ~/Desktop/Projects/vesuvius/renders/<name>.zarr  <user>@orcd-login001.mit.edu:~/vesuvius/renders/
and predictions back:
    rsync -av <user>@orcd-login001.mit.edu:~/vesuvius/predictions/  ~/Desktop/Projects/vesuvius/predictions/orcd/

## First session (15 min, interactive)
1. OnDemand -> Interactive -> Shell or Jupyter; partition mit_normal_gpu; extra Slurm options: --gres=gpu:1; 2 hours.
2. In the session:  nvidia-smi            (must list a GPU)
3. Copy this orcd/ folder to the cluster, then:  bash orcd/setup_env.sh
   Last lines must read  torch ... | cuda: True | <GPU name>.  If cuda: False, you are not on a GPU node.
4. Smoke test on one render (copy renders/seed_4144_2742_12557.zarr first):
       sbatch orcd/ink_infer.sbatch renders/seed_4144_2742_12557.zarr 2
   Expect 10-30 s of inference (vs 90-140 s on the Air). Output: predictions/seed_4144_2742_12557_S2.tif + _reverse.tif.

## Checks before queuing
    sinfo -O "Partition,Nodes:10,CPUsState,Gres:30,GresUsed:30,StateCompact" -e -p mit_normal_gpu
    squeue -u $USER
If the queue is long: edit the sbatch to  -p mit_preemptable  (job can be killed; inference is short so that is fine).

## Disk
Home quotas are usually small. Check  df -h $HOME  and, if there is a scratch/pool path for your account, set
    export VESUVIUS_HOME=/path/to/scratch/vesuvius
before setup_env.sh and in each sbatch (or edit the default at the top of the scripts).

## Next on the cluster (after the smoke test)
- Hecate at full overlap on the 172 control crops (hecate_infer.sbatch) -> fair model comparison.
- Fine-tuning: villa/ink-detection training (the September "lighter ink training tutorial" downloads ~2.4 GB instead of 92 GB).
  Plan: distil onto 172 with dense teacher labels, hold out whole windings, score with bench172.py, then pseudo-label on 1447
  starting from the announced text site.
