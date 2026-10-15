"""Tetratic order and disclination charge of the papyrus weave on a flattened render.
theta from the structure tensor (line field); psi4 = <e^{4 i theta}> per tile (4-fold: both fibre families map to
one phase); q = (1/2pi) oint d(4 theta) around each tile boundary = enclosed disclination charge (units of 1/4).
usage: python3 tetratic.py renders/<name>_mid.png [--tile 128] [--sig 2] [--win 6]"""
import argparse, numpy as np, imageio.v3 as iio
from scipy.ndimage import gaussian_filter
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
ap=argparse.ArgumentParser(); ap.add_argument("img"); ap.add_argument("--tile",type=int,default=128)
ap.add_argument("--sig",type=float,default=2.0); ap.add_argument("--win",type=float,default=6.0)
ap.add_argument("--smooth",type=float,default=16.0,help="window (px) for smoothing z4 before counting winding")
ap.add_argument("--floor",type=float,default=0.25,help="min |psi4| of a tile to count its charge"); a=ap.parse_args()
I=iio.imread(a.img).astype(float); I=I[...,0] if I.ndim==3 else I
valid=I>0; name=a.img.split("/")[-1].replace("_mid.png","")
gx=gaussian_filter(I,a.sig,order=(0,1)); gy=gaussian_filter(I,a.sig,order=(1,0))
Jxx=gaussian_filter(gx*gx,a.win); Jyy=gaussian_filter(gy*gy,a.win); Jxy=gaussian_filter(gx*gy,a.win)
theta=0.5*np.arctan2(2*Jxy,Jxx-Jyy)
coh=(np.sqrt((Jxx-Jyy)**2+4*Jxy**2))/(Jxx+Jyy+1e-9)
z4=np.exp(4j*theta)
T=a.tile; H,W=I.shape; hh,ww=H//T,W//T
blk=lambda A:A[:hh*T,:ww*T].reshape(hh,T,ww,T)
occ=blk(valid).mean((1,3)); good=occ>0.95
psi4=np.abs(blk(z4).mean((1,3))); cohm=blk(coh).mean((1,3))
# regularised phase: smooth the complex order-parameter field, then take its argument.
# Where the local field is disordered |zs|->0 and the phase is meaningless; charge is only counted on ordered tiles.
zs=gaussian_filter(z4.real,a.smooth)+1j*gaussian_filter(z4.imag,a.smooth)
phi=np.angle(zs)
def wrap(d): return (d+np.pi)%(2*np.pi)-np.pi
q=np.zeros((hh,ww))
for i in range(hh):
    for j in range(ww):
        y0,y1,x0,x1=i*T,(i+1)*T-1,j*T,(j+1)*T-1
        loop=np.concatenate([phi[y0,x0:x1],phi[y0:y1,x1],phi[y1,x1:x0:-1],phi[y1:y0:-1,x0]])
        q[i,j]=np.round(wrap(np.diff(np.append(loop,loop[0]))).sum()/(2*np.pi))
q[~good]=np.nan; psi4[~good]=np.nan; cohm[~good]=np.nan; v=good
lowo=psi4<a.floor; q[lowo]=np.nan; vq=v&~lowo
print(f"{name}: {v.sum()} full tiles of {T}px")
print(f"  |psi4| tetratic order: median {np.nanmedian(psi4):.3f}  p10 {np.nanpercentile(psi4,10):.3f}  min {np.nanmin(psi4):.3f}")
print(f"  disclination charge (ordered tiles |psi4|>={a.floor}, {vq.sum()} of {v.sum()}): q!=0 in {100*np.nanmean(q[vq]!=0):.1f}%  mean|q| {np.nanmean(np.abs(q[vq])):.2f}  net {np.nansum(q[vq]):+.0f}")
print(f"  baseline coherence: median {np.nanmedian(cohm):.3f}  p10 {np.nanpercentile(cohm,10):.3f}   corr(psi4,coh) {np.corrcoef(psi4[v],cohm[v])[0,1]:.3f}")
np.savez(f"renders/{name}_tetratic.npz",psi4=psi4,q=q,coh=cohm)
fig,ax=plt.subplots(1,4,figsize=(18,4.8))
ax[0].imshow(I,cmap="gray"); ax[0].set_title("mid layer")
im=ax[1].imshow(psi4,vmin=0,vmax=1,cmap="magma"); ax[1].set_title("|psi4| tetratic order"); plt.colorbar(im,ax=ax[1],fraction=.046)
im=ax[2].imshow(q,cmap="coolwarm",vmin=-2,vmax=2); ax[2].set_title("disclination charge q (1/4 units)"); plt.colorbar(im,ax=ax[2],fraction=.046)
im=ax[3].imshow(cohm,vmin=0,vmax=1,cmap="viridis"); ax[3].set_title("baseline: ST coherence"); plt.colorbar(im,ax=ax[3],fraction=.046)
for x in ax: x.axis("off")
fig.suptitle(name); fig.tight_layout(); fig.savefig(f"renders/{name}_tetratic.png",dpi=90)
