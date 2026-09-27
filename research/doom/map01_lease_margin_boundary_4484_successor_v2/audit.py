#!/usr/bin/env python3
"""Independent arithmetic audit; imports neither runner nor frozen controller."""
import argparse, hashlib, json
from pathlib import Path
EXPECTED={"deadline-5s":"HOLD","deadline-5s249ms":"HOLD",
          "deadline-5s250ms":"SEND","deadline-6s":"SEND",
          "uncertainty-over-1s":"HOLD_UNCERTAINTY"}
def require(ok,msg):
    if not ok: raise ValueError(msg)
def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--raw",required=True); a=ap.parse_args()
    rawpath=Path(a.raw); raw=json.loads(rawpath.read_text(encoding="utf-8"))
    results=[]; errors=[]
    for c in raw["cases"]:
        cid=c["case_id"]; probes=c["probe_rows"]; reads=c["host_clock_reads_ns"]
        require(len(probes)==3,cid+": expected three probes")
        require(len(reads)>=6,cid+": missing host readings")
        bounds=[]
        for i,p in enumerate(probes):
            send,recv=reads[2*i:2*i+2]
            require(p["host_send_ns"]==send,cid+": send timestamp mismatch")
            require(recv-send==p["duration_ns"]>0,cid+": probe duration mismatch")
            bounds.append((p["runtime_ns"]-recv,p["runtime_ns"]-send))
        lower=min(x[0] for x in bounds); upper=max(x[1] for x in bounds)
        width=upper-lower; uncertain=width>1_000_000_000
        now=reads[6] if len(reads)>=7 else None
        remaining=c["host_deadline_ns"]-now if now is not None else None
        disposition=("HOLD_UNCERTAINTY" if uncertain else
                     "HOLD" if remaining is None or remaining<5_000_000_000 else "SEND")
        observed=("SEND" if len(c["emitted_submits"])==1 else
                  "HOLD_UNCERTAINTY" if c["exception"] and
                  "interval exceeds 1s" in c["exception"]["message"] else "HOLD")
        if disposition!=EXPECTED[cid] or observed!=disposition:
            errors.append({"case":cid,"expected":EXPECTED[cid],
                           "reconstructed":disposition,"observed":observed})
        if disposition=="SEND":
            require(c["exception"] is None,cid+": unexpected exception")
            require(len(c["emitted_submits"])==1,cid+": submit count")
            require(len(c["translation_rows"])==1,cid+": receipt count")
            row=c["translation_rows"][0]; translated=c["emitted_submits"][0]["valid_until_ns"]
            require(row["host_deadline_ns"]==c["host_deadline_ns"],cid+": host deadline mutated")
            require(row["runtime_deadline_ns"]==translated,cid+": translated deadline mismatch")
            require(row["offset_lower_ns"]==lower,cid+": offset is not minimum lower bound")
            runtime_remaining_at_lower=translated-(now+lower)
            host_remaining=c["host_deadline_ns"]-now
            require(runtime_remaining_at_lower==host_remaining,cid+": lower bound arithmetic")
            require(runtime_remaining_at_lower<=host_remaining,cid+": authorization extended")
        else:
            require(c["exception"] is not None,cid+": missing fail-closed exception")
            require(not c["emitted_submits"],cid+": submit escaped on HOLD")
            require(not c["translation_rows"],cid+": translation escaped on HOLD")
        results.append({"case_id":cid,"disposition":observed,"offset_lower_ns":lower,
                        "offset_upper_ns":upper,"uncertainty_width_ns":width,
                        "post_probe_remaining_ns":remaining,"probe_bounds_ns":bounds})
    result={"schema":"issue-5054-independent-boundary-audit-v1",
        "disposition":"PASS_BOUNDARY_CONSTRUCTION_SCOPED" if not errors else "FAIL_CONTRACT_OR_AUDIT",
        "case_count":len(results),"errors":errors,"cases":results,
        "raw_sha256":hashlib.sha256(rawpath.read_bytes()).hexdigest(),
        "source_sha256":raw["source_sha256"],
        "limits":["synthetic clocks only","no real socket, MAP01, model, OS input, freshness, or game efficacy",
                  "not authorization for any live allocation"]}
    (rawpath.parent/"audit.json").write_text(json.dumps(result,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print(result["disposition"]+" cases="+str(len(results))+" errors="+str(len(errors)))
    return len(errors)
if __name__=="__main__":
    ap=argparse.ArgumentParser(); ap.add_argument("--raw",required=True); args=ap.parse_args()
    raise SystemExit(main())
