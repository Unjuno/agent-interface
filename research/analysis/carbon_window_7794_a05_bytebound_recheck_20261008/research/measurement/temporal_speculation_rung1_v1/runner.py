from __future__ import annotations
import argparse,hashlib,json,random,statistics,time
from pathlib import Path

SEED=107420260918101
UNIVERSE=(-2,-1,1,2);K=2
HIT_BASE_NS=1_000_000
FALLBACK_BASE_NS=101_500_000
PRIMARY_PREDICTABLE=80_000
PRIMARY_AMBIGUOUS=20_000
CONTROL_N=20_000
ARMS=("wait","current","temporal")

def percentile(xs,p):
    ys=sorted(xs); k=(len(ys)-1)*p; lo=int(k); hi=min(lo+1,len(ys)-1); f=k-lo
    return ys[lo]*(1-f)+ys[hi]*f

def prepare(arm,kind,direction):
    t0=time.perf_counter_ns()
    if arm=="wait": branches=()
    elif arm=="current": branches=(-1,1)
    elif arm=="temporal":
        branches=(-1,1) if kind=="ambiguous" else (direction,2*direction)
    else: raise ValueError(arm)
    t1=time.perf_counter_ns()
    return branches,t1-t0

def score_effect(realized,action):
    return action is not None and action==realized

def evaluate(arm,kind,direction,realized,expired=False,authority=True):
    branches,compute=prepare(arm,kind,direction)
    prepared_no_authority=True
    fresh_match=realized in branches
    admit=bool(fresh_match and not expired and authority and arm!="wait")
    planner_resumed=False
    action=None; latency=None
    if admit:
        action=realized; latency=HIT_BASE_NS+compute
    elif authority:
        planner_resumed=True
        action=realized; latency=FALLBACK_BASE_NS+compute
    effect=score_effect(realized,action)
    return {
      "branches":branches,"compute_ns":compute,"fresh_match":fresh_match,"admitted":admit,
      "planner_resumed":planner_resumed,"action":action,"effect":effect,"latency_ns":latency,
      "prepared_no_authority":prepared_no_authority
    }

def make_primary():
    rng=random.Random(SEED); rows=[]
    for _ in range(PRIMARY_PREDICTABLE):
        d=1 if rng.getrandbits(1) else -1; u=rng.random()
        if u<.60:r=d
        elif u<.85:r=2*d
        elif u<.95:r=-d
        else:r=-2*d
        rows.append(("predictable",d,r))
    for _ in range(PRIMARY_AMBIGUOUS):
        d=1 if rng.getrandbits(1) else -1
        r=1 if rng.getrandbits(1) else -1
        rows.append(("ambiguous",d,r))
    return rows

def digest_rows(rows):
    h=hashlib.sha256()
    for row in rows:h.update(("%s,%d,%d\n"%row).encode())
    return h.hexdigest()

def summarize_primary(rows,arm):
    lat=[];comp=[];hits=0;resumes=0;effects=0;wrong=0;authority_launder=0
    for kind,d,r in rows:
        o=evaluate(arm,kind,d,r)
        lat.append(o["latency_ns"]);comp.append(o["compute_ns"])
        hits+=o["admitted"];resumes+=o["planner_resumed"];effects+=o["effect"]
        wrong+=bool(o["admitted"] and not o["effect"])
        authority_launder+=bool(o["admitted"] and not o["prepared_no_authority"])
    n=len(rows)
    return {
      "n":n,"branch_hits":hits,"branch_hit_rate":hits/n,"planner_resumptions":resumes,
      "planner_resumption_rate":resumes/n,"effect_correct":effects,"wrong_admissions":wrong,
      "authority_laundering":authority_launder,
      "latency_ns":{"mean":statistics.fmean(lat),"p50":percentile(lat,.5),"p95":percentile(lat,.95)},
      "prepare_compute_ns":{"mean":statistics.fmean(comp),"p95":percentile(comp,.95)}
    }

def controls(arm):
    rng=random.Random(SEED+1)
    out={"forced_reversal":{"n":CONTROL_N,"pre_fallback_admissions":0,"effects_correct":0},
         "expiry":{"n":CONTROL_N,"expired_admissions":0,"effects_correct":0},
         "no_authority":{"n":CONTROL_N,"admissions":0,"effects":0}}
    for _ in range(CONTROL_N):
        d=1 if rng.getrandbits(1) else -1
        o=evaluate(arm,"predictable",d,-2*d)
        out["forced_reversal"]["pre_fallback_admissions"]+=o["admitted"]
        out["forced_reversal"]["effects_correct"]+=o["effect"]
    for _ in range(CONTROL_N):
        d=1 if rng.getrandbits(1) else -1
        o=evaluate(arm,"predictable",d,d,expired=True)
        out["expiry"]["expired_admissions"]+=o["admitted"]
        out["expiry"]["effects_correct"]+=o["effect"]
    for _ in range(CONTROL_N):
        d=1 if rng.getrandbits(1) else -1
        o=evaluate(arm,"predictable",d,d,authority=False)
        out["no_authority"]["admissions"]+=o["admitted"]
        out["no_authority"]["effects"]+=o["effect"]
    return out

def main():
    ap=argparse.ArgumentParser();ap.add_argument("--out",required=True);a=ap.parse_args();out=Path(a.out)
    if out.exists():raise SystemExit("formal result exists")
    rows=make_primary()
    result={"task":"TEMPORAL-SPECULATION-COMPOSITION-RUNG1-20260918-001","formal_invocations":1,"reruns":0,
      "seed":SEED,"universe":list(UNIVERSE),"k":K,"primary_digest":digest_rows(rows),
      "planner_gap_ns":100_000_000,"hit_base_ns":HIT_BASE_NS,"fallback_base_ns":FALLBACK_BASE_NS,
      "arms":{},"controls":{},"grants_prepared_authority":False}
    for arm in ARMS:
        result["arms"][arm]=summarize_primary(rows,arm);result["controls"][arm]=controls(arm)
    out.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    print(json.dumps(result,sort_keys=True))
if __name__=="__main__":main()
