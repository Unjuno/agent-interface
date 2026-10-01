#!/usr/bin/env python3
"""Raw-only independent decision reconstruction; does not import the protocol."""
from __future__ import annotations
import argparse, base64, copy, hashlib, json
from pathlib import Path

EXPECTED_BLOB="f5caf71a743a563b7de046b82d44db7ebe49e829"
EXPECTED_INPUTS=[
 {"case_id":"fresh_stable","source_health":97,"source_sequence":10,"typed":{"event":"typed_observation","sequence":11,"signals":{"health":{"status":"observed","value":97}}}},
 {"case_id":"stale_sequence","source_health":97,"source_sequence":10,"typed":{"event":"typed_observation","sequence":10,"signals":{"health":{"status":"observed","value":97}}}},
 {"case_id":"health_unavailable","source_health":97,"source_sequence":10,"typed":{"event":"typed_observation","sequence":11,"signals":{"health":{"status":"unavailable","value":None}}}},
 {"case_id":"health_loss","source_health":97,"source_sequence":10,"typed":{"event":"typed_observation","sequence":11,"signals":{"health":{"status":"observed","value":96}}}},
]
EXPECTED={"fresh_stable":(False,None),"stale_sequence":(True,"non_fresh_sequence"),"health_unavailable":(True,"health_unavailable"),"health_loss":(True,"health_loss")}

def blob(data:bytes)->str: return hashlib.sha1(b"blob "+str(len(data)).encode("ascii")+b"\\0"+data).hexdigest()

def audit(raw:dict)->list[str]:
 e=[]
 if raw.get("schema")!="map01-recovery-guard-host-construction-v2": e.append("schema")
 if raw.get("allocation")!="HOST-59-RECOVERY-GUARD-C-20261001-02": e.append("allocation")
 if raw.get("base_main")!="0764c928f1a32a3c7f992f1b80cb62f774e2d7ed": e.append("base_main")
 if raw.get("source_blob_sha1")!=EXPECTED_BLOB: e.append("source_blob")
 rows=raw.get("cases")
 if not isinstance(rows,list) or len(rows)!=4: return e+["case_cardinality"]
 by={x.get("case_id"):x for x in rows if isinstance(x,dict)}
 if set(by)!=set(EXPECTED): e.append("case_ids")
 for expected_input in EXPECTED_INPUTS:
  cid=expected_input["case_id"]; row=by.get(cid)
  if row is None: continue
  if row.get("input")!=expected_input: e.append("frozen_input:"+cid); continue
  inp=expected_input; typed=inp["typed"]; seq=typed.get("sequence")
  if type(seq) is not int or seq<=inp["source_sequence"]: expected=(True,"non_fresh_sequence")
  else:
   h=typed.get("signals",{}).get("health",{})
   if not isinstance(h,dict) or h.get("status")!="observed" or type(h.get("value")) is not int or h.get("value")<0: expected=(True,"health_unavailable")
   elif h["value"]<inp["source_health"]: expected=(True,"health_loss")
   else: expected=(False,None)
  actual=row.get("actual",{})
  if (actual.get("failed"),actual.get("reason"))!=expected: e.append("decision:"+cid)
  if expected!=EXPECTED[cid]: e.append("oracle_fixture:"+cid)
 c=raw.get("construction",{})
 if c.get("recovery_step_count")!=10: e.append("step_count")
 if c.get("total_hold_ms")!=250: e.append("hold_ms")
 if c.get("fresh_valid_until_ns")!=2_900_000_000: e.append("fresh_deadline")
 if c.get("stale_source_rejected") is not True: e.append("stale_source")
 return e

def main()->int:
 ap=argparse.ArgumentParser();ap.add_argument("raw",type=Path);ap.add_argument("--output",type=Path,required=True);ns=ap.parse_args()
 if ns.output.exists(): raise SystemExit("STOP_AUDIT_OUTPUT_COLLISION")
 raw_bytes=ns.raw.read_bytes();raw=json.loads(raw_bytes);base_errors=audit(raw)
 source=base64.b64decode("".join(Path(__file__).with_name("frozen_source.b64").read_text(encoding="ascii").split()),validate=True)
 source_ok=blob(source)==EXPECTED_BLOB
 mutations=[
  ("flip_decision",lambda x:x["cases"][0]["actual"].update(failed=True)),
  ("alter_input",lambda x:x["cases"][3]["input"]["typed"]["signals"]["health"].update(value=99)),
  ("remove_case",lambda x:x["cases"].pop()),
  ("duplicate_case",lambda x:x["cases"][3].update(case_id="fresh_stable")),
  ("source_digest",lambda x:x.update(source_blob_sha1="0"*40))]
 controls=[]
 for name,mut in mutations:
  changed=copy.deepcopy(raw);mut(changed);controls.append({"name":name,"rejected":bool(audit(changed))})
 if not source_ok: base_errors.append("frozen_source_bytes")
 passed=not base_errors and all(x["rejected"] for x in controls)
 result={"schema":"map01-recovery-guard-host-audit-v2","disposition":"PASS_HOST_RAW_AUDIT" if passed else "FAIL_HOST_RAW_AUDIT",
  "errors":base_errors,"case_count":len(raw.get("cases",[])),"mutation_controls":controls,"mutation_rejections":sum(x["rejected"] for x in controls),
  "source_blob_sha1":blob(source),"raw_sha256":hashlib.sha256(raw_bytes).hexdigest(),"scope":"independent raw-only audit; no candidate protocol import"}
 ns.output.write_text(json.dumps(result,sort_keys=True,indent=2)+"\\n",encoding="utf-8")
 print(json.dumps({"disposition":result["disposition"],"errors":base_errors,"mutation_rejections":result["mutation_rejections"]},sort_keys=True))
 return 0 if passed else 1
if __name__=="__main__": raise SystemExit(main())
