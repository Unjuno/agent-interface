import argparse, copy, json
from pathlib import Path

def evaluate(r):
    m=r["metrics"]; errs=[]
    if r.get("task")!="PERSISTENT-GEOMETRIC-WORLD-STATE-R0-20260918-001": errs.append("task")
    if r.get("reruns")!=0 or r.get("replacements")!=0 or r.get("tuning")!=0: errs.append("allocation_counters")
    if m.get("candidate_oracle_mismatch")!=0: errs.append("oracle_mismatch")
    if m.get("candidate_false_current")!=0: errs.append("false_current")
    if m.get("candidate_overinvalidations")!=0: errs.append("overinvalidate")
    if m.get("compaction_semantic_changes")!=0: errs.append("compaction_changed")
    if m.get("fresh_reobservations_current",0)<=0: errs.append("no_fresh_reobserve")
    if m.get("baseline_false_current",0)<=0: errs.append("no_discriminator")
    if r.get("phase")=="formal":
        if r.get("formal_invocations")!=1 or m.get("traces")!=200000: errs.append("formal_shape")
        for k in ("aba_stress","compact_stress","occlude_stress","infer_stress"):
            if m.get(k,0)<40000: errs.append(k)
    return errs

def controls(r):
    out={}
    for name,key,val in [("false_current","candidate_false_current",1),("oracle","candidate_oracle_mismatch",1),
                         ("overinvalidate","candidate_overinvalidations",1),("compaction","compaction_semantic_changes",1),
                         ("baseline","baseline_false_current",0)]:
        q=copy.deepcopy(r); q["metrics"][key]=val
        out[name]=bool(evaluate(q))
    return out

if __name__=="__main__":
    ap=argparse.ArgumentParser(); ap.add_argument("result"); ap.add_argument("--out",required=True); a=ap.parse_args()
    r=json.loads(Path(a.result).read_text()); errs=evaluate(r); cc=controls(r)
    o={"errors":errs,"corruption_controls":cc,"controls_pass":all(cc.values()),"pass":not errs and all(cc.values())}
    Path(a.out).write_text(json.dumps(o,indent=2,sort_keys=True)+"\n")
    print(json.dumps(o,indent=2,sort_keys=True))
    raise SystemExit(0 if o["pass"] else 4)
