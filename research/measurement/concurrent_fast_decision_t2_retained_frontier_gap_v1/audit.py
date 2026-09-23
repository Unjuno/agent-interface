from pathlib import Path
import json, math, statistics, sys, copy

HERE=Path(__file__).resolve().parent
def pct(xs,p):
    xs=sorted(xs); k=(len(xs)-1)*p; lo=math.floor(k); hi=math.ceil(k)
    return xs[lo] if lo==hi else xs[lo]*(hi-k)+xs[hi]*(k-lo)

def recompute(src):
    sm=[]; im=[]
    for r in src["rows"]:
        x=r["record"]; sm.append((x["exited_ns"]-x["started_ns"])/1e6); im.append((x["exited_ns"]-x["stdin_closed_ns"])/1e6)
    return {"n":len(im),
      "start_to_exit_ms":{"min":min(sm),"median":statistics.median(sm),"p95":pct(sm,.95),"max":max(sm)},
      "stdin_closed_to_exit_ms":{"min":min(im),"median":statistics.median(im),"p95":pct(im,.95),"max":max(im)},
      "min_gap_to_deadline_ratio":min(im)/src["frozen_t1_deadline_ms"],
      "min_gap_to_t1_max_effect_ratio":min(im)/src["frozen_t1_max_useful_effect_latency_ms"]}

def close(a,b,tol=1e-9):
    if isinstance(a,dict): return a.keys()==b.keys() and all(close(a[k],b[k],tol) for k in a)
    if isinstance(a,(int,float)) and isinstance(b,(int,float)): return abs(a-b)<=tol*max(1,abs(a),abs(b))
    return a==b

def main(result_path,out_path):
    src=json.loads((HERE/"INPUT.json").read_text()); res=json.loads(Path(result_path).read_text())
    errors=[]
    if res["task"]!=src["task"]: errors.append("task")
    expected=recompute(src)
    if not close(expected,res["stats"]): errors.append("stats")
    if res["analysis_invocations"]!=1 or res["reruns"]!=0: errors.append("invocation")
    if res["requested_route"]["served_identity_verified"] is not False: errors.append("identity_claim")
    if any(r["record"]["observed_model_identity"] is not None for r in src["rows"]): errors.append("input_identity_changed")
    if min(x["record"]["exited_ns"]-x["record"]["stdin_closed_ns"] for x in src["rows"]) <= int(src["frozen_t1_deadline_ms"]*1e6): errors.append("gap")
    controls={}
    bad=copy.deepcopy(src); bad["rows"][0]["record"]["requested_model"]="other"
    controls["model_mismatch_detected"]=bad["rows"][0]["record"]["requested_model"]!="gpt-6-astra"
    bad2=copy.deepcopy(src); bad2["rows"][0]["record"]["exited_ns"]=bad2["rows"][0]["record"]["stdin_closed_ns"]+1_000_000
    controls["deadline_violation_detected"]=min((r["record"]["exited_ns"]-r["record"]["stdin_closed_ns"])/1e6 for r in bad2["rows"])<=src["frozen_t1_deadline_ms"]
    bad3=copy.deepcopy(res); bad3["stats"]["n"]=9
    controls["stats_corruption_detected"]=not close(expected,bad3["stats"])
    if not all(controls.values()): errors.append("controls")
    out={"task":src["task"],"pass":not errors,"errors":errors,"corruption_controls":controls,
         "decision":res["decision"],"audit_invocations":1}
    Path(out_path).write_text(json.dumps(out,indent=2,sort_keys=True)+"\n")
    print(json.dumps(out,sort_keys=True))
    raise SystemExit(0 if not errors else 2)
if __name__=="__main__": main(sys.argv[1],sys.argv[2])
