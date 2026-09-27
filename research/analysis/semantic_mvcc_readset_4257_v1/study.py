from __future__ import annotations
import json,sys,time
from pathlib import Path
READS=("target","dialog")

def semantic(state):
    t,d=state["target"],state["dialog"]
    if t[0] is None or t[1] is None or d[0] is None or d[1] is None:
        return "UNKNOWN"
    if t[0] != "A": return "TARGET_MISMATCH"
    if d[0] != "READY": return "DIALOG_BLOCKED"
    return "READY"

def snapshot(c):
    return c["start"]["obs"] == c["finish"]["obs"] and c["ready_ms"] <= c["deadline_ms"]

def readset(c):
    s,f=c["start"],c["finish"]
    valid=(c["ready_ms"] <= c["deadline_ms"] and s["intent"]==f["intent"] and s["producer"]==f["producer"] and s["epoch"]==f["epoch"])
    for k in READS:
        valid = valid and s[k][0] is not None and f[k][0] is not None and s[k][1] is not None and f[k][1] is not None and s[k]==f[k]
    return bool(valid)

def run(root):
    cases=json.loads((Path(root)/"cases.json").read_text()); rows=[]
    for i,c in enumerate(cases):
        start_result=semantic(c["start"]); finish_oracle=semantic(c["finish"])
        t0=time.perf_counter_ns(); strict=snapshot(c); t1=time.perf_counter_ns(); rs=readset(c); t2=time.perf_counter_ns()
        rows.append({"index":i,"name":c["name"],"case":c,"start_result":start_result,"finish_oracle":finish_oracle,
          "strict_snapshot":{"accept":strict,"committed":start_result if strict else None,"validation_ns":t1-t0},
          "read_set_validate":{"accept":rs,"committed":start_result if rs else None,"validation_ns":t2-t1},
          "authority_granted":False})
    return {"allocation":"semantic-mvcc-readset-4257-20260923-01","formal_invocations":1,"reruns":0,"replacements":0,"tuning":0,"rows":rows}
if __name__=="__main__":
    if len(sys.argv)!=3: raise SystemExit("usage: study.py ROOT OUTPUT")
    out=Path(sys.argv[2]); out.parent.mkdir(parents=True,exist_ok=True); out.write_text(json.dumps(run(sys.argv[1]),sort_keys=True,indent=2)+"\n")
