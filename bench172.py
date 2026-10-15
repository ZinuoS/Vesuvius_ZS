"""Score ink predictions for the PHerc.172 w087 control crop against the team's published map.
usage: python3 bench172.py pred1.tif [pred2.tif ...]   (crop origin read from the filename: ..._CX_CY...)"""
import sys, re, numpy as np, tifffile, imageio.v3 as iio
team = iio.imread("control172/team_ink_w087_ds8.jpg"); team = team[..., 0] if team.ndim == 3 else team
for f in sys.argv[1:]:
    cx, cy = map(int, re.search(r"w087_(\d+)_(\d+)", f).groups())
    p = tifffile.imread(f).astype(np.float32)
    h, w = p.shape
    t = team[cy // 8:(cy + h) // 8, cx // 8:(cx + w) // 8].astype(np.float32)   # team map at 1/8 scale
    q = p[:t.shape[0] * 8, :t.shape[1] * 8].reshape(t.shape[0], 8, t.shape[1], 8).mean((1, 3))
    r = np.corrcoef(q.ravel(), t.ravel())[0, 1]
    ink = t > np.percentile(t, 85)                     # top 15% of team map = "ink" for AUC
    s_pos, s_neg = q[ink], q[~ink]                     # Mann-Whitney AUC
    ranks = np.argsort(np.argsort(np.concatenate([s_pos, s_neg])))
    auc = (ranks[:len(s_pos)].sum() - len(s_pos) * (len(s_pos) - 1) / 2) / (len(s_pos) * len(s_neg))
    print(f"{f}\tcorr={r:+.3f}\tAUC={auc:.3f}")
