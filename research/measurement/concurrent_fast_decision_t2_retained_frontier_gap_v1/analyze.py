from pathlib import Path
import json, math, statistics, sys

HERE=Path(__file__).resolve().parent
TASK="CONCURRENT-FAST-DECISION-T2-RETAINED-FRONTIER-GAP-20260918-009"

def percentile(xs,p):
    xs=sorted(xs); k=(len(xs)-1)*p; lo=math.floor(k); hi=math.ceil(k)
    if lo==hi:return xs[lo]
    return xs[lo]*(hi-k)+xs[hi]*(k-lo)

def main(out_path):
    src=json.loads((HERE/"INPUT.json").read_text())
    rows=src["rows"]
    if len(rows)!=10 or len({r["tag"] for r in rows})!=10: raise ValueError("expected ten unique rows")
    start_ms=[]; stdin_ms=[]; derived=[]
    meta_ok=True
    for r in rows:
        x=r["record"]
        meta_ok &= x["exit_code"]==0 and x["requested_model"]=="gpt-6-astra" and x["requested_effort"]=="medium"
        a=(x["exited_ns"]-x["started_ns"])/1e6
        b=(x["exited_ns"]-x["stdin_closed_ns"])/1e6
        if a<0 or b<0: raise ValueError("negative interval")
        start_ms.append(a); stdin_ms.append(b)
        derived.append({"tag":r["tag"],"git_blob":r["git_blob"],"start_to_exit_ms":a,"stdin_closed_to_exit_ms":b,
                        "observed_model_identity":x["observed_model_identity"],"cost":x["cost"]})
    deadline=float(src["frozen_t1_deadline_ms"]); local=float(src["frozen_t1_max_useful_effect_latency_ms"])
    stats={
      "n":len(rows),
      "start_to_exit_ms":{"min":min(start_ms),"median":statistics.median(start_ms),"p95":percentile(start_ms,.95),"max":max(start_ms)},
      "stdin_closed_to_exit_ms":{"min":min(stdin_ms),"median":statistics.median(stdin_ms),"p95":percentile(stdin_ms,.95),"max":max(stdin_ms)},
      "min_gap_to_deadline_ratio":min(stdin_ms)/deadline,
      "min_gap_to_t1_max_effect_ratio":min(stdin_ms)/local,
    }
    identity_unverified=all(r["record"]["observed_model_identity"] is None for r in rows)
    ok=meta_ok and min(stdin_ms)>deadline and local<deadline and identity_unverified
    decision="PASS_RETAINED_FRONTIER_GAP_ELIGIBLE_SCOPED" if ok else "HOLD_RETAINED_SAMPLE_HAS_NO_GAP"
    result={"task":TASK,"decision":decision,"analysis_invocations":1,"reruns":0,
            "requested_route":{"model":"gpt-6-astra","effort":"medium","served_identity_verified":False},
            "frozen_t1_deadline_ms":deadline,"frozen_t1_max_useful_effect_latency_ms":local,
            "stats":stats,"rows":derived,
            "scope":"retained historical requested-route subprocess intervals only; not a real-frontier T2 execution"}
    Path(out_path).write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    print(json.dumps({"decision":decision,"stats":stats},sort_keys=True))
if __name__=="__main__": main(sys.argv[1])
