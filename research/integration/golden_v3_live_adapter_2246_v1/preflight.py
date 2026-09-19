#!/usr/bin/env python3
import hashlib, json, os
from pathlib import Path

ROOT=Path(__file__).resolve().parents[3]
EXPECTED={
 "runtime/golden_desktop_demo_v3.py":"26db03b8400b03fbe5272bd4ae5ad9c3a82d31a2",
 "runtime/cli_v1/api.py":"5674bd39e3cb2170095f476dac90e2a781f4f77a",
 "runtime/results/golden-desktop-app-server-v3-live-01/golden-report.json":"e168a9bdc84fc6b807f4e90806ec7c501da89689",
}
def blob_sha(data):
    return hashlib.sha1(b"blob %d\0"%len(data)+data).hexdigest()
checks={}
for rel,want in EXPECTED.items():
    p=ROOT/rel
    checks[rel]={"exists":p.is_file(),"blob_sha":blob_sha(p.read_bytes()) if p.is_file() else None,"expected":want}
source_ok=all(v["exists"] and v["blob_sha"]==v["expected"] for v in checks.values())
authority=os.environ.get("AGENT_INTERFACE_LIVE_AUTHORITY","").strip().lower() in {"1","true","yes"}
if not source_ok:
    status="STOP_SOURCE_IDENTITY_GAP"
elif not authority:
    status="HOLD_NO_MODEL_AUTHORITY"
else:
    status="READY_FOR_SEPARATE_LIVE_ALLOCATION"
result={"schema":"golden_v3_live_adapter_preflight_v1","status":status,
        "source_checks":checks,"authority_declared":authority,
        "model_calls":0,"gui_calls":0,"input_events":0,"network_task_calls":0,
        "scope":"preflight only; no live allocation"}
print(json.dumps(result,sort_keys=True,indent=2))
raise SystemExit(0 if status in {"HOLD_NO_MODEL_AUTHORITY","READY_FOR_SEPARATE_LIVE_ALLOCATION"} else 1)
