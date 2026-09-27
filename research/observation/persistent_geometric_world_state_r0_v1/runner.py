import argparse, json, random
from candidate import TypedWorldState, LatestGeometryOnly
from oracle import HistoryOracle

SEED=152620260918001
ENTITIES=16
CATEGORIES=("ABA","COMPACT","OCCLUDE","INFER","MIXED")

def nrm(x): return ("UNKNOWN",) if x[0]=="UNKNOWN" else x

def apply_all(objs,op,*args):
    for o in objs: getattr(o,op)(*args)

def run_trace(i,rng,c,o,b):
    e=i%ENTITIES
    cat=CATEGORIES[i%len(CATEGORIES)]
    epoch=i*10+1
    base=(rng.randrange(0,500),rng.randrange(0,500),10+rng.randrange(0,30),10+rng.randrange(0,30))
    fresh=(base[0]+1,base[1]+1,base[2],base[3])
    before_compact=None
    flags={"aba":0,"compact":0,"occlude":0,"infer":0,"fresh_reobserve":0}
    apply_all((c,o,b),"advance_generation",e)
    apply_all((c,o,b),"observe",e,epoch,base)
    epoch+=1

    if cat=="ABA":
        flags["aba"]=1
        apply_all((c,o,b),"advance_generation",e)
        c.query_current(e); o.query_current(e); b.query_current(e)
        apply_all((c,o,b),"observe",e,epoch,fresh)
        flags["fresh_reobserve"]=1
    elif cat=="COMPACT":
        flags["compact"]=1
        before_compact=c.query_current(e)
        apply_all((c,o,b),"compact")
    elif cat=="OCCLUDE":
        flags["occlude"]=1
        apply_all((c,o,b),"occlude",e,epoch)
    elif cat=="INFER":
        flags["infer"]=1
        apply_all((c,o,b),"infer",e,epoch,fresh)
    else:
        flags["compact"]=1; flags["infer"]=1
        apply_all((c,o,b),"compact")
        apply_all((c,o,b),"advance_generation",e)
        apply_all((c,o,b),"infer",e,epoch,fresh)

    cq,oq,bq=c.query_current(e),o.query_current(e),b.query_current(e)
    mismatch=nrm(cq)!=nrm(oq)
    baseline_false=(oq[0]=="UNKNOWN" and bq[0]=="CURRENT_OBSERVED")
    compaction_changed=(before_compact is not None and cq!=before_compact)
    fresh_ok=(flags["fresh_reobserve"] and cq[0]=="CURRENT_OBSERVED")
    stale_leak=(oq[0]=="UNKNOWN" and cq[0]=="CURRENT_OBSERVED")
    overinvalidate=(oq[0]=="CURRENT_OBSERVED" and cq[0]!="CURRENT_OBSERVED")
    return {"mismatch":mismatch,"baseline_false":baseline_false,"compaction_changed":compaction_changed,
            "fresh_ok":bool(fresh_ok),"stale_leak":stale_leak,"overinvalidate":overinvalidate,**flags}

def execute(traces):
    rng=random.Random(SEED)
    c,o,b=TypedWorldState(ENTITIES),HistoryOracle(ENTITIES),LatestGeometryOnly(ENTITIES)
    m={"traces":traces,"seed":SEED,"candidate_oracle_mismatch":0,"baseline_false_current":0,
       "compaction_semantic_changes":0,"fresh_reobservations_current":0,"candidate_false_current":0,
       "candidate_overinvalidations":0,"aba_stress":0,"compact_stress":0,"occlude_stress":0,"infer_stress":0}
    for i in range(traces):
        r=run_trace(i,rng,c,o,b)
        m["candidate_oracle_mismatch"]+=r["mismatch"]
        m["baseline_false_current"]+=r["baseline_false"]
        m["compaction_semantic_changes"]+=r["compaction_changed"]
        m["fresh_reobservations_current"]+=r["fresh_ok"]
        m["candidate_false_current"]+=r["stale_leak"]
        m["candidate_overinvalidations"]+=r["overinvalidate"]
        m["aba_stress"]+=r["aba"]; m["compact_stress"]+=r["compact"]
        m["occlude_stress"]+=r["occlude"]; m["infer_stress"]+=r["infer"]
    formal=traces==200000
    gates=[m["candidate_oracle_mismatch"]==0,m["candidate_false_current"]==0,m["candidate_overinvalidations"]==0,
           m["compaction_semantic_changes"]==0,m["fresh_reobservations_current"]>0,m["baseline_false_current"]>0]
    if formal:
        gates += [m["aba_stress"]>=40000,m["compact_stress"]>=40000,m["occlude_stress"]>=40000,m["infer_stress"]>=40000]
    if not all(gates):
        decision="FAIL_PROVENANCE_AUTHORITY_LEAK" if m["candidate_false_current"] else "FAIL_CURRENT_GEOMETRY_OVERINVALIDATION" if m["candidate_overinvalidations"] else "FAIL_INTEGRITY"
    else:
        decision="PASS_PERSISTENT_GEOMETRIC_STATE_PROVENANCE_R0_SCOPED" if formal else "PASS_CONSTRUCTION_ELIGIBLE"
    return {"task":"PERSISTENT-GEOMETRIC-WORLD-STATE-R0-20260918-001","phase":"formal" if formal else "construction",
            "formal_invocations":1 if formal else 0,"reruns":0,"replacements":0,"tuning":0,"decision":decision,"metrics":m}

if __name__=="__main__":
    ap=argparse.ArgumentParser(); ap.add_argument("--traces",type=int,default=1000); ap.add_argument("--out",required=True); a=ap.parse_args()
    out=execute(a.traces)
    with open(a.out,"w") as f: json.dump(out,f,indent=2,sort_keys=True)
    print(json.dumps(out,indent=2,sort_keys=True))
