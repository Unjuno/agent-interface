#!/usr/bin/env python3
"""One-shot CPU-only construction check of frozen recovery-guard predicates."""
from __future__ import annotations
import base64, hashlib, json, sys, types
from pathlib import Path
EXPECTED_BLOB="f5caf71a743a563b7de046b82d44db7ebe49e829"
EXPECTED_CASES=[
 {"case_id":"fresh_stable","source_health":97,"source_sequence":10,"typed":{"event":"typed_observation","sequence":11,"signals":{"health":{"status":"observed","value":97}}}},
 {"case_id":"stale_sequence","source_health":97,"source_sequence":10,"typed":{"event":"typed_observation","sequence":10,"signals":{"health":{"status":"observed","value":97}}}},
 {"case_id":"health_unavailable","source_health":97,"source_sequence":10,"typed":{"event":"typed_observation","sequence":11,"signals":{"health":{"status":"unavailable","value":None}}}},
 {"case_id":"health_loss","source_health":97,"source_sequence":10,"typed":{"event":"typed_observation","sequence":11,"signals":{"health":{"status":"observed","value":96}}}},
]
def git_blob(data):
 return hashlib.sha1(b"blob "+str(len(data)).encode("ascii")+bytes([0])+data).hexdigest()
def main():
 source_path=Path(__file__).with_name("frozen_source.b64")
 out=Path(__file__).with_name("evidence")/"candidate.json"
 if out.exists(): raise SystemExit("STOP_OUTPUT_COLLISION")
 source=base64.b64decode("".join(source_path.read_text(encoding="ascii").split()),validate=True)
 digest=git_blob(source)
 if digest!=EXPECTED_BLOB: raise SystemExit("STOP_FROZEN_SOURCE_MISMATCH")
 module=types.ModuleType("frozen_current_main_recovery_protocol");sys.modules[module.__name__]=module
 exec(compile(source,"<frozen-current-main-protocol>","exec"),module.__dict__)
 cases=[]
 for item in EXPECTED_CASES:
  failed,reason=module.recovery_guard_failed(item["source_health"],item["source_sequence"],item["typed"])
  cases.append({"case_id":item["case_id"],"input":item,"actual":{"failed":failed,"reason":reason}})
 steps=module.build_recovery_steps();stale_rejected=False
 try: module.recovery_valid_until_ns(2_000_000_000,3_100_000_000)
 except ValueError: stale_rejected=True
 payload={"schema":"map01-recovery-guard-host-construction-v3","allocation":"HOST-59-RECOVERY-GUARD-C-20261001-03","base_main":"32cac82ec1f5b6e79035d8022a125b785218c897",
  "source_blob_sha1":digest,"cases":cases,
  "construction":{"recovery_step_count":len(steps),"total_hold_ms":sum(s.get("duration_ms",0) for s in steps if s.get("op")=="hold"),
   "fresh_valid_until_ns":module.recovery_valid_until_ns(2_000_000_000,2_500_000_000),"stale_source_rejected":stale_rejected},
  "scope":"host-only predicate construction; not formal or live #59 T1"}
 out.parent.mkdir(parents=True,exist_ok=True)
 out.write_text(json.dumps(payload,sort_keys=True,separators=(",",":"))+"\\n",encoding="utf-8")
 print(json.dumps({"disposition":"PASS_HOST_GUARD_CONSTRUCTION","case_count":len(cases),"source_blob_sha1":digest},sort_keys=True))
 return 0
if __name__=="__main__": raise SystemExit(main())
