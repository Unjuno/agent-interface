#!/usr/bin/env python3
"""Offline, independent audit of the one returned #2849 model response."""
import argparse
import json
from pathlib import Path
import subprocess


AUDIT_IMAGE = "sha256:5cc4d237e6af4548147ddfffc35413faf2487fd585f6a0216221f153f61cf073"

AUDIT = r'''import hashlib, json, sys
from pathlib import Path
from jsonschema import Draft202012Validator
events_path, schema_path, request_path, broker_path, client_path, stderr_path = map(Path, sys.argv[1:])
rows = [json.loads(line) for line in events_path.read_text(encoding="utf-8").splitlines() if line.strip()]
schema = json.loads(schema_path.read_text(encoding="utf-8"))
request = json.loads(request_path.read_text(encoding="utf-8"))
broker = json.loads(broker_path.read_text(encoding="utf-8"))
client = json.loads(client_path.read_text(encoding="utf-8"))
stderr = stderr_path.read_text(encoding="utf-8")
turns = [r for r in rows if r.get("type") == "turn.completed"]
completed = [r.get("item", {}) for r in rows if r.get("type") == "item.completed"]
messages = [x for x in completed if x.get("type") == "agent_message"]
errors = [x for x in completed if x.get("type") == "error"]
output = None
json_error = None
if len(messages) == 1:
    try: output = json.loads(messages[0].get("text", ""))
    except (json.JSONDecodeError, TypeError) as exc: json_error = type(exc).__name__
schema_valid = isinstance(output, dict) and not list(Draft202012Validator(schema).iter_errors(output))
checks = {
  "one_ipc_handle_no_image_request": request.get("mode") == "handle" and request.get("image") is None and request.get("authority_granted") is False,
  "one_host_cli_invocation_returned_zero": broker.get("host_cli_invoked") is True and broker.get("host_cli_spawn_attempted") is True and broker.get("returncode") == 0 and broker.get("authority_granted") is False,
  "one_completed_turn_has_usage": len(turns) == 1 and isinstance(turns[0].get("usage"), dict) and turns[0]["usage"].get("output_tokens", 0) > 0,
  "exactly_one_assistant_json_message": len(messages) == 1 and isinstance(output, dict),
  "assistant_json_satisfies_schema": schema_valid,
  "container_runner_failed_on_completed_item_count": client.get("returncode") == 1 and "not one completed turn/message" in stderr and len(completed) == 2 and len(errors) == 1,
}
print(json.dumps({"audit_status": "PASS_FAILURE_REPRODUCED" if all(checks.values()) else "AUDIT_INCOMPLETE", "checks": checks, "event_types": [r.get("type") for r in rows], "completed_item_types": [x.get("type") for x in completed], "usage": turns[0].get("usage") if len(turns) == 1 else None, "assistant_json_sha256": hashlib.sha256(messages[0].get("text", "").encode()).hexdigest() if len(messages) == 1 else None, "schema_dialect": schema.get("$schema"), "schema_errors": 0 if schema_valid else None, "request_id": request.get("request_id"), "host_cli_version": (broker.get("host_cli_identity") or {}).get("version"), "runner_process_receipt_present": False, "message_parse_error": json_error}, sort_keys=True))
'''


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--attempt", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    a = p.parse_args()
    root = a.attempt.resolve()
    ipc = root / "ipc"
    repo = root / "repo"
    events = repo / "preflight-result/model-call/events.jsonl"
    schema = repo / "schema.json"
    client = repo / "preflight-result/preflight-client-result.json"
    stderr = root / "container.stderr.txt"
    requests = list(ipc.glob("*.request.json"))
    brokers = list(ipc.glob("*.broker.json"))
    if len(requests) != 1 or len(brokers) != 1:
        raise RuntimeError("expected exactly one raw request and broker receipt")
    cmd = ["docker", "--context", "orbstack", "run", "--rm", "--network", "none", "--read-only",
           "--mount", f"type=bind,src={events},dst=/events.jsonl,readonly",
           "--mount", f"type=bind,src={schema},dst=/schema.json,readonly",
           "--mount", f"type=bind,src={requests[0]},dst=/request.json,readonly",
           "--mount", f"type=bind,src={brokers[0]},dst=/broker.json,readonly",
           "--mount", f"type=bind,src={client},dst=/client.json,readonly",
           "--mount", f"type=bind,src={stderr},dst=/container.stderr.txt,readonly",
           "--entrypoint", "python", AUDIT_IMAGE, "-c", AUDIT,
           "/events.jsonl", "/schema.json", "/request.json", "/broker.json", "/client.json", "/container.stderr.txt"]
    done = subprocess.run(cmd, capture_output=True, text=True, check=False, timeout=30)
    a.output.parent.mkdir(parents=True, exist_ok=True)
    a.output.write_text(json.dumps({"command": cmd, "returncode": done.returncode,
                                    "stdout": done.stdout, "stderr": done.stderr}, indent=2) + "\n",
                        encoding="utf-8")
    print(done.stdout, end="")
    return done.returncode


if __name__ == "__main__":
    raise SystemExit(main())
