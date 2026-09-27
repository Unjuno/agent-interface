#!/usr/bin/env python3
import hashlib,json
from pathlib import Path
EXP={"scale-native":("SELECTED","native_fixed80"),"scale-wheel":("SELECTED","ctrl_wheel"),"scale-prefer-native":("SELECTED","native_fixed80"),"center-fallback-wheel":("SELECTED","ctrl_wheel"),"center-native-only":("UNSUPPORTED",None),"center-wheel-only":("SELECTED","ctrl_wheel"),"scale-negative-first":("SELECTED","ctrl_wheel"),"center-insufficient-only":("UNSUPPORTED",None),"unknown-dimension":("INVALID_REQUEST",None),"missing-provenance":("UNSUPPORTED_PROVENANCE",None)}
def blob(b): return hashlib.sha1(b"blob "+str(len(b)).encode()+b"\0"+b).hexdigest()
root=Path(__file__).resolve().parent; errors=[]
ids={"scale-audit.json":"389fe8cd93603c0415480fc398664a903dede0f4","center-summary.json":"28bc4a8c07958db58efe98eb73881cbced46c481"}
for n,h in ids.items():
 if blob((root/"evidence"/n).read_bytes())!=h: errors.append("evidence:"+n)
s=json.loads((root/"evidence/scale-audit.json").read_text()); c=json.loads((root/"evidence/center-summary.json").read_text()); cs=c["route_stats"]["ctrl_wheel"]; ns=c["route_stats"]["native_fixed80"]
if not s.get("pass") or cs["full_contract_matches"]!=cs["n"] or ns["scale_matches"]!=ns["n"] or ns["full_contract_matches"]!=0: errors.append("retained_semantics")
if any(0.45<=x<=0.55 for x in s["route_ratios"]["one_contact_negative"]): errors.append("negative_control")
r=json.loads((root/"formal-result.json").read_text()); rows={x["request_id"]:x for x in r["rows"]}
if r.get("formal_invocations")!=1 or len(rows)!=10: errors.append("allocation_shape")
for k,v in EXP.items():
 got=rows.get(k,{}).get("candidate",{});
 if (got.get("status"),got.get("route"))!=v: errors.append("candidate:"+k)
 if got.get("status")=="SELECTED" and not set(rows[k]["required_dimensions"])<=set(r["catalog"][got["route"]]["dims"]): errors.append("semantic_weakening:"+k)
false_flat=sum(rows[k]["baseline"]=={"status":"SELECTED","route":"native_fixed80"} for k in ["center-fallback-wheel","center-native-only"])
if false_flat!=2: errors.append("baseline_discriminator")
if any(x["candidate"].get("route")=="one_contact_negative" for x in rows.values()): errors.append("negative_selected")
out={"schema":"route-capability-audit-v1","pass":not errors,"decision":"PASS_EFFECT_DIMENSION_CAPABILITY_NEGOTIATION_SCOPED" if not errors else "FAIL_EFFECT_DIMENSION_CAPABILITY_NEGOTIATION","errors":errors,"candidate_rows":len(rows),"baseline_false_admissions":false_flat}; (root/"audit-result.json").write_text(json.dumps(out,indent=2,sort_keys=True)+"\n"); print(json.dumps(out,sort_keys=True)); raise SystemExit(0 if out["pass"] else 1)
