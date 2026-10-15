"""Pick seed points on the m7 recto-surface prediction, spaced apart, in level-0 voxel coords.
usage: python seeds.py --z 22000 24600 --n 12 [--level 3] [--min-sep 600]
Reads only the downsampled pyramid level over HTTPS; nothing is downloaded in full."""
import argparse, os, sys, numpy as np, zarr, fsspec
ap = argparse.ArgumentParser()
ap.add_argument("--z", nargs=2, type=int, required=True, help="z range at level 0")
ap.add_argument("--n", type=int, default=12)
ap.add_argument("--level", type=int, default=3, help="pyramid level to read (3 = 1/8 res)")
ap.add_argument("--min-sep", type=int, default=600, help="min seed separation, level-0 voxels")
ap.add_argument("--out", default="seeds.txt")
ap.add_argument("--ct-min", type=int, default=20, help="min CT value (uint8) under a seed")
ap.add_argument("--append", action="store_true", help="append to --out instead of overwriting")
a = ap.parse_args()
url = os.environ["SURF_URL"]
g = zarr.open(fsspec.get_mapper(url), mode="r")[str(a.level)]  # works on zarr 2.x and 3.x
f = 2 ** a.level
z0, z1 = a.z[0] // f, a.z[1] // f
print(f"reading {url}/{a.level} z[{z0}:{z1}] shape {g.shape}", file=sys.stderr)
vol = g[z0:z1]
# reject surface-prediction hits where the masked CT is empty (outside the scroll) or dim
ct = zarr.open(fsspec.get_mapper(os.environ["CT_URL"]), mode="r")[str(a.level)][z0:z1]
ct = ct[:, :vol.shape[1], :vol.shape[2]]
inside = ct > a.ct_min
print(f"surface voxels {int((vol>0).sum())}, of which inside scroll (CT>{a.ct_min}) {int(((vol>0)&inside).sum())}", file=sys.stderr)
idx = np.argwhere((vol > 0) & inside)
if len(idx) == 0: sys.exit("no surface voxels in that z range")
rng = np.random.default_rng(0); rng.shuffle(idx)
chosen = []
sep = a.min_sep / f
for p in idx:
    if all(np.linalg.norm(p - q) >= sep for q in chosen):
        chosen.append(p)
    if len(chosen) == a.n: break
with open(a.out, "a" if a.append else "w") as fh:
    for p in chosen:  # p = (z, y, x) at the pyramid level; convert to level-0 voxel coords
        z, y, x = (p + 0.5) * f
        fh.write(f"{x:.0f} {y:.0f} {z + z0 * f:.0f}\n")
print(f"wrote {len(chosen)} seeds to {a.out} (x y z, level 0)", file=sys.stderr)
