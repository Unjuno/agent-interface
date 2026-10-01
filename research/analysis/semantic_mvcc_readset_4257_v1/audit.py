from __future__ import annotations
import hashlib,json,sys
from pathlib import Path
READS=("target","dialog")

def sem(s):
    if any(s[k][0] is None or s[k][1] is None for k in READS): return "UNKNOWN"
    if s["target"][0] != "A": return "TARGET_MISMATCH"
    if s["dialog"][0] != "READY": return "DIALOG_BLOCKED"
    return "READY"

def rs_valid(c):
    s,f=c["start"],c["finish"]
    if c["ready_ms"]>c["deadline_ms"] or s["intent"]!=f["intent"] or s["producer"]!=f["producer"] or s["epoch"]!=f["epoch"]: return False
    return all(s[k][0] is not None and f[k][0] is not None and s[k][1] is not None and f[k][1] is not None and s[k]==f[k] for k in READS)

def strict_valid(c): return c["start"]["obs"]==c["finish"]["obs"] and c["ready_ms"]<=c["deadline_ms"]

def audit(root_path,formal_path):
    root=Path(root_path); obj=json.loads(Path(formal_path).read_text()); errors=[]; checks=0
    freeze=json.loads((root/"FREEZE.json").read_text())
    for name,dig in freeze["sha256"].items():
        checks+=1
        if hashlib.sha256((root/name).read_bytes()).hexdigest()!=dig: errors.append("source_hash:"+name)
    frozen=json.loads((root/"cases.json").read_text()); rows=obj.get("rows",[]); checks+=2
    if len(rows)!=10: errors.append("row_count")
    if [r.get("case") for r in rows]!=frozen: errors.append("case_binding")
    salvage=0; false_accepts=0; unnecessary=0
    for i,(c,r) in enumerate(zip(frozen,rows)):
        start=sem(c["start"]); finish=sem(c["finish"]); sv=strict_valid(c); rv=rs_valid(c); checks+=10
        if r.get("index")!=i or r.get("name")!=c["name"]: errors.append(f"{i}:identity")
        if r.get("start_result")!=start or r.get("finish_oracle")!=finish: errors.append(f"{i}:oracle")
        if r.get("strict_snapshot",{}).get("accept") is not sv: errors.append(f"{i}:strict")
        if r.get("read_set_validate",{}).get("accept") is not rv: errors.append(f"{i}:readset")
        if r.get("authority_granted") is not False: errors.append(f"{i}:authority")
        committed=r.get("read_set_validate",{}).get("committed")
        if rv and committed!=finish: false_accepts+=1; errors.append(f"{i}:false_commit")
        if rv and not sv: salvage+=1
        if (not rv) and start==finish and c["name"] not in ("TARGET_ABA_NEW_GENERATION",): unnecessary+=1
    checks+=9
    names={r["name"]:r for r in rows}
    for n in ("TOOLBAR_ONLY","TOOLBAR_ONLY_2"):
        if not names.get(n,{}).get("read_set_validate",{}).get("accept") or names[n]["strict_snapshot"]["accept"]: errors.append("salvage:"+n)
    for n in ("TARGET_CHANGED","DIALOG_CHANGED","DIALOG_UNKNOWN","INTENT_CHANGED","PRODUCER_CHANGED","TARGET_ABA_NEW_GENERATION","LATE_DEADLINE"):
        if names.get(n,{}).get("read_set_validate",{}).get("accept"): errors.append("must_reject:"+n)
    if salvage<2: errors.append("salvage_count")
    if false_accepts: errors.append("false_accepts")
    if obj.get("formal_invocations")!=1 or any(obj.get(k)!=0 for k in ("reruns","replacements","tuning")): errors.append("execution_discipline")
    decision="PASS_SEMANTIC_MVCC_READSET_SCOPED" if not errors else ("FAIL_FALSE_SEMANTIC_COMMIT" if false_accepts else "FAIL_INTEGRITY_OR_GATE")
    return {"decision":decision,"errors":errors,"checks":checks,"row_count":len(rows),"salvaged_correct_late_results":salvage,"false_accepts":false_accepts,"strict_accepts":sum(r.get("strict_snapshot",{}).get("accept") is True for r in rows),"readset_accepts":sum(r.get("read_set_validate",{}).get("accept") is True for r in rows),"formal_sha256":hashlib.sha256(Path(formal_path).read_bytes()).hexdigest()}
if __name__=="__main__":
    if len(sys.argv)!=3: raise SystemExit("usage: audit.py ROOT FORMAL")
    r=audit(sys.argv[1],sys.argv[2]); print(json.dumps(r,sort_keys=True,indent=2)); raise SystemExit(bool(r["errors"]))
