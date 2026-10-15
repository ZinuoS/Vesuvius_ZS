"""Lock-in ink score: rev - k*fwd, k fitted on one crop, tested on the other. Also a two-sided veto."""
import numpy as np, tifffile, imageio.v3 as iio
team=iio.imread("control172/team_ink_w087_ds8.jpg"); team=team[...,0] if team.ndim==3 else team
def ds(f): p=tifffile.imread(f).astype(float); return p[:2048,:2048].reshape(256,8,256,8).mean((1,3))
def auc(q,t):
    ink=t>np.percentile(t,85); s=np.concatenate([q[ink],q[~ink]]); r=np.argsort(np.argsort(s)); n1=ink.sum()
    return (r[:n1].sum()-n1*(n1-1)/2)/(n1*(~ink).sum())
def corr(a,b): return np.corrcoef(a.ravel(),b.ravel())[0,1]
crops={"A":(5440,5120),"B":(1200,9200)}
D={}
for c,(cx,cy) in crops.items():
    t=team[cy//8:cy//8+256, cx//8:cx//8+256].astype(float)
    for S in [2,6]:
        n=f"predictions/scan/ctrl172_w087_{cx}_{cy}_S{S}"
        D[(c,S)]=(t, ds(n+"_reverse.tif"), ds(n+".tif"))
print(f"{'crop':4} {'S':>2} {'k':>6} | {'rev corr':>8} {'lockin corr':>11} | {'rev AUC':>7} {'lockin AUC':>10} | veto-kept%")
for S in [2,6]:
    for fit,test in [("A","B"),("B","A")]:
        t,r,f=D[(fit,S)]
        # k: least squares of residual t ~ r - k f  (after z-scoring maps)
        z=lambda v:(v-v.mean())/v.std(); rz,fz,tz=z(r),z(f),z(t)
        k=-np.linalg.lstsq(np.c_[fz.ravel()], (tz-rz).ravel(), rcond=None)[0][0]
        t2,r2,f2=D[(test,S)]; r2z,f2z=z(r2),z(f2)
        L=r2z-k*f2z
        # veto: suppress pixels where fwd is also high (both-sided = texture)
        both=(f2z>1.0)&(r2z>1.0); V=np.where(both, L.min(), L)
        print(f"{test:4} {S:>2} {k:+6.2f} | {corr(r2,t2):8.3f} {corr(L,t2):11.3f} | {auc(r2,t2):7.3f} {auc(L,t2):10.3f} | {100*(1-both.mean()):.1f}  (k fit on {fit}); veto corr {corr(V,t2):.3f}")
