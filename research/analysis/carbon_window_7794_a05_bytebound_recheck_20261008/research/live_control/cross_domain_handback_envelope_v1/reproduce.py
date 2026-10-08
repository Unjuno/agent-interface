#!/usr/bin/env python3
"""Re-audit the retained #1530 cross-domain representation result."""
import hashlib, json
from pathlib import Path
R=Path(__file__).parent
src=json.loads((R/"retained_sources.json").read_text())
res=json.loads((R/"RESULT.json").read_text())
errors=[]
expected={
 "x11_summary":"458ba631c0d5ba58332bc5c432db42a497061169",
 "x11_schema":"429e790f08ea4f083dec9ab61a5a282e0f2b45ed",
 "map01_feedback":"bfdcd8c299a7dbe759977b346737bf592e3f4772",
 "map01_tempo":"62abb1b07bd70edfa83354e6e864b2481d6f9d3a",
 "map01_release":"f077c1bd576af8f3e83c6d394669361f597b6e5c"}
for k,v in expected.items():
 if src["source_blobs"].get(k,{}).get("git_blob")!=v: errors.append("source:"+k)
rows=res["rows"]
for i,r in enumerate(rows):
 if r.get("input_authority") is not False or r.get("semantic_authority") is not False: errors.append(f"authority:{i}")
 if r["domain"]=="doom_map01" and r["variant"]=="OBSERVED_STATE_CHANGE":
  if (r.get("causal_to_action"),r.get("task_useful"),r.get("handoff_effect_status"))!=("UNVERIFIED","UNVERIFIED","UNRESOLVED"): errors.append(f"map01_state:{i}")
 if r["variant"]=="VERIFIED_PHYSICAL_RELEASE" and (r.get("task_useful")!="UNVERIFIED" or r.get("handoff_effect_status")!="UNRESOLVED"): errors.append(f"release:{i}")
 if r["domain"]=="x11_tk" and r["variant"]=="OBSERVED_CURRENT_EFFECT" and r.get("source_role")!="CURRENT_EFFECT": errors.append(f"x11_role:{i}")
if src["facts"]["map01"]["decision"]!="SCHEMA_INSUFFICIENT_FIRST_USEFUL_FEEDBACK": errors.append("map01_source_decision")
if res["decision"]!="PASS_REPRESENTATION_TRANSFER_CANDIDATE": errors.append("decision")
print(json.dumps({"pass":not errors,"errors":errors,"result_sha256":hashlib.sha256((R/"RESULT.json").read_bytes()).hexdigest()},sort_keys=True))
raise SystemExit(bool(errors))
