"""Seeds on the m7 surface prediction near a target point, inside the scroll, at full resolution.
usage: python3 near.py X Y Z [--r 160] [--n 3] [--min-sep 120] [--out seeds_near.txt]"""
import argparse, os, sys, numpy as np, zarr, fsspec
ap = argparse.ArgumentParser(); ap.add_argument("x", type=int); ap.add_argument("y", type=int); ap.add_argument("z", type=int)
ap.add_argument("--r", type=int, default=160); ap.add_argument("--n", type=int, default=3)
ap.add_argument("--min-sep", type=int, default=120); ap.add_argument("--ct-min", type=int, default=20)
ap.add_argument("--out", default="seeds_near.txt"); a = ap.parse_args()
r = a.r; lo = [a.z - r, a.y - r, a.x - r]
sl = tuple(slice(max(l, 0), l + 2 * r) for l in lo)
surf = zarr.open(fsspec.get_mapper(os.environ["SURF_URL"]), mode="r")["0"][sl]
ct = zarr.open(fsspec.get_mapper(os.environ["CT_URL"]), mode="r")["0"][sl]
idx = np.argwhere((surf > 0) & (ct > a.ct_min))
print(f"window {2*r}^3 around ({a.x},{a.y},{a.z}): {len(idx)} on-surface in-scroll voxels", file=sys.stderr)
if not len(idx): sys.exit("none found; increase --r")
off = np.array([s.start for s in sl]); pts = idx + off              # (z, y, x) level 0
d = np.linalg.norm(pts - [a.z, a.y, a.x], axis=1); order = np.argsort(d)
chosen = []
for k in order:
    p = pts[k]
    if all(np.linalg.norm(p - q) >= a.min_sep for q in chosen): chosen.append(p)
    if len(chosen) == a.n: break
with open(a.out, "w") as fh:
    for z, y, x in chosen: fh.write(f"{x} {y} {z}\n"); print(f"seed {x} {y} {z}  dist {np.linalg.norm([z-a.z,y-a.y,x-a.x]):.0f} vx", file=sys.stderr)
