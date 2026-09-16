#!/usr/bin/env python3
from __future__ import annotations
import hashlib,json
from pathlib import Path
EXPECT={
"scale-native":("SELECTED","native_fixed80"),"scale-wheel":("SELECTED","ctrl_wheel"),"scale-prefer-native":("SELECTED","native_fixed80"),
"center-fallback-wheel":("SELECTED","ctrl_wheel"),"center-native-only":("UNSUPPORTED",None),"center-wheel-only":("SELECTED","ctrl_wheel"),
"scale-negative-first":("SELECTED","ctrl_wheel"),"center-insufficient-only":("UNSUPPORTED",None),"unknown-dimension":("INVALID_REQUEST",None),
"missing-provenance":("UNSUPPORTED_PROVENANCE",None)}
BLOBS={"scale-audit.json":"389fe8cd93603c0415480fc398664a903dede0f4","center-summary.json":"28bc4a8c07958db58efe98eb73881cbced46c481"}

def blob(data): return hashlib.sha1(b"blob "+str(len(data)).encode()+b"\0"+data).hexdigest()
def audit(root):
    errors=[]
    for name,sha in BLOBS.items():
        data=(root/"evidence"/name).read_bytes()
        if blob(data)!=sha: errors.append("evidence_blob:"+name)
    s=json.loads((root/"evidence/scale-audit.json").read_text()); c=json.loads((root/"evidence/center-summary.json").read_text())
    if s.get("decision")!="PASS_INKSCAPE_ZOOM_MULTI_ROUTE_SCOPED" or not s.get("pass"): errors.append("scale_disposition")
    cs=c.get("route_stats",{}).get("ctrl_wheel",{}); ns=c.get("route_stats",{}).get("native_fixed80",{})
    if not (cs.get("n")==9 and cs.get("scale_matches")==9 and cs.get("full_contract_matches")==9): errors.append("ctrl_evidence")
    if not (ns.get("n")==9 and ns.get("scale_matches")==9 and ns.get("full_contract_matches")==0): errors.append("native_boundary")
    one=s.get("route_ratios",{}).get("one_contact_negative",[])
    if len(one)!=4 or any(0.45<=x<=0.55 for x in one): errors.append("negative_control_evidence")
    result=json.loads((root/"formal-result.json").read_text())
    if result.get("formal_invocations")!=1: errors.append("formal_invocation_count")
    rows=result.get("rows",[])
    if len(rows)!=10: errors.append("row_count")
    by={r.get("request_id"):r for r in rows}
    for rid,(status,route) in EXPECT.items():
        r=by.get(rid)
        if not r: errors.append("missing_row:"+rid); continue
        got=r.get("candidate",{})
        if (got.get("status"),got.get("route"))!=(status,route): errors.append("candidate:"+rid)
        if got.get("status")=="SELECTED":
            req=set(r.get("required_dimensions",[])); cap=set(result.get("catalog",{}).get(got.get("route"),{}).get("verified_dimensions",[]))
            if not req.issubset(cap): errors.append("semantic_weakening:"+rid)
    false_flat=0
    for rid in ("center-fallback-wheel","center-native-only"):
        r=by.get(rid,{}); b=r.get("baseline",{})
        if b.get("status")=="SELECTED" and b.get("route")=="native_fixed80": false_flat+=1
    if false_flat!=2: errors.append("baseline_discriminator")
    if any(r.get("candidate",{}).get("route")=="one_contact_negative" for r in rows): errors.append("negative_route_selected")
    decision="PASS_EFFECT_DIMENSION_CAPABILITY_NEGOTIATION_SCOPED" if not errors else "FAIL_EFFECT_DIMENSION_CAPABILITY_NEGOTIATION"
    return {"schema":"route-capability-audit-v1","pass":not errors,"decision":decision,"errors":errors,"candidate_rows":len(rows),"baseline_false_admissions":false_flat}

def main():
    root=Path(__file__).resolve().parent; out=audit(root); (root/"audit-result.json").write_text(json.dumps(out,indent=2,sort_keys=True)+"\n"); print(json.dumps(out,sort_keys=True)); raise SystemExit(0 if out["pass"] else 1)
if __name__=="__main__": main()
