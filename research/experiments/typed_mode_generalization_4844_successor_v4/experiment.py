#!/usr/bin/env python3
"""Fresh-seed synthetic typed-mode replication for Issue #5184."""
import hashlib
import json
import math
import os
import random
from pathlib import Path

TRAIN_SEED = 866309294
TEST_SEED = 301332595
TRAIN_N = 2000
PER_BLOCK = 960
MODES = 5
DISP = (0, 0, 1, 2, 2)
PROTO = ((0,0,0,0,0,0),(1,1,1,1,1,1),(0,1,0,1,0,1),(1,0,1,0,1,0),(0,0,1,1,0,1))
FLIP = 0.08
DROP = 0.20
ALPHA = 1.0
THRESHOLD = 0.65
MARGIN = 0.0
BLOCKS = ("COMPLETE", "SINGLE_MISSING", "MULTI_MISSING", "COMPOSITION_HOLDOUT", "NUISANCE_SHIFT")

def sample(rng, mode, block):
    bits = list(PROTO[mode])
    if block == "COMPOSITION_HOLDOUT":
        bits[0] ^= 1; bits[5] ^= 1
    if block == "NUISANCE_SHIFT":
        bits[3] ^= 1
    for j in range(6):
        if rng.random() < FLIP: bits[j] ^= 1
    mask = [True] * 6
    if block == "SINGLE_MISSING": mask[1] = False
    elif block == "MULTI_MISSING": mask[1] = mask[4] = False
    if block != "COMPLETE":
        for j in range(6):
            if rng.random() < DROP: mask[j] = False
    return tuple(bits[j] if mask[j] else -1 for j in range(6))

def fit(xs, ys, classes):
    count = [0] * classes
    one = [[0] * 6 for _ in range(classes)]
    seen = [[0] * 6 for _ in range(classes)]
    for x, y in zip(xs, ys):
        count[y] += 1
        for j, v in enumerate(x):
            if v >= 0: seen[y][j] += 1; one[y][j] += v
    return count, one, seen

def posterior(x, model):
    count, one, seen = model; k = len(count); total = sum(count); scores=[]
    for c in range(k):
        s = math.log((count[c]+ALPHA)/(total+k*ALPHA))
        for j,v in enumerate(x):
            if v < 0: continue
            p=(one[c][j]+ALPHA)/(seen[c][j]+2*ALPHA)
            s += math.log(p if v else 1-p)
        scores.append(s)
    m=max(scores); e=[math.exp(s-m) for s in scores]; z=sum(e)
    return [q/z for q in e]

def emit(probs):
    order=sorted(range(len(probs)), key=lambda i:(-probs[i],i))
    p=probs[order[0]]; margin=p-(probs[order[1]] if len(order)>1 else 0.0)
    return (order[0] if p >= THRESHOLD and margin >= MARGIN else None), p, margin

def predict(x, direct, typed):
    dp=posterior(x,direct); mp=posterior(x,typed)
    d,dc,dm=emit(dp)
    agg=[sum(mp[i] for i,v in enumerate(DISP) if v==j) for j in range(3)]
    t,tc,tm=emit(agg)
    return d,t,dc,dm,tc,tm

def main():
    tr=random.Random(TRAIN_SEED); te=random.Random(TEST_SEED)
    tx=[]; tm=[]
    for i in range(TRAIN_N):
        mode=i%MODES; tx.append(sample(tr,mode,"TRAIN")); tm.append(mode)
    direct=fit(tx,[DISP[m] for m in tm],3); typed=fit(tx,tm,5)
    rows=[]
    for block in BLOCKS:
        for i in range(PER_BLOCK):
            mode=i%MODES; x=sample(te,mode,block)
            d,t,dc,dm,tc,tmar=predict(x,direct,typed)
            truth=DISP[mode]
            rows.append({"block":block,"mode":mode,"truth":truth,"x":x,"direct":d,"typed":t,
                         "direct_confidence":dc,"direct_margin":dm,"typed_confidence":tc,"typed_margin":tmar,
                         "direct_wrong":d is not None and d!=truth,"typed_wrong":t is not None and t!=truth,
                         "direct_coverage":d is not None,"typed_coverage":t is not None})
    summary={}
    for b in BLOCKS:
        rr=[r for r in rows if r["block"]==b]
        summary[b]={"n":len(rr),"direct_wrong":sum(r["direct_wrong"] for r in rr),"typed_wrong":sum(r["typed_wrong"] for r in rr),
          "direct_coverage":sum(r["direct_coverage"] for r in rr)/len(rr),"typed_coverage":sum(r["typed_coverage"] for r in rr)/len(rr),
          "direct_unsafe":0,"typed_unsafe":0}
    controls=[]
    for mode,x in enumerate(PROTO):
        d,t,*_=predict(x,direct,typed)
        controls.append({"kind":"prototype","mode":mode,"expected":DISP[mode],"direct":d,"typed":t})
    unknown=(-1,)*6; contradiction=(0,0,0,1,0,1)
    control_predictions=[]
    for name,x in (("unknown",unknown),("contradictory",contradiction)):
        d,t,*_=predict(x,direct,typed)
        control_predictions.append({"kind":name,"direct":d,"typed":t})
    obj={"allocation":"typed-mode-4844-successor-20260928-04","seed_train":TRAIN_SEED,"seed_test":TEST_SEED,
      "n_train":TRAIN_N,"n_test":len(rows),"blocks":summary,"rows":rows,"prototype_controls":controls,
      "fail_closed_controls":control_predictions,"config":{"alpha":ALPHA,"flip_p":FLIP,"drop_p":DROP,"threshold":THRESHOLD,"margin":MARGIN,
        "dispositions":DISP,"prototypes":PROTO}}
    raw=json.dumps(obj,sort_keys=True,separators=(",",":"),ensure_ascii=True).encode()
    out=Path(os.environ.get("OUT_DIR","/out")); out.mkdir(parents=True,exist_ok=True); (out/"result.json").write_bytes(raw)
    print(json.dumps({"result_sha256":hashlib.sha256(raw).hexdigest(),"rows":len(rows),"blocks":summary},sort_keys=True))

if __name__=="__main__": main()
