"""Turn a rendered surface volume (zarr, layers x H x W) into inspection PNGs:
max-intensity composite, middle layer, and a 3x3 contact sheet of layers.
usage: python composite.py renders/<name>.zarr"""
import sys, pathlib, numpy as np, zarr, imageio.v3 as iio
p = pathlib.Path(sys.argv[1]); z = zarr.open(str(p), mode="r")
arr = z[:] if hasattr(z, "shape") else z["0"][:]
if arr.ndim == 4: arr = arr[0]
L = arr.shape[0]
if arr.max() == 0: print(f"WARNING {p.name}: render is all zeros (patch lies outside the masked scroll)"); sys.exit(0)
def norm(x):
    lo, hi = np.percentile(x, (1, 99.5)); return np.clip((x - lo) / max(hi - lo, 1e-6) * 255, 0, 255).astype(np.uint8)
out = p.with_suffix("")
iio.imwrite(f"{out}_max.png", norm(arr.max(0)))
iio.imwrite(f"{out}_mid.png", norm(arr[L // 2]))
pick = np.linspace(0, L - 1, 9).astype(int); tiles = [norm(arr[i]) for i in pick]
h, w = tiles[0].shape; sheet = np.zeros((3 * h, 3 * w), np.uint8)
for k, t in enumerate(tiles): sheet[(k // 3) * h:(k // 3 + 1) * h, (k % 3) * w:(k % 3 + 1) * w] = t
iio.imwrite(f"{out}_sheet.png", sheet)
print(f"{p.name}: {L} layers, {h}x{w} px  ->  _max / _mid / _sheet .png")
