#!/usr/bin/env python3
"""One-shot local-Docker invocation of the frozen #59 guard predicate."""
from __future__ import annotations
import base64, hashlib, importlib.util, json, sys, types
from pathlib import Path

HERE=Path(__file__).resolve().parent
EXPECTED_GIT_BLOB="f5caf71a743a563b7de046b82d44db7ebe49e829"
ALLOCATION="MAP01-RECOVERY-GUARD-DOCKER-CONSTRUCTION-20261001-01"

def git_blob(data: bytes) -> str:
    return hashlib.sha1(b"blob "+str(len(data)).encode("ascii")+b"\0"+data).hexdigest()

def main() -> int:
    encoded=(HERE/"protocol.b64").read_text(encoding="ascii")
    source=base64.b64decode("".join(encoded.split()),validate=True)
    fixture_path=HERE/"fixture.json"; out=Path("/out/raw.json")
    if out.exists(): raise SystemExit("STOP_OUTPUT_EXISTS")
    blob=git_blob(source)
    if blob!=EXPECTED_GIT_BLOB: raise SystemExit("STOP_FROZEN_PROTOCOL_BLOB_MISMATCH")
    fx=json.loads(fixture_path.read_text(encoding="utf-8"))
    if fx.get("allocation")!=ALLOCATION: raise SystemExit("STOP_ALLOCATION_MISMATCH")
    name="frozen_recovery_protocol"
    module=types.ModuleType(name)
    module.__file__=str(HERE/"protocol.py")
    module.__package__=""
    sys.modules[name]=module
    exec(compile(source,module.__file__,"exec"),module.__dict__)
    rows=[]
    for c in fx["cases"]:
        failed,reason=module.recovery_guard_failed(c["source_health"],c["source_sequence"],c["typed"])
        rows.append({"case_id":c["case_id"],"input":{k:c[k] for k in ("source_health","source_sequence","typed")},
                     "actual":{"failed":failed,"reason":reason}})
    steps=module.build_recovery_steps()
    fresh_deadline=module.recovery_valid_until_ns(2_000_000_000,2_500_000_000)
    stale_rejected=False
    try: module.recovery_valid_until_ns(2_000_000_000,3_100_000_000)
    except ValueError: stale_rejected=True
    raw={"schema":"map01-recovery-guard-docker-raw-v1","allocation":ALLOCATION,
         "base_main":"8bbf3211cb10e0606c4ca13d6fb15b55f3895ad5",
         "fixture_sha256":hashlib.sha256(fixture_path.read_bytes()).hexdigest(),
         "protocol_git_blob_sha1":blob,"protocol_sha256":hashlib.sha256(source).hexdigest(),
         "candidate_sha256":hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
         "rows":rows,"construction":{"recovery_step_count":len(steps),
           "total_hold_ms":sum(s.get("duration_ms",0) for s in steps if s.get("op")=="hold"),
           "fresh_valid_until_ns":fresh_deadline,"stale_source_rejected":stale_rejected},
         "scope":"predicate-only construction; no MAP01/live T1 claim"}
    out.write_text(json.dumps(raw,sort_keys=True,separators=(",",":"))+"\n",encoding="utf-8")
    print(json.dumps({"status":"CANDIDATE_COMPLETE","case_count":len(rows),
      "protocol_git_blob_sha1":blob,"raw_bytes":out.stat().st_size},sort_keys=True))
    return 0

if __name__=="__main__": raise SystemExit(main())
