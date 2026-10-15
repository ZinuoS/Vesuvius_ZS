"""Score any prediction image against the team's w087 map. Resamples the prediction onto the team's 1/8 grid.
usage: python3 bench_png.py PRED CX CY W     (crop origin and width in 7.91 um render pixels)"""
import sys, numpy as np, imageio.v3 as iio
from PIL import Image
f, cx, cy, w = sys.argv[1], *map(int, sys.argv[2:5])
team = iio.imread("control172/team_ink_w087_ds8.jpg"); team = team[..., 0] if team.ndim == 3 else team
t = team[cy // 8:(cy + w) // 8, cx // 8:(cx + w) // 8].astype(np.float32)
p = iio.imread(f); p = p[..., 0] if p.ndim == 3 else p
q = np.asarray(Image.fromarray(p.astype(np.float32)).resize((t.shape[1], t.shape[0]), Image.BOX))
r = np.corrcoef(q.ravel(), t.ravel())[0, 1]
ink = t > np.percentile(t, 85); s = np.concatenate([q[ink], q[~ink]]); rk = np.argsort(np.argsort(s))
n1 = ink.sum(); auc = (rk[:n1].sum() - n1 * (n1 - 1) / 2) / (n1 * (~ink).sum())
print(f"{f}\tcorr={r:+.3f}\tAUC={auc:.3f}")
