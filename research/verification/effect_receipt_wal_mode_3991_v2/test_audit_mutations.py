#!/usr/bin/env python3
"""Independent-auditor corruption suite over the retained formal corpus."""
import copy, json, pathlib, sys
sys.path.insert(0,str(pathlib.Path(__file__).parent))
import audit_raw

def main(rows_path):
    p=pathlib.Path(rows_path); out=p.parent; rows=json.loads(p.read_text())
    baseline=audit_raw.audit(str(p))
    if baseline["errors"]: raise SystemExit(f"baseline audit failed: {baseline}")
    case=next(r for r in rows if r.get("protocol")=="EFFECT_FIRST" and r.get("cut")=="AFTER_FIRST" and r.get("mode")=="DELETE")
    mutations=[]
    for key,value in (("effects",1),("receipt_count",0),("retry",False),("receipt_status","COMPLETED"),("child_exit",0),("protocol","ATOMIC_LOCAL"),("mode","WAL"),("cut","AFTER_SECOND"),("dir","/tmp/outside")):
        m=copy.deepcopy(case); m[key]=value; mutations.append(m)
    m=copy.deepcopy(case); m["pre_recovery_files"][0]["sha256"]="0"*64; mutations.append(m)
    m=copy.deepcopy(case); m["pre_recovery_files"][0]["name"]="missing.db"; mutations.append(m)
    control=copy.deepcopy(next(r for r in rows if "control" in r)); control["result"]="ACCEPTED"; mutations.append(control)
    control=copy.deepcopy(next(r for r in rows if "control" in r)); control["effects"]=1; mutations.append(control)
    rejected=0
    for m in mutations:
        if audit_raw.audit_row(m,out): rejected+=1
    if rejected!=len(mutations): raise SystemExit(f"corruption controls rejected {rejected}/{len(mutations)}")
    print(f"PASS_RAW_AUDIT_MUTATIONS rejected={rejected}/{len(mutations)}")

if __name__=="__main__": main(sys.argv[1])
