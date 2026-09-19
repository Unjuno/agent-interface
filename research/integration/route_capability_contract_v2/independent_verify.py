#!/usr/bin/env python3
import json,sys
from pathlib import Path
root=Path(sys.argv[1]).resolve() if len(sys.argv)>1 else Path(__file__).resolve().parent
r=json.loads((root/"formal-result.json").read_text()); ref=json.loads((root/"reference-v1-decisions.json").read_text()); exp=json.loads((root/"expected.json").read_text())
by={x["request_id"]:x for x in r["rows"]}; errors=[]
if len(by)!=10 or set(by)!=set(ref["rows"]): errors.append("row_identity")
for rid,w in ref["rows"].items():
    x=by.get(rid,{})
    if x.get("baseline")!=w["baseline"] or x.get("candidate")!=w["candidate"]: errors.append("decision_drift:"+rid)
def scan(arm):
    bad=[]
    for rid,x in by.items():
        y=x[arm]
        if y["status"]!="SELECTED": continue
        dims=r["catalog"].get(y["route"],{}).get("dims",[])
        if any(req not in dims for req in x["required_dimensions"]): bad.append(rid)
    return sorted(bad)
b=scan("baseline"); c=scan("candidate")
if b!=sorted(exp["baseline_semantic_weakening_rows"]): errors.append("baseline_set")
if c!=[]: errors.append("candidate_set")
out={"schema":"route-capability-independent-verifier-v2","pass":not errors,"errors":errors,"baseline_semantic_weakening_rows":b,"candidate_semantic_weakening_rows":c,"decision":"PASS_INDEPENDENT_AUDIT_COVERAGE" if not errors else "FAIL_INDEPENDENT_AUDIT_COVERAGE"}
if len(sys.argv)==1:(root/"independent-verifier.json").write_text(json.dumps(out,indent=2,sort_keys=True)+"\n")
print(json.dumps(out,sort_keys=True)); raise SystemExit(0 if out["pass"] else 1)
