#!/usr/bin/env python3
"""Frozen one-shot candidate for exact rational action-schedule T0."""
from fractions import Fraction as F
import hashlib, json
from pathlib import Path

ROOT=Path(__file__).resolve().parent
fb=(ROOT/"FIXTURE.json").read_bytes(); fixture=json.loads(fb)
order=fixture["tie_order"]
def vec(v): return tuple(F(n,d) for n,d in v)
def norm2(a,b): return (a[0]-b[0])**2+(a[1]-b[1])**2
def in_hull(dictionary,v):
    # For these explicitly frozen dictionaries, the 4-way hull is |x|+|y|<=1;
    # the 8-way hull is the square [-1,1]^2.
    if dictionary=="4way": return abs(v[0])+abs(v[1])<=1
    return abs(v[0])<=1 and abs(v[1])<=1
def choose(actions,target,allowed):
    ranked=[]
    for name in order:
        if name in allowed:
            a=tuple(F(x) for x in actions[name]); ranked.append((norm2(a,target),order.index(name),name,a))
    return min(ranked)
def make(policy,c,actions):
    v=vec(c["v"]); n=c["horizon"]
    if c["mode"]=="outside_hull": return {"status":"UNREPRESENTABLE","moves":[],"positions":[],"prefix_error_sq":[],"switches":0,"final_release":True,"envelope_violations":0}
    if c["mode"]=="calibration_mismatch": return {"status":"STOP_CALIBRATION_MISMATCH","moves":[],"positions":[],"prefix_error_sq":[],"switches":0,"final_release":True,"envelope_violations":0}
    if c["mode"]=="hold_transfer": return {"status":"HOLD_TRANSFER","moves":[],"positions":[],"prefix_error_sq":[],"switches":0,"final_release":True,"envelope_violations":0}
    allowed=list(actions)
    if policy=="A_FIXED_HORIZON_NEAREST":
        _,_,nm,_=choose(actions,(v[0]*n/n,v[1]*n/n),allowed)
        seq=[nm]*n
    elif policy=="B_PER_SLOT_NEAREST_NO_CARRY":
        _,_,nm,_=choose(actions,v,allowed); seq=[nm]*n
    elif policy=="C_CUMULATIVE_ERROR_CARRY":
        pos=(F(0),F(0)); seq=[]
        for k in range(1,n+1):
            ideal=(v[0]*k,v[1]*k)
            ranked=[]
            for name in order:
                if name in actions:
                    a=tuple(F(x) for x in actions[name]); nxt=(pos[0]+a[0],pos[1]+a[1])
                    ranked.append((norm2(nxt,ideal),order.index(name),name,nxt))
            _,_,nm,pos=min(ranked); seq.append(nm)
    else: seq=["RELEASE"]*n
    pos=(F(0),F(0)); positions=[]; errors=[]; violations=0
    box=fixture["safety_box"]
    for k,name in enumerate(seq,1):
        a=tuple(F(x) for x in actions[name]); pos=(pos[0]+a[0],pos[1]+a[1]); positions.append([str(pos[0]),str(pos[1])])
        errors.append(str(norm2(pos,(v[0]*k,v[1]*k))))
        if not(box["xmin"]<=pos[0]<=box["xmax"] and box["ymin"]<=pos[1]<=box["ymax"]): violations+=1
    switches=sum(seq[i]!=seq[i-1] for i in range(1,len(seq))) + (seq[0]!="RELEASE") + (seq[-1]!="RELEASE")
    return {"status":"SCHEDULED","moves":seq,"positions":positions,"prefix_error_sq":errors,
            "terminal_error_sq":errors[-1] if errors else "0","worst_prefix_error_sq":str(max(map(F,errors),default=F(0))),
            "switches":switches,"final_release":True,"envelope_violations":violations}
rows=[]
for c in fixture["cases"]:
    actions=fixture["dictionaries"][c["dictionary"]]["actions"]
    policies={p:make(p,c,actions) for p in fixture["policies"]}
    rows.append({"case_id":c["id"],"policies":policies})
raw={"schema":"discrete-intent-t0-raw-v1","fixture_sha256":hashlib.sha256(fb).hexdigest(),"rows":rows}
out=ROOT/"results/t0/RAW.json"
if out.exists(): raise SystemExit("STOP_OUTPUT_EXISTS_NO_RETRY")
out.parent.mkdir(parents=True,exist_ok=False)
data=(json.dumps(raw,sort_keys=True,separators=(",",":"))+"\n").encode();out.write_bytes(data)
print(json.dumps({"status":"CANDIDATE_RAW_WRITTEN","cases":len(rows),"policy_rows":len(rows)*4,"raw_sha256":hashlib.sha256(data).hexdigest()},sort_keys=True))
