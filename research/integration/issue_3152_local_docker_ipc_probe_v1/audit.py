#!/usr/bin/env python3
"""Reconcile the retained host-CLI JSONL probe and scope fields."""
import hashlib, json, sys
from pathlib import Path

result=json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
transcript=Path(sys.argv[2]).read_bytes()
errors=[]
if result.get("schema") != "issue3152-local-docker-ipc-probe-v1": errors.append("schema")
if result.get("formal_allocation_count") != 0 or result.get("prospective_freeze") is not False: errors.append("formal scope")
probe=result.get("ipc_probe", {})
normalized=transcript.replace(b"\r\n", b"\n")
if hashlib.sha256(normalized).hexdigest() != probe.get("protocol_transcript_sha256"): errors.append("LF-normalized transcript sha256")
try:
    events=[json.loads(line) for line in normalized.decode("utf-8").splitlines() if line]
except Exception as exc:
    events=[]; errors.append("transcript JSONL: "+type(exc).__name__)
threads=[e for e in events if e.get("type")=="thread.started"]
messages=[e for e in events if e.get("type")=="item.completed" and e.get("item",{}).get("type")=="agent_message"]
turns=[e for e in events if e.get("type")=="turn.completed"]
if len(threads)!=1 or len(messages)!=1 or len(turns)!=1: errors.append("expected exactly one thread/message/completed turn")
if len(messages)==1:
    try: answer=json.loads(messages[0]["item"]["text"])
    except Exception: answer=None
    if answer != probe.get("schema_response"): errors.append("schema response mismatch")
if len(turns)==1:
    usage=turns[0].get("usage",{})
    if usage.get("input_tokens") != probe.get("usage",{}).get("input_tokens"): errors.append("input tokens")
    if usage.get("output_tokens") != probe.get("usage",{}).get("output_tokens"): errors.append("output tokens")
    if usage.get("input_tokens",0)+usage.get("output_tokens",0) != probe.get("usage",{}).get("total_tokens"): errors.append("usage total")
docker=result.get("docker",{})
if not (docker.get("test_count")==18 and docker.get("passed")==18 and docker.get("failed")==0 and docker.get("network")=="none"): errors.append("Docker test scope/count")
print(json.dumps({"audit":"PASS_RETAINED_IPC_TRANSCRIPT" if not errors else "HOLD_RETAINED_IPC_TRANSCRIPT","errors":errors,"transcript_reparsed":True,"model_call_replayed":False,"docker_tests_reexecuted":False,"formal_acceptance":False},indent=2,sort_keys=True))
raise SystemExit(0 if not errors else 2)
