from __future__ import annotations
import json, math, os, platform, statistics, threading, time
import numpy as np
SEED=2026091504
rng=np.random.default_rng(SEED)
H=W=256; BASE=80; SIGMA=2.0; DELTA=16
CX=CY=128; TARGET_SIZE=12; ROI_SIZE=48
PIX_T=12; FRAC_T=.05
N=60
lo=CX-ROI_SIZE//2

def make(changed):
    a=np.full((H,W),BASE,np.float32)
    if changed:
        s=TARGET_SIZE; tl=CX-s//2; a[tl:tl+s,tl:tl+s]+=DELTA
    a+=rng.normal(0,SIGMA,a.shape)
    return np.clip(np.rint(a),0,255).astype(np.uint8)
ref=make(False)
valid_frames=[make(False) for _ in range(128)]
invalid_frames=[make(True) for _ in range(128)]

def det(cur):
    aa=ref[lo:lo+ROI_SIZE,lo:lo+ROI_SIZE]
    bb=cur[lo:lo+ROI_SIZE,lo:lo+ROI_SIZE]
    d=np.abs(aa.astype(np.int16)-bb.astype(np.int16))
    return np.count_nonzero(d>=PIX_T)/d.size>=FRAC_T

def quant(v,q):
    s=sorted(v); return s[math.ceil(q*len(s))-1]

results={}
for hz in [30,60,120,240]:
    interval=1.0/hz
    lats=[]; checks=[]; sched_lag=[]
    for trial in range(N):
        state=threading.Event(); stamp={}
        delay=0.020 + float(rng.uniform(0,interval))
        def flip():
            time.sleep(delay); stamp['t']=time.perf_counter(); state.set()
        th=threading.Thread(target=flip); th.start()
        start=time.perf_counter(); next_t=start; i=0; detected=None; lag_samples=[]
        while True:
            now=time.perf_counter()
            if now < next_t:
                time.sleep(max(0,next_t-now))
            actual=time.perf_counter(); lag_samples.append(max(0,actual-next_t))
            frames=invalid_frames if state.is_set() else valid_frames
            cur=frames[i%len(frames)]; i+=1
            if det(cur) and state.is_set():
                detected=time.perf_counter(); break
            next_t += interval
            if actual-start>0.25: break
        th.join()
        if detected is None or 't' not in stamp: raise RuntimeError('no detection')
        lats.append((detected-stamp['t'])*1000); checks.append(i); sched_lag.extend(x*1000 for x in lag_samples)
    results[str(hz)]={'median_event_to_detect_ms':statistics.median(lats),'p95_ms':quant(lats,.95),'max_ms':max(lats),'median_checks':statistics.median(checks),'median_schedule_lag_ms':statistics.median(sched_lag),'p95_schedule_lag_ms':quant(sched_lag,.95),'detector_compute_budget_fraction_est':None}
vals=[]
for i in range(15000):
    cur=(valid_frames+invalid_frames)[i%256]
    t0=time.perf_counter_ns(); det(cur); vals.append((time.perf_counter_ns()-t0)/1e9)
med=statistics.median(vals)
for hz,row in results.items(): row['detector_compute_budget_fraction_est']=med*int(hz)
print(json.dumps({'env':{'python':platform.python_version(),'platform':platform.platform(),'cpu_count':os.cpu_count()},'fixture':{'sigma':SIGMA,'delta':DELTA,'target_size':TARGET_SIZE,'roi_size':ROI_SIZE,'n_per_cadence':N,'seed':SEED,'note':'in-memory pre-generated frames; no X11 capture cost'},'detector_median_compute_us':med*1e6,'results':results},indent=2))
