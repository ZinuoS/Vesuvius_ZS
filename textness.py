"""Textness of an ink map: does it have the rhythm of writing, or only the texture of papyrus?
Three scores, all computed after resampling the map to a common pitch (default 64 um/px):
  line   : periodicity of the projection profile at the line spacing (3-8 mm), maximised over orientation.
           Projection along the line direction, unbiased autocorrelation, peak height in the lag band.
  letter : same along the line (lag band 1-3 mm): letter / word rhythm. Weaker, reported for completeness.
  rot90  : asymmetry of the 2D power spectrum under a 90 degree turn, in the annulus 0.8-6 mm.
           Weave is four-fold (same thing psi4 measures) and scores ~0; lines of text break it.
Null: block-shuffle the map in 1 mm tiles N times (kills long-range order, keeps local texture) and report the
z-score and the fraction of shuffles that beat the observed line score.
usage: python3 textness.py MAP.tif --um 7.91 [--crop CX CY W] [--null 200] [--name NAME]
       python3 textness.py --w087 5440 5120          # standard panel on a control crop: team map, ink_9um S2 rev/fwd, Hecate
Writes predictions/textness/<name>.png (map, log-spectrum, angle scan, best profile) and appends a row to
predictions/textness/scores.tsv."""
import argparse, os, pathlib, sys, numpy as np, tifffile, imageio.v3 as iio
from scipy.ndimage import rotate, gaussian_filter
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt

# ---------------------------------------------------------------- loading and resampling
def load(path):
    p = tifffile.imread(path) if path.endswith((".tif", ".tiff")) else iio.imread(path)
    p = p[..., 0] if p.ndim == 3 else p
    return p.astype(np.float64)

def to_pitch(img, um, pitch):
    """block-average by an integer factor so the pixel pitch is close to `pitch` um; returns (img, actual pitch)"""
    f = max(1, int(round(pitch / um)))
    h, w = (img.shape[0] // f) * f, (img.shape[1] // f) * f
    return img[:h, :w].reshape(h // f, f, w // f, f).mean((1, 3)), um * f

def prep(img, pitch_mm, hp_mm=2.0):
    """z-score after removing slow illumination (Gaussian high-pass, sigma hp_mm). No window here: the
    projection profiles must not inherit an envelope; the FFT applies its own Hann window."""
    x = img - gaussian_filter(img, hp_mm / pitch_mm)
    return (x - x.mean()) / (x.std() + 1e-9)

def hann2(x):
    return x * np.outer(np.hanning(x.shape[0]), np.hanning(x.shape[1]))

# ---------------------------------------------------------------- scores
def disc_mask(shape):
    yy, xx = np.indices(shape); cy, cx = (shape[0] - 1) / 2, (shape[1] - 1) / 2
    return ((yy - cy) ** 2 + (xx - cx) ** 2) <= (min(shape) / 2) ** 2

def acf(profile):
    """unbiased, normalised autocorrelation of a 1-D profile"""
    p = profile - profile.mean(); n = len(p); v = (p * p).sum() + 1e-12
    c = np.correlate(p, p, "full")[n - 1:] / v
    return c * n / (n - np.arange(n))          # unbiased: divide by the number of overlapping samples

def profile_peak(img, theta, pitch_mm, band_mm, mask):
    """rotate by theta so candidate lines are horizontal, project along rows inside the disc, autocorrelate,
    return the max ACF value in the lag band and the lag (mm) where it occurs"""
    r = rotate(img, theta, reshape=False, order=1, mode="constant", cval=0.0)
    prof = (r * mask).sum(1) / np.maximum(mask.sum(1), 1)
    prof = prof[mask.any(1)]
    c = acf(prof); lags = np.arange(len(c)) * pitch_mm
    sel = (lags >= band_mm[0]) & (lags <= band_mm[1])
    # prominence of a period-L peak: c(L) minus the mean of c at the half-period troughs L/2 and 3L/2.
    # a slow envelope lifts all three together and cancels; a genuine period L lifts c(L) and sinks the troughs.
    def at(l): return np.interp(l, lags, c, right=np.nan)
    prom = np.array([c[i] - 0.5 * (at(lags[i] / 2) + at(1.5 * lags[i])) if sel[i] else -np.inf for i in range(len(c))])
    prom = np.where(np.isnan(prom), -np.inf, prom); k = int(np.argmax(prom))
    return prom[k], lags[k], prof, c, lags

def scan_angles(img, pitch_mm, band_mm, step=3, theta0=None, halfwidth=9):
    """theta0=None: full 0-180 scan (unknown line direction). theta0 given: only theta0 +- halfwidth, which is
    the constrained test to use when the line direction is known from a reference map (far fewer looks)"""
    mask = disc_mask(img.shape)
    thetas = np.arange(0, 180, step) if theta0 is None else np.arange(theta0 - halfwidth, theta0 + halfwidth + 1, step)
    vals = np.array([profile_peak(img, t, pitch_mm, band_mm, mask)[0] for t in thetas])
    return thetas, vals

def rot90_asymmetry(img, pitch_mm, lam_mm=(0.8, 6.0), nsec=30):
    """angular power distribution A(phi) in the annulus lam_mm (nsec sectors over 180 deg, since P(k) = P(-k));
    asymmetry = sum|A(phi) - A(phi + 90)| / sum A. Sector averaging is essential: raw periodogram bins are
    exponentially distributed and |P1 - P2| / (P1 + P2) tends to 0.5 for pure noise."""
    n = min(img.shape); x = hann2(img[:n, :n])
    P = np.abs(np.fft.fftshift(np.fft.fft2(x))) ** 2
    k = np.fft.fftshift(np.fft.fftfreq(n, d=pitch_mm)); K = np.sqrt(k[:, None] ** 2 + k[None, :] ** 2)
    ann = (K >= 1 / lam_mm[1]) & (K <= 1 / lam_mm[0])
    phi = np.degrees(np.arctan2(k[:, None], k[None, :])) % 180
    sec = np.minimum((phi / (180 / nsec)).astype(int), nsec - 1)
    A = np.array([P[ann & (sec == s)].mean() for s in range(nsec)])
    q = nsec // 2                                                   # 90 degrees = nsec/2 sectors
    return float(np.abs(A - np.roll(A, q)).sum() / (2 * A.sum() + 1e-12)), np.log10(P + 1e-9), ann, A

def block_shuffle(img, tile, rng):
    h, w = (img.shape[0] // tile) * tile, (img.shape[1] // tile) * tile
    b = img[:h, :w].reshape(h // tile, tile, w // tile, tile).transpose(0, 2, 1, 3).reshape(-1, tile, tile)
    b = b[rng.permutation(len(b))]
    return b.reshape(h // tile, w // tile, tile, tile).transpose(0, 2, 1, 3).reshape(h, w)

def textness(raw, um, pitch=64.0, line_band=(3.0, 8.0), letter_band=(1.0, 3.0), n_null=100, seed=0, step=3, theta0=None):
    """returns a dict of scores (line, theta, lag_line, letter, lag_letter, rot90, z, p) plus the arrays for the figure"""
    img, pitch_um = to_pitch(raw, um, pitch); pitch_mm = pitch_um / 1000
    x = prep(img, pitch_mm)
    thetas, vals = scan_angles(x, pitch_mm, line_band, step, theta0)
    i = int(np.argmax(vals)); theta_line = float(thetas[i]); line = float(vals[i])
    mask = disc_mask(x.shape)
    _, lag_line, prof, c, lags = profile_peak(x, theta_line, pitch_mm, line_band, mask)
    letter, lag_letter, *_ = profile_peak(x, theta_line + 90, pitch_mm, letter_band, mask)
    rot, logP, ann, A = rot90_asymmetry(x, pitch_mm)
    # null: block shuffle in ~1 mm tiles, re-score the line statistic at the SAME orientation scan
    rng = np.random.default_rng(seed); tile = max(2, int(round(1.0 / pitch_mm))); null = []
    for _ in range(n_null):
        xs = prep(block_shuffle(img, tile, rng), pitch_mm)
        null.append(scan_angles(xs, pitch_mm, line_band, step=step * (1 if theta0 is not None else 3), theta0=theta0)[1].max())
    null = np.array(null); z = (line - null.mean()) / (null.std() + 1e-9); pval = float((null >= line).mean())
    return dict(line=line, theta=theta_line, lag_line=float(lag_line), letter=float(letter), lag_letter=float(lag_letter),
                rot90=rot, z=float(z), p=pval, null_mean=float(null.mean()), null_sd=float(null.std()),
                band=line_band, pitch_mm=pitch_mm, img=img, x=x, thetas=thetas, vals=vals, prof=prof, acf=c, lags=lags, logP=logP, ann=ann, A=A)

# ---------------------------------------------------------------- report
def figure(res, name, out):
    fig, ax = plt.subplots(1, 4, figsize=(18, 4.4))
    ax[0].imshow(res["img"], cmap="gray"); ax[0].set_title(f"{name}  ({res['pitch_mm']*1000:.0f} um/px)"); ax[0].axis("off")
    n = res["logP"].shape[0]; ax[1].imshow(res["logP"], cmap="magma"); ax[1].contour(res["ann"], levels=[0.5], colors="c", linewidths=0.6)
    ax[1].set_title(f"log power; rot90 asym {res['rot90']:.3f}"); ax[1].axis("off")
    ax[2].plot(res["thetas"], res["vals"]); ax[2].axvline(res["theta"], color="r", lw=0.8)
    ax[2].axhline(res["null_mean"], color="gray", ls="--", lw=0.8); ax[2].axhline(res["null_mean"] + 2 * res["null_sd"], color="gray", ls=":", lw=0.8)
    ax[2].set_xlabel("orientation (deg)"); ax[2].set_ylabel(f"ACF prominence, {res['band'][0]:g}-{res['band'][1]:g} mm"); ax[2].set_title(f"line {res['line']:.3f}  z {res['z']:+.1f}  p {res['p']:.2f}")
    ax[3].plot(res["lags"], res["acf"]); ax[3].set_xlim(0, 13); ax[3].axvspan(res["band"][0], res["band"][1], color="y", alpha=0.2)
    ax[3].axvline(res["lag_line"], color="r", lw=0.8); ax[3].set_xlabel("lag (mm)"); ax[3].set_title(f"profile ACF at {res['theta']:.0f} deg; peak lag {res['lag_line']:.1f} mm")
    fig.tight_layout(); fig.savefig(out, dpi=90); plt.close(fig)

def run_one(path, um, name, crop=None, n_null=100, outdir="predictions/textness", line_band=(3.0, 8.0), theta0=None):
    raw = load(path)
    if crop is not None:
        cx, cy, w = crop; raw = raw[cy:cy + w, cx:cx + w]
    res = textness(raw, um, n_null=n_null, line_band=line_band, theta0=theta0)
    pathlib.Path(outdir).mkdir(parents=True, exist_ok=True)
    figure(res, name, f"{outdir}/{name}.png")
    row = f"{name}\t{res['line']:.3f}\t{res['theta']:.0f}\t{res['lag_line']:.2f}\t{res['letter']:.3f}\t{res['lag_letter']:.2f}\t{res['rot90']:.3f}\t{res['z']:+.2f}\t{res['p']:.3f}"
    print(row)
    with open(f"{outdir}/scores.tsv", "a") as fh: fh.write(row + "\n")
    return res

HEADER = "name\tline\ttheta\tlag_mm\tletter\tlag_mm\trot90\tz\tp"

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("map", nargs="?"); ap.add_argument("--um", type=float, help="pixel pitch of MAP in um")
    ap.add_argument("--crop", nargs=3, type=int, metavar=("CX", "CY", "W"), help="crop in MAP pixels")
    ap.add_argument("--null", type=int, default=100); ap.add_argument("--name")
    ap.add_argument("--w087", nargs=2, type=int, metavar=("CX", "CY"), help="standard panel on a w087 control crop (render px)")
    ap.add_argument("--root", default=".", help="repo root (where control172/ and predictions/ live)")
    ap.add_argument("--calib", action="store_true", help="power vs field of view: team w087 map at full size and central 48/32/16 mm windows")
    ap.add_argument("--theta", type=float, help="known line orientation (deg); restricts the scan to +-9 deg (constrained test)")
    ap.add_argument("--line-band", nargs=2, type=float, default=(3.0, 8.0), metavar=("MIN_MM", "MAX_MM"))
    a = ap.parse_args(); os.chdir(a.root)
    print(HEADER)
    if a.calib:
        t = load("control172/team_ink_w087_ds8.jpg"); um = 63.28
        for fov in [None, 48, 32, 16]:
            if fov is None: crop = None; name = "team_w087_full"
            else:
                w = int(fov * 1000 / um); cy, cx = (t.shape[0] - w) // 2, (t.shape[1] - w) // 2; crop = (cx, cy, w); name = f"team_w087_{fov}mm"
            run_one("control172/team_ink_w087_ds8.jpg", um, name, crop, a.null, line_band=tuple(a.line_band), theta0=a.theta)
    elif a.w087:
        cx, cy = a.w087; W = 2048; tag = f"ctrl172_w087_{cx}_{cy}"
        panel = [("team", "control172/team_ink_w087_ds8.jpg", 63.28, (cx // 8, cy // 8, W // 8)),
                 ("ink9um_S2_rev", f"predictions/scan/{tag}_S2_reverse.tif", 7.91, None),
                 ("ink9um_S2_fwd", f"predictions/scan/{tag}_S2.tif", 7.91, None),
                 ("ink9um_S6_rev", f"predictions/scan/{tag}_S6_reverse.tif", 7.91, None),
                 ("hecate_rev", f"predictions/hecate/{tag}_rev.png", 9.6, None),
                 ("hecate_fwd", f"predictions/hecate/{tag}_fwd.png", 9.6, None),
                 ("hecate_s32_rev", f"predictions/hecate/{tag}_s32_rev.png", 9.6, None)]
        for name, path, um, crop in panel:
            if os.path.exists(path): run_one(path, um, f"{tag}_{name}", crop, a.null, line_band=tuple(a.line_band), theta0=a.theta)
            else: print(f"{tag}_{name}\t(missing: {path})", file=sys.stderr)
    else:
        if not (a.map and a.um): sys.exit("give MAP and --um, or --w087 CX CY")
        run_one(a.map, a.um, a.name or pathlib.Path(a.map).stem, tuple(a.crop) if a.crop else None, a.null, line_band=tuple(a.line_band), theta0=a.theta)
