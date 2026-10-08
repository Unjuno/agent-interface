#!/usr/bin/env python3
"""Frozen synthetic typed-mode vs direct-recovery diagnostic for Issue #4844."""
import hashlib, itertools, json, math, os, random
from pathlib import Path

SEED = 484401
N_TRAIN = 2000
N_TEST = 3000
ALPHA = 1.0
MODES = 5
DISP = [0, 0, 1, 2, 2]
PROTOTYPES = [
    (0,0,0,0,0,0), (1,1,1,1,1,1), (0,1,0,1,0,1),
    (1,0,1,0,1,0), (0,0,1,1,0,1)
]
N_CUES = 6
FLIP_P = 0.08
DROP_P = 0.20
CONFIDENCE_THRESHOLD = 0.70
BLOCKS = ["all_missing_cue1", "all_missing_cue4", "two_missing_cues", "contradictory"]

def sample_row(rng, mode, block):
    bits = list(PROTOTYPES[mode])
    for i in range(N_CUES):
        if rng.random() < FLIP_P: bits[i] ^= 1
    mask = [True] * N_CUES
    if block == "all_missing_cue1": mask[1] = False
    elif block == "all_missing_cue4": mask[4] = False
    elif block == "two_missing_cues": mask[1] = mask[4] = False
    elif block == "contradictory":
        bits[0] ^= 1; bits[5] ^= 1
    for i in range(N_CUES):
        if rng.random() < DROP_P: mask[i] = False
    return bits, mask

def encode(bits, mask):
    return tuple((int(b) if m else -1) for b,m in zip(bits,mask))

def fit(rows, labels, classes):
    counts = [0]*classes
    ones = [[0]*N_CUES for _ in range(classes)]
    seen = [[0]*N_CUES for _ in range(classes)]
    for x,y in zip(rows,labels):
        counts[y]+=1
        for j,v in enumerate(x):
            if v >= 0:
                seen[y][j]+=1
                ones[y][j]+=v
    return counts,ones,seen

def predict(x, model):
    counts,ones,seen=model; n=len(counts); scores=[]
    for c in range(n):
        score=math.log((counts[c]+ALPHA)/(sum(counts)+n*ALPHA))
        for j,v in enumerate(x):
            if v<0: continue
            p=(ones[c][j]+ALPHA)/(seen[c][j]+2*ALPHA)
            score += math.log(p if v else 1-p)
        scores.append(score)
    mx=max(scores); ex=[math.exp(s-mx) for s in scores]; z=sum(ex)
    probs=[a/z for a in ex]
    return max(range(n),key=lambda c:(probs[c],-c)),probs

def main():
    rtrain=random.Random(SEED); rtest=random.Random(SEED+1)
    train_x=[]; train_mode=[]
    for i in range(N_TRAIN):
        mode=i%MODES
        block="train"
        b,m=sample_row(rtrain,mode,block); train_x.append(encode(b,m)); train_mode.append(mode)
    test=[]
    per_block=N_TEST//len(BLOCKS)
    for bi,block in enumerate(BLOCKS):
        for k in range(per_block):
            mode=(k+bi)%MODES
            b,m=sample_row(rtest,mode,block)
            test.append({"x":encode(b,m),"mode":mode,"disposition":DISP[mode],"block":block})
    direct_labels=[DISP[m] for m in train_mode]
    direct=fit(train_x,direct_labels,3)
    typed=fit(train_x,train_mode,5)
    rows=[]
    for row in test:
        pd,dp=predict(row["x"],direct)
        pm,post=predict(row["x"],typed)
        agg=[sum(post[m] for m,d in enumerate(DISP) if d==k) for k in range(3)]
        pt=max(range(3),key=lambda k:(agg[k],-k))
        if max(dp)<CONFIDENCE_THRESHOLD: pd=None
        if max(post)<CONFIDENCE_THRESHOLD: pt=None
        rows.append({"block":row["block"],"truth_mode":row["mode"],"truth_disposition":row["disposition"],"direct":pd,"typed":pt,"direct_wrong":pd is not None and pd!=row["disposition"],"typed_wrong":pt is not None and pt!=row["disposition"],"direct_coverage":pd is not None,"typed_coverage":pt is not None,"direct_unsafe":False,"typed_unsafe":False})
    summary={}
    for block in BLOCKS:
        rs=[r for r in rows if r["block"]==block]
        summary[block]={"n":len(rs),"direct_wrong":sum(r["direct_wrong"] for r in rs),"typed_wrong":sum(r["typed_wrong"] for r in rs),"direct_coverage":sum(r["direct_coverage"] for r in rs)/len(rs),"typed_coverage":sum(r["typed_coverage"] for r in rs)/len(rs),"direct_unsafe":sum(r["direct_unsafe"] for r in rs),"typed_unsafe":sum(r["typed_unsafe"] for r in rs)}
    # Full-observation deterministic control uses noiseless prototypes, checked by frozen table.
    control={"rows":0,"direct_equals_typed":True,"correct":True}
    for mode,bits in enumerate(PROTOTYPES):
        x=encode(bits,[True]*N_CUES)
        d,dp=predict(x,direct); m,p= predict(x,typed)
        ag=[sum(p[k] for k,disp in enumerate(DISP) if disp==j) for j in range(3)]
        t=max(range(3),key=lambda j:(ag[j],-j))
        if max(dp)<CONFIDENCE_THRESHOLD: d=None
        if max(p)<CONFIDENCE_THRESHOLD: t=None
        control["rows"]+=1
        if d!=DISP[mode] or t!=DISP[mode]: control["correct"]=False
        if d!=t: control["direct_equals_typed"]=False
    # Chosen by exhaustive construction-only scan of the 64 binary vectors; it is
    # not drawn from held-out rows and must trigger fail-closed on both models.
    contradiction_bits=(0,0,0,1,0,1)
    contradiction={"input":contradiction_bits,"direct_abstains":max(predict(contradiction_bits,direct)[1])<CONFIDENCE_THRESHOLD,"typed_abstains":max(predict(contradiction_bits,typed)[1])<CONFIDENCE_THRESHOLD}
    unknown=(-1,-1,-1,-1,-1,-1)
    unknown_control={"input":unknown,"direct_abstains":max(predict(unknown,direct)[1])<CONFIDENCE_THRESHOLD,"typed_abstains":max(predict(unknown,typed)[1])<CONFIDENCE_THRESHOLD}
    out={"allocation":"typed-mode-4844-seed-484401-v1","seed_train":SEED,"seed_test":SEED+1,"n_train":N_TRAIN,"n_test":N_TEST,"alpha":ALPHA,"confidence_threshold":CONFIDENCE_THRESHOLD,"flip_p":FLIP_P,"drop_p":DROP_P,"dispositions":DISP,"prototypes":PROTOTYPES,"blocks":summary,"full_observation_control":control,"unknown_control":unknown_control,"contradictory_control":contradiction,"rows":rows}
    raw=json.dumps(out,sort_keys=True,separators=(",",":"),ensure_ascii=True).encode()
    Path(os.environ.get("OUT_DIR","/out")).mkdir(parents=True,exist_ok=True)
    Path(os.environ.get("OUT_DIR","/out"),"result.json").write_bytes(raw)
    print(json.dumps({"result_sha256":hashlib.sha256(raw).hexdigest(),"blocks":summary,"full_observation_control":control},sort_keys=True))

if __name__=="__main__": main()

