#!/usr/bin/env python3
import hashlib,json,sys
from pathlib import Path
EXPECTED_BLOB="28bc4a8c07958db58efe98eb73881cbced46c481"
def blob(b): return hashlib.sha1(b"blob "+str(len(b)).encode()+b"\0"+b).hexdigest()
def audit(root):
    errors=[]
    if blob((root/"evidence/center-summary.json").read_bytes())!=EXPECTED_BLOB: errors.append("evidence_identity")
    result=json.loads((root/"formal-result.json").read_text()); expected=json.loads((root/"expected.json").read_text())
    rows={x["case_id"]:x for x in result.get("rows",[])}
    if result.get("formal_invocations")!=1: errors.append("formal_count")
    if len(rows)!=7 or set(rows)!=set(expected["rows"]): errors.append("row_identity")
    for cid,want in expected["rows"].items():
        got=rows.get(cid,{})
        for arm in ("baseline","candidate"):
            actual=got.get(arm,{})
            if {"status":actual.get("status"),"route":actual.get("route")}!=want[arm]: errors.append(f"{arm}:{cid}")
            if actual.get("authority")!="none": errors.append(f"authority:{arm}:{cid}")
    for cid in ["session_changed","surface_changed","geometry_changed","all_changed"]:
        if rows.get(cid,{}).get("baseline",{}).get("status")!="SELECTED": errors.append("baseline_discriminator:"+cid)
        if rows.get(cid,{}).get("candidate",{}).get("status")!="STALE_CAPABILITY": errors.append("dependency_escape:"+cid)
    exact=rows.get("exact",{}).get("candidate",{})
    if exact.get("status")!="SELECTED" or exact.get("route")!="ctrl_wheel": errors.append("positive")
    if set(result.get("verified_dimensions",[]))!={"scale","center"}: errors.append("semantic_dimensions")
    decision="PASS_ROUTE_CAPABILITY_DEPENDENCY_BINDING_SCOPED" if not errors else "FAIL_ROUTE_CAPABILITY_DEPENDENCY_BINDING"
    return {"schema":"route-capability-dependency-audit-v1","pass":not errors,"decision":decision,"errors":errors,"rows":len(rows)}
def main():
    root=Path(sys.argv[1]).resolve() if len(sys.argv)>1 else Path(__file__).resolve().parent
    out=audit(root)
    if len(sys.argv)==1:(root/"audit-result.json").write_text(json.dumps(out,indent=2,sort_keys=True)+"\n")
    print(json.dumps(out,sort_keys=True)); raise SystemExit(0 if out["pass"] else 1)
if __name__=="__main__":main()
