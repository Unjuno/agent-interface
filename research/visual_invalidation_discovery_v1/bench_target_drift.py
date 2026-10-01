from __future__ import annotations
import json, numpy as np, platform, os
SEED=2026091506
rng=np.random.default_rng(SEED)
BASE=80; SIGMA=2.0; DELTA=16; N=1500
T=12; RS=48; PIX_T=12; FRAC_T=.05
CENTER=RS//2

def pair(dx):
    a=np.full((RS,RS),BASE,np.float32); b=a.copy()
    tx=CENTER-T//2+dx; ty=CENTER-T//2
    x0=max(0,tx); x1=min(RS,tx+T); y0=max(0,ty); y1=min(RS,ty+T)
    if x0<x1 and y0<y1:
        b[y0:y1,x0:x1]+=DELTA
    a+=rng.normal(0,SIGMA,a.shape); b+=rng.normal(0,SIGMA,b.shape)
    return np.clip(np.rint(a),0,255).astype(np.uint8),np.clip(np.rint(b),0,255).astype(np.uint8)
res={}; threshold=FRAC_T*RS*RS
for dx in [0,8,12,16,18,19,20,21,22,24,28,32]:
    hits=0; counts=[]
    for _ in range(N):
        a,b=pair(dx); d=np.abs(a.astype(np.int16)-b.astype(np.int16)); c=int(np.count_nonzero(d>=PIX_T)); counts.append(c); hits+=int(c/d.size>=FRAC_T)
    res[str(dx)]={'hit_rate':hits/N,'median_changed_pixels':float(np.median(counts)),'p05_changed_pixels':float(np.quantile(counts,.05)),'threshold_pixels':threshold}
print(json.dumps({'env':{'python':platform.python_version(),'cpu_count':os.cpu_count()},'fixture':{'sigma':SIGMA,'delta':DELTA,'target_size':T,'roi_size':RS,'pixel_threshold':PIX_T,'fraction_threshold':FRAC_T,'n_per_offset':N,'seed':SEED},'results':res},indent=2))
