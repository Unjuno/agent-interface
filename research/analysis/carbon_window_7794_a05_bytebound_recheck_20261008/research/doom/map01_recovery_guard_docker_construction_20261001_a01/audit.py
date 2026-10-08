#!/usr/bin/env python3
"""Independent raw-only audit; does not import candidate or recovery protocol."""
from __future__ import annotations
import base64, copy, hashlib, json
from pathlib import Path
ALLOCATION="MAP01-RECOVERY-GUARD-DOCKER-CONSTRUCTION-20261001-01"
BASE="8bbf3211cb10e0606c4ca13d6fb15b55f3895ad5"
BLOB="f5caf71a743a563b7de046b82d44db7ebe49e829"
EXPECTED={
 "fresh_stable":({"source_health":97,"source_sequence":10,"typed":{"event":"typed_observation","sequence":11,"signals":{"health":{"status":"observed","value":97}}}},(False,None)),
 "stale_sequence":({"source_health":97,"source_sequence":10,"typed":{"event":"typed_observation","sequence":10,"signals":{"health":{"status":"observed","value":97}}}},(True,"non_fresh_sequence")),
 "health_unavailable":({"source_health":97,"source_sequence":10,"typed":{"event":"typed_observation","sequence":11,"signals":{"health":{"status":"unavailable","value":None}}}},(True,"health_unavailable")),
 "health_loss":({"source_health":97,"source_sequence":10,"typed":{"event":"typed_observation","sequence":11,"signals":{"health":{"status":"observed","value":96}}}},(True,"health_loss"))
}
def audit(raw,fixture,protocol_bytes,candidate_bytes):
 errors=[]
 if raw.get("schema")!="map01-recovery-guard-docker-raw-v1": errors.append("schema")
 if raw.get("allocation")!=ALLOCATION: errors.append("allocation")
 if raw.get("base_main")!=BASE: errors.append("base_main")
 if raw.get("fixture_sha256")!=hashlib.sha256(Path("/src/fixture.json").read_bytes()).hexdigest(): errors.append("fixture_hash")
 git_blob=hashlib.sha1(b"blob "+str(len(protocol_bytes)).encode("ascii")+b"\0"+protocol_bytes).hexdigest()
 if git_blob!=BLOB or raw.get("protocol_git_blob_sha1")!=BLOB: errors.append("protocol_blob")
 if raw.get("protocol_sha256")!=hashlib.sha256(protocol_bytes).hexdigest(): errors.append("protocol_hash")
 if raw.get("candidate_sha256")!=hashlib.sha256(candidate_bytes).hexdigest(): errors.append("candidate_hash")
 rows=raw.get("rows")
 if not isinstance(rows,list) or len(rows)!=len(EXPECTED): return errors+["row_cardinality"]
 by={}
 for row in rows:
  if not isinstance(row,dict) or row.get("case_id") in by: errors.append("duplicate_or_malformed_row")
  else: by[row["case_id"]]=row
 if set(by)!=set(EXPECTED): errors.append("case_set")
 for cid,(inp,decision) in EXPECTED.items():
  r=by.get(cid)
  if r is None: continue
  if r.get("input")!=inp: errors.append("input:"+cid)
  a=r.get("actual",{})
  if (a.get("failed"),a.get("reason"))!=decision: errors.append("decision:"+cid)
 c=raw.get("construction",{})
 if c.get("recovery_step_count")!=10: errors.append("recovery_step_count")
 if c.get("total_hold_ms")!=250: errors.append("total_hold_ms")
 if c.get("fresh_valid_until_ns")!=2_900_000_000: errors.append("fresh_deadline")
 if c.get("stale_source_rejected") is not True: errors.append("stale_source_rejected")
 if fixture.get("allocation")!=ALLOCATION or len(fixture.get("cases",[]))!=4: errors.append("frozen_fixture")
 return errors
def main():
 raw_path=Path("/input/raw.json"); out=Path("/out/audit.json")
 if out.exists(): raise SystemExit("STOP_AUDIT_OUTPUT_EXISTS")
 raw=json.loads(raw_path.read_text(encoding="utf-8"))
 fixture=json.loads(Path("/src/fixture.json").read_text(encoding="utf-8"))
 encoded=(Path("/src/protocol.b64").read_text(encoding="ascii"))
 protocol=base64.b64decode("".join(encoded.split()),validate=True)
 candidate=Path("/src/candidate.py").read_bytes()
 errors=audit(raw,fixture,protocol,candidate)
 mutations=[
  ("flip_decision",lambda x:x["rows"][0]["actual"].update(failed=True)),
  ("alter_input",lambda x:x["rows"][3]["input"].update(source_health=1)),
  ("remove_row",lambda x:x["rows"].pop()),
  ("duplicate_row",lambda x:x["rows"][3].update(case_id="fresh_stable")),
  ("protocol_hash",lambda x:x.update(protocol_sha256="0"*64)),
 ]
 controls=[]
 for name,mutate in mutations:
  changed=copy.deepcopy(raw);mutate(changed);controls.append({"name":name,"rejected":bool(audit(changed,fixture,protocol,candidate))})
 passed=not errors and all(x["rejected"] for x in controls)
 result={"schema":"map01-recovery-guard-docker-audit-v1",
  "disposition":"PASS_HOST_GUARD_CONSTRUCTION" if passed else "FAIL_INDEPENDENT_AUDIT",
  "errors":errors,"rows":len(raw.get("rows",[])),"mutation_controls":controls,
  "mutation_rejections":sum(x["rejected"] for x in controls),
  "raw_sha256":hashlib.sha256(raw_path.read_bytes()).hexdigest(),
  "protocol_git_blob_sha1":hashlib.sha1(b"blob "+str(len(protocol)).encode("ascii")+b"\0"+protocol).hexdigest()}
 out.write_text(json.dumps(result,sort_keys=True,indent=2)+"\n",encoding="utf-8")
 print(json.dumps({"disposition":result["disposition"],"errors":errors,
  "mutation_rejections":result["mutation_rejections"]},sort_keys=True))
 return 0 if passed else 1
if __name__=="__main__": raise SystemExit(main())
