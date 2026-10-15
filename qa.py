"""Cross-section QA sheet for a grown patch, no GUI.
For a 3x3 grid of points across the patch: XY and YZ CT slices (level 0) around the point,
with the mesh's intersection with that slice overlaid in orange. Plus the flattened mid layer
with the points numbered. One PNG per patch: renders/<name>_qa.png
usage: python3 qa.py patches/<name> [--half 192] [--grid 3]"""
import argparse, json, os, pathlib, sys
import numpy as np, tifffile, zarr, fsspec, imageio.v3 as iio
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt

ap = argparse.ArgumentParser()
ap.add_argument("patch"); ap.add_argument("--half", type=int, default=192, help="half-width of slice crop, voxels")
ap.add_argument("--grid", type=int, default=3)
ap.add_argument("--level", type=int, default=1, help="CT pyramid level for slices (0 = full res, 1 = half, ~4x fewer chunks)")
a = ap.parse_args()
import time; T0 = time.time()
def log(m): print(f"[{time.time()-T0:5.1f}s] {m}", file=sys.stderr, flush=True)
P = pathlib.Path(a.patch); name = P.name
X, Y, Z = [tifffile.imread(P / f"{c}.tif").astype(np.float32) for c in "xyz"]
valid = (X > 0) & (Y > 0) & (Z > 0)
meta = json.load(open(P / "meta.json")); step = round(1 / meta["scale"][0])   # voxels per grid cell
log(f"{name}: opening CT level {a.level}")
ct = zarr.open(fsspec.get_mapper(os.environ["CT_URL"]), mode="r")[str(a.level)]
f = 2 ** a.level   # level-0 -> level-a coordinate factor

# sample points: grid quantiles over valid vertices, snapped to nearest valid vertex
rr, cc = np.nonzero(valid)
pts = []
for i in range(a.grid):
    for j in range(a.grid):
        tr = np.quantile(rr, (i + .5) / a.grid); tc = np.quantile(cc, (j + .5) / a.grid)
        k = np.argmin((rr - tr) ** 2 + (cc - tc) ** 2); pts.append((rr[k], cc[k]))

def mesh_cut(axis, value, tol):
    """mesh vertices within tol voxels of the slice plane"""
    coord = {"z": Z, "x": X}[axis]
    m = valid & (np.abs(coord - value) < tol)
    return X[m], Y[m], Z[m]

h = a.half; n = len(pts)
fig = plt.figure(figsize=(4 * 3, 4 * (n + 1) / 1.5), dpi=90)
gs = fig.add_gridspec(n + 1, 2)
# flattened overview with numbered points
mid = pathlib.Path(f"renders/{name}_mid.png")
ax = fig.add_subplot(gs[0, :])
if mid.exists():
    ax.imshow(iio.imread(mid), cmap="gray")
    for idx, (r, c) in enumerate(pts):
        ax.plot(c * step, r * step, "o", ms=14, mfc="none", mec="orange", mew=2)
        ax.text(c * step + 25, r * step, str(idx + 1), color="orange", fontsize=14, weight="bold")
ax.set_title(f"{name}: flattened mid layer, sample points"); ax.axis("off")

for idx, (r, c) in enumerate(pts):
    log(f"point {idx+1}/{n}: fetching XY + YZ slices")
    x0, y0, z0 = int(X[r, c] / f), int(Y[r, c] / f), int(Z[r, c] / f)
    # XY slice at z0
    sl = ct[z0, max(y0 - h, 0):y0 + h, max(x0 - h, 0):x0 + h]
    mx, my, _ = mesh_cut("z", z0 * f, step / 2); mx, my = mx / f, my / f
    ax = fig.add_subplot(gs[idx + 1, 0]); ax.imshow(sl, cmap="gray")
    ax.plot(mx - max(x0 - h, 0), my - max(y0 - h, 0), ".", color="orange", ms=3)
    ax.plot(h, h, "+", color="cyan", ms=12); ax.set_xlim(0, sl.shape[1]); ax.set_ylim(sl.shape[0], 0)
    ax.set_title(f"{idx+1}  XY @ z={z0*f}  (L{a.level})"); ax.axis("off")
    # YZ slice at x0  (rows z, cols y)
    sl = ct[max(z0 - h, 0):z0 + h, max(y0 - h, 0):y0 + h, x0]
    _, my, mz = mesh_cut("x", x0 * f, step / 2); my, mz = my / f, mz / f
    ax = fig.add_subplot(gs[idx + 1, 1]); ax.imshow(sl, cmap="gray")
    ax.plot(my - max(y0 - h, 0), mz - max(z0 - h, 0), ".", color="orange", ms=3)
    ax.plot(h, h, "+", color="cyan", ms=12); ax.set_xlim(0, sl.shape[1]); ax.set_ylim(sl.shape[0], 0)
    ax.set_title(f"{idx+1}  YZ @ x={x0*f}  (L{a.level})"); ax.axis("off")
    log(f"point {idx+1} done (L0 x={x0*f} y={y0*f} z={z0*f})")

out = f"renders/{name}_qa.png"; fig.tight_layout(); fig.savefig(out); print(f"wrote {out}")
