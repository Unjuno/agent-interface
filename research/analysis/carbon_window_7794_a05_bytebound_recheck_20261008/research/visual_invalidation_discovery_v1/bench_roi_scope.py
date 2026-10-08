from __future__ import annotations
import json, math, os, platform, statistics, time
import numpy as np
SEED=2026091503
rng=np.random.default_rng(SEED)
H=W=256; BASE=80; SIGMA=2.0; DELTA=16
CX=CY=128; TARGET_SIZE=12; N=1500; N_BENCH=10000
PIX_T=12; FRAC_T=0.05

def make(changed):
    a=np.full((H,W),BASE,np.float32); b=a.copy()
    if changed:
        s=TARGET_SIZE; lo=CX-s//2
        b[lo:lo+s,lo:lo+s]+=DELTA
    a+=rng.normal(0,SIGMA,a.shape); b+=rng.normal(0,SIGMA,b.shape)
    return np.clip(np.rint(a),0,255).astype(np.uint8),np.clip(np.rint(b),0,255).astype(np.uint8)

no=[make(False) for _ in range(N)]; yes=[make(True) for _ in range(N)]
res={}
for rs in [24,32,40,48,64,96,128,256]:
    lo=CX-rs//2
    def det(a,b):
        aa=a[lo:lo+rs,lo:lo+rs]; bb=b[lo:lo+rs,lo:lo+rs]
        d=np.abs(aa.astype(np.int16)-bb.astype(np.int16))
        return np.count_nonzero(d>=PIX_T)/d.size>=FRAC_T
    fp=sum(det(a,b) for a,b in no); tp=sum(det(a,b) for a,b in yes)
    bench=(no[:50]+yes[:50]); vals=[]
    for i in range(300): det(*bench[i%len(bench)])
    for i in range(N_BENCH):
        p=bench[i%len(bench)]; t0=time.perf_counter_ns(); det(*p); vals.append((time.perf_counter_ns()-t0)/1000)
    vals.sort()
    expected_frac=(TARGET_SIZE*TARGET_SIZE)/(rs*rs)
    res[str(rs)]={'target_area_fraction':expected_frac,'fpr':fp/N,'fnr':1-tp/N,'median_us':statistics.median(vals),'p95_us':vals[math.ceil(.95*len(vals))-1]}
print(json.dumps({'env':{'python':platform.python_version(),'platform':platform.platform(),'cpu_count':os.cpu_count()},'fixture':{'sigma':SIGMA,'delta':DELTA,'target_size':TARGET_SIZE,'pixel_threshold':PIX_T,'fraction_threshold':FRAC_T,'n_per_class':N,'seed':SEED},'results':res},indent=2))
