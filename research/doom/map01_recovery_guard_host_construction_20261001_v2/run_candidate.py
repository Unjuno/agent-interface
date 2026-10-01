#!/usr/bin/env python3
"""One-shot, host-only predicate construction; no runtime or side effects."""
from __future__ import annotations
import argparse, base64, hashlib, json, types
from pathlib import Path

EXPECTED_BLOB = "f5caf71a743a563b7de046b82d44db7ebe49e829"
SOURCE_B64 = Path(__file__).with_name("frozen_source.b64")
EXPECTED_INPUTS = [
 {"case_id":"fresh_stable","source_health":97,"source_sequence":10,"typed":{"event":"typed_observation","sequence":11,"signals":{"health":{"status":"observed","value":97}}}},
 {"case_id":"stale_sequence","source_health":97,"source_sequence":10,"typed":{"event":"typed_observation","sequence":10,"signals":{"health":{"status":"observed","value":97}}}},
 {"case_id":"health_unavailable","source_health":97,"source_sequence":10,"typed":{"event":"typed_observation","sequence":11,"signals":{"health":{"status":"unavailable","value":None}}}},
 {"case_id":"health_loss","source_health":97,"source_sequence":10,"typed":{"event":"typed_observation","sequence":11,"signals":{"health":{"status":"observed","value":96}}}},
]

def git_blob_sha(data: bytes) -> str:
 return hashlib.sha1(b"blob "+str(len(data)).encode("ascii")+b"\\0"+data).hexdigest()

def main() -> int:
 ap=argparse.ArgumentParser(); ap.add_argument("--output",type=Path,required=True); ns=ap.parse_args()
 if ns.output.exists(): raise SystemExit("STOP_OUTPUT_COLLISION")
 try: source=base64.b64decode("".join(SOURCE_B64.read_text(encoding="ascii").split()),validate=True)
 except Exception as exc: raise SystemExit("STOP_FROZEN_SOURCE_BASE64:"+type(exc).__name__)
 digest=git_blob_sha(source)
 if digest!=EXPECTED_BLOB: raise SystemExit("STOP_FROZEN_SOURCE_MISMATCH")
 # Executing module definitions only after exact blob verification; __main__ is not entered.
 module=types.ModuleType("frozen_recovery_protocol")
 exec(compile(source,"<frozen-current-main-protocol>","exec"),module.__dict__)
 cases=[]
 for item in EXPECTED_INPUTS:
  failed,reason=module.recovery_guard_failed(item["source_health"],item["source_sequence"],item["typed"])
  cases.append({"case_id":item["case_id"],"input":item,"actual":{"failed":failed,"reason":reason}})
 steps=module.build_recovery_steps()
 stale_rejected=False
 try: module.recovery_valid_until_ns(2_000_000_000,3_100_000_000)
 except ValueError: stale_rejected=True
 payload={"schema":"map01-recovery-guard-host-construction-v2","allocation":"HOST-59-RECOVERY-GUARD-C-20261001-02","base_main":"0764c928f1a32a3c7f992f1b80cb62f774e2d7ed","source_blob_sha1":digest,"cases":cases,
  "construction":{"recovery_step_count":len(steps),"total_hold_ms":sum(x.get("duration_ms",0) for x in steps if x.get("op")=="hold"),
   "fresh_valid_until_ns":module.recovery_valid_until_ns(2_000_000_000,2_500_000_000),"stale_source_rejected":stale_rejected},
  "scope":"CPU-only pure predicate construction; not formal or live #59 T1"}
 ns.output.parent.mkdir(parents=True,exist_ok=True); ns.output.write_text(json.dumps(payload,sort_keys=True,separators=(",",":"))+"\\n",encoding="utf-8")
 print(json.dumps({"disposition":"PASS_HOST_GUARD_CONSTRUCTION","case_count":len(cases),"source_blob_sha1":digest,"output":str(ns.output)},sort_keys=True))
 return 0
if __name__=="__main__": raise SystemExit(main())
