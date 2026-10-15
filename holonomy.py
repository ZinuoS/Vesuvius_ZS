"""Holonomy / developability QA for a tifxyz mesh.
Per-vertex discrete Gaussian curvature (angle deficit over the 4-neighbour umbrella), integrated over loops of
L x L cells -> holonomy angle per loop (Gauss-Bonnet). Also grid-stretch (parametrisation distortion) as the
'existing check' baseline. Prints stats; writes renders/<name>_holo.png (3 panels: mid render, |holonomy|, stretch).
usage: python3 holonomy.py patches/<name> [--L 6] [--ref renders/<name>_mid.png] [--thresh DEG]"""
import argparse, json, pathlib, numpy as np, tifffile, imageio.v3 as iio
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
ap=argparse.ArgumentParser(); ap.add_argument("patch"); ap.add_argument("--L",type=int,default=6)
ap.add_argument("--thresh",type=float,default=None,help="holonomy threshold in degrees (default: report percentiles)")
a=ap.parse_args(); P=pathlib.Path(a.patch); name=P.name
X,Y,Z=[tifffile.imread(P/f"{c}.tif").astype(np.float64) for c in "xyz"]
V=np.stack([X,Y,Z],-1); ok=(X>0)&(Y>0)&(Z>0)
meta=json.load(open(P/"meta.json")); step=1/meta["scale"][0]
H,W=X.shape
# --- angle deficit at interior vertices with all 4 neighbours valid
def ang(u,v):
    c=(u*v).sum(-1)/np.sqrt((u*u).sum(-1)*(v*v).sum(-1)+1e-12); return np.arccos(np.clip(c,-1,1))
c=V[1:-1,1:-1]; nb=[V[:-2,1:-1],V[1:-1,2:],V[2:,1:-1],V[1:-1,:-2]]   # up,right,down,left
okc=ok[1:-1,1:-1]&ok[:-2,1:-1]&ok[1:-1,2:]&ok[2:,1:-1]&ok[1:-1,:-2]
deficit=2*np.pi-sum(ang(nb[i]-c,nb[(i+1)%4]-c) for i in range(4))
deficit=np.where(okc,deficit,np.nan)
# --- loop holonomy: sum of deficits over LxL cells (Gauss-Bonnet), in degrees
L=a.L; hh,ww=(H-2)//L,(W-2)//L
blk=lambda A:A[:hh*L,:ww*L].reshape(hh,L,ww,L)
valid=np.isfinite(blk(deficit)).all((1,3))
holo=np.degrees(np.nansum(blk(deficit),(1,3))); holo[~valid]=np.nan
# --- grid stretch baseline: edge lengths vs nominal step, per cell, as max |log ratio|
ex=np.linalg.norm(V[:,1:]-V[:,:-1],axis=-1)/step; ey=np.linalg.norm(V[1:]-V[:-1],axis=-1)/step
okx=ok[:,1:]&ok[:,:-1]; oky=ok[1:]&ok[:-1]
sx=np.where(okx,np.abs(np.log(ex+1e-9)),np.nan)[1:-1,1:-1]; sy=np.where(oky,np.abs(np.log(ey+1e-9)),np.nan)[1:-1,1:-1]
stretch=np.nanmax(np.stack([blk(sx[:hh*L,:ww*L]).max((1,3)) if False else np.nanmax(blk(sx),(1,3)), np.nanmax(blk(sy),(1,3))]),0)
stretch[~valid]=np.nan
mm=L*step*float(meta.get("voxelsize",8.64) if "voxelsize" in meta else 8.64)/1000
v=np.isfinite(holo); h=np.abs(holo[v]); s=stretch[v]
print(f"{name}: grid {H}x{W}, loops {L}x{L} cells (~{mm:.2f} mm), {v.sum()} valid loops")
print(f"  |holonomy| deg: median {np.median(h):.2f}  p90 {np.percentile(h,90):.2f}  p99 {np.percentile(h,99):.2f}  max {h.max():.1f}")
print(f"  stretch |log r|: median {np.median(s):.3f}  p90 {np.percentile(s,90):.3f}  p99 {np.percentile(s,99):.3f}")
print(f"  corr(|holonomy|, stretch) over loops: {np.corrcoef(h,s)[0,1]:.3f}")
if a.thresh is not None:
    flag=np.abs(holo)>a.thresh; print(f"  loops above {a.thresh} deg: {100*np.nanmean(flag[v]):.1f}%")
np.save(f"renders/{name}_holo.npy",holo); np.save(f"renders/{name}_stretch.npy",stretch)
fig,ax=plt.subplots(1,3,figsize=(15,5.2))
mid=pathlib.Path(f"renders/{name}_mid.png")
if mid.exists(): ax[0].imshow(iio.imread(mid),cmap="gray"); ax[0].set_title("flattened mid layer")
im=ax[1].imshow(np.abs(holo),cmap="magma",vmin=0,vmax=np.nanpercentile(np.abs(holo),99)); ax[1].set_title(f"|holonomy| per {mm:.1f} mm loop (deg)"); plt.colorbar(im,ax=ax[1],fraction=.046)
im=ax[2].imshow(stretch,cmap="viridis",vmin=0,vmax=np.nanpercentile(stretch,99)); ax[2].set_title("grid stretch |log r| (baseline)"); plt.colorbar(im,ax=ax[2],fraction=.046)
for x in ax: x.axis("off")
fig.suptitle(name); fig.tight_layout(); fig.savefig(f"renders/{name}_holo.png",dpi=90); print(f"  wrote renders/{name}_holo.png")
