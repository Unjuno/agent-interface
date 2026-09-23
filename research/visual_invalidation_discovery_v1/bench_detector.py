from __future__ import annotations
import json, math, os, platform, statistics, time
import numpy as np
import cv2

SEED=20260915
rng=np.random.default_rng(SEED)
H=W=256
ROI=(96,96,64,64)
TARGET=(116,116,24,24)
BASE=80
DELTA=40
SIGMA=2.0
N_QUALITY=2000
N_BENCH=12000

x,y,rw,rh=ROI
tx,ty,tw,th=TARGET

def make_pair(changed: bool, sigma: float=SIGMA):
    a=np.full((H,W), BASE, dtype=np.float32)
    b=np.full((H,W), BASE, dtype=np.float32)
    if changed:
        b[ty:ty+th, tx:tx+tw] += DELTA
    if sigma:
        a += rng.normal(0,sigma,a.shape)
        b += rng.normal(0,sigma,b.shape)
    a=np.clip(np.rint(a),0,255).astype(np.uint8)
    b=np.clip(np.rint(b),0,255).astype(np.uint8)
    return a,b

def roi(a):
    return a[y:y+rh,x:x+rw]

def d_full_any(a,b): return bool(np.any(a!=b))
def d_roi_any(a,b): return bool(np.any(roi(a)!=roi(b)))
def d_full_mad(a,b): return float(np.mean(np.abs(a.astype(np.int16)-b.astype(np.int16)))) >= 2.55
def d_roi_mad(a,b): return float(np.mean(np.abs(roi(a).astype(np.int16)-roi(b).astype(np.int16)))) >= 4.0

def d_roi_fraction(a,b):
    d=np.abs(roi(a).astype(np.int16)-roi(b).astype(np.int16))
    return float(np.count_nonzero(d>=12))/d.size >= 0.05

def d_roi_fraction_cv2(a,b):
    d=cv2.absdiff(roi(a),roi(b))
    _, m=cv2.threshold(d,11,255,cv2.THRESH_BINARY)
    return cv2.countNonZero(m)/m.size >= 0.05

DETS={
 'full_any':d_full_any,
 'roi_any':d_roi_any,
 'full_mad':d_full_mad,
 'roi_mad':d_roi_mad,
 'roi_fraction_np':d_roi_fraction,
 'roi_fraction_cv2':d_roi_fraction_cv2,
}

pairs_no=[make_pair(False) for _ in range(N_QUALITY)]
pairs_yes=[make_pair(True) for _ in range(N_QUALITY)]
quality={}
for name,f in DETS.items():
    fp=sum(f(a,b) for a,b in pairs_no)
    tp=sum(f(a,b) for a,b in pairs_yes)
    quality[name]={'false_positive_rate':fp/N_QUALITY,'false_negative_rate':1-tp/N_QUALITY,'tp':tp,'fp':fp}

bench_pairs=(pairs_no[:100]+pairs_yes[:100])
lat={}
for name,f in DETS.items():
    vals=[]
    for i in range(500): f(*bench_pairs[i%len(bench_pairs)])
    for i in range(N_BENCH):
        p=bench_pairs[i%len(bench_pairs)]
        t0=time.perf_counter_ns(); f(*p); t1=time.perf_counter_ns()
        vals.append((t1-t0)/1000.0)
    vals.sort()
    lat[name]={'median_us':statistics.median(vals),'p95_us':vals[math.ceil(.95*len(vals))-1],'p99_us':vals[math.ceil(.99*len(vals))-1]}

noise={}
for sigma in [0.0,0.5,1.0,2.0,4.0,8.0]:
    res={}; n=500
    no=[make_pair(False,sigma) for _ in range(n)]
    yes=[make_pair(True,sigma) for _ in range(n)]
    for name,f in DETS.items():
        fp=sum(f(a,b) for a,b in no); tp=sum(f(a,b) for a,b in yes)
        res[name]={'fpr':fp/n,'fnr':1-tp/n}
    noise[str(sigma)]=res

out={'env':{'python':platform.python_version(),'platform':platform.platform(),'cpu_count':os.cpu_count(),'numpy':np.__version__,'opencv':cv2.__version__},'fixture':{'frame':[H,W],'roi':ROI,'target':TARGET,'base':BASE,'delta':DELTA,'sigma_primary':SIGMA,'seed':SEED,'n_quality_per_class':N_QUALITY,'n_latency_calls':N_BENCH,'thresholds':{'full_mad':2.55,'roi_mad':4.0,'pixel_absdiff':12,'changed_fraction':0.05}},'quality':quality,'latency':lat,'noise_stress':noise}
print(json.dumps(out,indent=2))
