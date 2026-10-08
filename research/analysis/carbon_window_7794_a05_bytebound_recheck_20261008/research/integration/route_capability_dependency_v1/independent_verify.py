#!/usr/bin/env python3
import json,sys
from pathlib import Path
root=Path(sys.argv[1]).resolve() if len(sys.argv)>1 else Path(__file__).resolve().parent
r=json.loads((root/"formal-result.json").read_text()); rows={x["case_id"]:x for x in r["rows"]}; errors=[]
if len(rows)!=7: errors.append("row_count")
positive=rows.get("exact",{}).get("candidate",{})
if (positive.get("status"),positive.get("route"))!=("SELECTED","ctrl_wheel"): errors.append("positive")
for cid in ("session_changed","surface_changed","geometry_changed","all_changed"):
    row=rows.get(cid,{})
    if row.get("baseline",{}).get("status")!="SELECTED": errors.append("baseline:"+cid)
    if row.get("candidate",{}).get("status")!="STALE_CAPABILITY" or row.get("candidate",{}).get("route") is not None: errors.append("candidate:"+cid)
if rows.get("geometry_missing",{}).get("candidate",{}).get("status")!="CURRENT_CONTEXT_INCOMPLETE": errors.append("missing")
if rows.get("malformed_provenance",{}).get("candidate",{}).get("status")!="UNSUPPORTED_PROVENANCE": errors.append("provenance")
for x in rows.values():
    if x["candidate"].get("status")=="SELECTED" and not set(x["required_dimensions"])<=set(r["verified_dimensions"]): errors.append("semantic_weakening:"+x["case_id"])
    if x["candidate"].get("authority")!="none" or x["baseline"].get("authority")!="none": errors.append("authority:"+x["case_id"])
out={"schema":"route-capability-dependency-independent-v1","pass":not errors,"decision":"PASS_INDEPENDENT_DEPENDENCY_BINDING" if not errors else "FAIL_INDEPENDENT_DEPENDENCY_BINDING","errors":errors}
if len(sys.argv)==1:(root/"independent-verifier.json").write_text(json.dumps(out,indent=2,sort_keys=True)+"\n")
print(json.dumps(out,sort_keys=True)); raise SystemExit(0 if out["pass"] else 1)
