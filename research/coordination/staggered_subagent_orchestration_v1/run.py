import hashlib, json, pathlib

SCENARIOS = [
 {"id":"independent_read", "critical":"low", "resource":"r1", "release":True},
 {"id":"resource_conflict", "critical":"high", "resource":"exclusive", "release":False},
 {"id":"stale_during_delay", "critical":"high", "resource":"r2", "release":"stale"},
 {"id":"predecessor_failed", "critical":"high", "resource":"r3", "release":"failed"},
 {"id":"postcondition_gate", "critical":"high", "resource":"r4", "release":True},
 {"id":"duplicate_restart_cancel_expiry", "critical":"high", "resource":"r5", "release":"expired"},
]
POLICIES=("IMMEDIATE","FIXED_STAGGER","CONDITION_STAGGER","SERIAL_CRITICAL")
def allowed(policy, s):
    if s["critical"]=="low": return True
    if policy=="CONDITION_STAGGER": return s["release"] is True
    if policy=="SERIAL_CRITICAL": return s["release"] is True
    return True
def main(out):
    rows=[]
    for s in SCENARIOS:
      for p in POLICIES:
        ok=allowed(p,s); unsafe=ok and s["release"] is not True
        rows.append({"scenario":s["id"],"policy":p,"criticality":s["critical"],"resource":s["resource"],"release":s["release"],"start":"allowed" if ok else "deferred","unsafe":unsafe,"trace":"held-out-runtime-trace-v1"})
    data={"schema":"staggered-subagent-orchestration-v1","scenarios":SCENARIOS,"policies":POLICIES,"rows":rows}
    p=pathlib.Path(out); p.mkdir(parents=True,exist_ok=True); (p/'RAW.json').write_text(json.dumps(data,sort_keys=True,indent=2)+'\n')
    print(json.dumps({"rows":len(rows),"sha256":hashlib.sha256((p/'RAW.json').read_bytes()).hexdigest()}))
if __name__=='__main__': import sys; main(sys.argv[1])
