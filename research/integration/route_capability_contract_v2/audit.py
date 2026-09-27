#!/usr/bin/env python3
import hashlib,json,sys
from pathlib import Path

def blob(b): return hashlib.sha1(b"blob "+str(len(b)).encode()+b"\0"+b).hexdigest()

def weakenings(result, arm):
    out=[]; cat=result["catalog"]
    for row in result["rows"]:
        d=row[arm]
        if d.get("status")=="SELECTED":
            route=d.get("route"); required=set(row["required_dimensions"]); have=set(cat.get(route,{}).get("dims",[]))
            if not required <= have: out.append(row["request_id"])
    return sorted(out)

def audit(root: Path):
    errors=[]
    ids={"scale-audit.json":"389fe8cd93603c0415480fc398664a903dede0f4","center-summary.json":"28bc4a8c07958db58efe98eb73881cbced46c481"}
    for n,h in ids.items():
        if blob((root/"evidence"/n).read_bytes())!=h: errors.append("evidence:"+n)
    result=json.loads((root/"formal-result.json").read_text()); expected=json.loads((root/"expected.json").read_text()); ref=json.loads((root/"reference-v1-decisions.json").read_text())
    rows=result.get("rows",[]); by={r["request_id"]:r for r in rows}
    if result.get("formal_invocations")!=1: errors.append("formal_invocations")
    if len(rows)!=expected["row_count"] or set(by)!=set(ref["rows"]): errors.append("row_identity")
    for rid,want in ref["rows"].items():
        got=by.get(rid)
        if not got: continue
        if got.get("baseline")!=want["baseline"] or got.get("candidate")!=want["candidate"]: errors.append("decision_drift:"+rid)
    b=weakenings(result,"baseline"); c=weakenings(result,"candidate")
    if b!=sorted(expected["baseline_semantic_weakening_rows"]): errors.append("baseline_weakening_set")
    if c!=sorted(expected["candidate_semantic_weakening_rows"]): errors.append("candidate_weakening_set")
    if any(r["candidate"].get("route")=="one_contact_negative" for r in rows): errors.append("negative_selected")
    decision="PASS_EFFECT_DIMENSION_CAPABILITY_NEGOTIATION_AUDITED_SCOPED" if not errors else "FAIL_ROUTE_CAPABILITY_AUDIT_REPAIR"
    return {"schema":"route-capability-audit-v2","pass":not errors,"decision":decision,"errors":errors,"baseline_semantic_weakening_rows":b,"candidate_semantic_weakening_rows":c,"rows":len(rows)}

def main():
    root=Path(sys.argv[1]).resolve() if len(sys.argv)>1 else Path(__file__).resolve().parent
    out=audit(root)
    if len(sys.argv)==1: (root/"audit-result.json").write_text(json.dumps(out,indent=2,sort_keys=True)+"\n")
    print(json.dumps(out,sort_keys=True)); raise SystemExit(0 if out["pass"] else 1)
if __name__=="__main__": main()
