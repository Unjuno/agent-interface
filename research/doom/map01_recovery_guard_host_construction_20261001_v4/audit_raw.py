#!/usr/bin/env python3
"""Independent raw-only audit; no import of the candidate protocol."""
from __future__ import annotations
import base64, copy, hashlib, json
from pathlib import Path
EXPECTED_BLOB="f5caf71a743a563b7de046b82d44db7ebe49e829"
EXPECTED_BASE="686ae6c94dd67e78bab9920457085dc6ad1ced19"
EXPECTED=[
 {"case_id":"fresh_stable","source_health":97,"source_sequence":10,"typed":{"event":"typed_observation","sequence":11,"signals":{"health":{"status":"observed","value":97}}}},
 {"case_id":"stale_sequence","source_health":97,"source_sequence":10,"typed":{"event":"typed_observation","sequence":10,"signals":{"health":{"status":"observed","value":97}}}},
 {"case_id":"health_unavailable","source_health":97,"source_sequence":10,"typed":{"event":"typed_observation","sequence":11,"signals":{"health":{"status":"unavailable","value":None}}}},
 {"case_id":"health_loss","source_health":97,"source_sequence":10,"typed":{"event":"typed_observation","sequence":11,"signals":{"health":{"status":"observed","value":96}}}},
]
DECISIONS={"fresh_stable":(False,None),"stale_sequence":(True,"non_fresh_sequence"),"health_unavailable":(True,"health_unavailable"),"health_loss":(True,"health_loss")}
def git_blob(data):
 return hashlib.sha1(b"blob "+str(len(data)).encode("ascii")+bytes([0])+data).hexdigest()
def audit(raw):
 e=[]
 if raw.get("schema")!="map01-recovery-guard-host-construction-v4":e.append("schema")
 if raw.get("allocation")!="HOST-59-RECOVERY-GUARD-C-20261001-04":e.append("allocation")
 if raw.get("base_main")!=EXPECTED_BASE:e.append("base")
 if raw.get("source_blob_sha1")!=EXPECTED_BLOB:e.append("source_blob")
 rows=raw.get("cases")
 if not isinstance(rows,list) or len(rows)!=4:return e+["cardinality"]
 by={}
 for row in rows:
  if isinstance(row,dict) and row.get("case_id") not in by:by[row.get("case_id")]=row
  else:e.append("duplicate_or_malformed_case")
 expected_by={x["case_id"]:x for x in EXPECTED}
 if set(by)!=set(expected_by):e.append("case_set")
 for cid,spec in expected_by.items():
  row=by.get(cid)
  if row is None:continue
  if row.get("input")!=spec:e.append("frozen_input:"+cid);continue
  typed=spec["typed"];seq=typed.get("sequence")
  if type(seq) is not int or seq<=spec["source_sequence"]:decision=(True,"non_fresh_sequence")
  else:
   h=typed.get("signals",{}).get("health",{})
   if not isinstance(h,dict) or h.get("status")!="observed" or type(h.get("value")) is not int or h.get("value")<0:decision=(True,"health_unavailable")
   elif h["value"]<spec["source_health"]:decision=(True,"health_loss")
   else:decision=(False,None)
  actual=row.get("actual",{})
  if (actual.get("failed"),actual.get("reason"))!=decision:e.append("decision:"+cid)
  if decision!=DECISIONS[cid]:e.append("fixture_oracle:"+cid)
 c=raw.get("construction",{})
 if c.get("recovery_step_count")!=10:e.append("recovery_step_count")
 if c.get("total_hold_ms")!=250:e.append("total_hold_ms")
 if c.get("fresh_valid_until_ns")!=2_900_000_000:e.append("fresh_deadline")
 if c.get("stale_source_rejected") is not True:e.append("stale_source")
 return e
def main():
 here=Path(__file__).parent;raw_path=here/"evidence"/"candidate.json";out=here/"evidence"/"audit.json"
 if out.exists():raise SystemExit("STOP_AUDIT_OUTPUT_COLLISION")
 raw_bytes=raw_path.read_bytes();raw=json.loads(raw_bytes);errs=audit(raw)
 source=base64.b64decode("".join((here/"frozen_source.b64").read_text(encoding="ascii").split()),validate=True)
 if git_blob(source)!=EXPECTED_BLOB:errs.append("frozen_source_bytes")
 mutations=[
  ("flip_decision",lambda x:x["cases"][0]["actual"].update(failed=True)),
  ("alter_input",lambda x:x["cases"][3]["input"]["typed"]["signals"]["health"].update(value=99)),
  ("remove_case",lambda x:x["cases"].pop()),
  ("duplicate_case",lambda x:x["cases"][3].update(case_id="fresh_stable")),
  ("source_hash",lambda x:x.update(source_blob_sha1="0"*40))]
 controls=[]
 for name,mutate in mutations:
  changed=copy.deepcopy(raw);mutate(changed);controls.append({"name":name,"rejected":bool(audit(changed))})
 passed=not errs and all(x["rejected"] for x in controls)
 result={"schema":"map01-recovery-guard-host-audit-v4","disposition":"PASS_HOST_RAW_AUDIT" if passed else "FAIL_HOST_RAW_AUDIT",
  "errors":errs,"case_count":len(raw.get("cases",[])),"mutation_controls":controls,
  "mutation_rejections":sum(x["rejected"] for x in controls),"source_blob_sha1":git_blob(source),
  "raw_sha256":hashlib.sha256(raw_bytes).hexdigest(),"scope":"independent raw-only audit; no candidate protocol import"}
 out.write_text(json.dumps(result,sort_keys=True,indent=2)+"\n",encoding="utf-8")
 print(json.dumps({"disposition":result["disposition"],"errors":errs,"mutation_rejections":result["mutation_rejections"]},sort_keys=True))
 return 0 if passed else 1
if __name__=="__main__":raise SystemExit(main())
