"""Docker schema preflight over the shared-volume host-model IPC boundary."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time


def has_remote_schema_reference(value) -> bool:
    if isinstance(value, dict):
        for key in ("$ref", "$dynamicRef", "$recursiveRef"):
            if key in value and (not isinstance(value[key], str)
                                 or not value[key].startswith("#")):
                return True
        return any(has_remote_schema_reference(item) for item in value.values())
    if isinstance(value, list):
        return any(has_remote_schema_reference(item) for item in value)
    return False


def validate_model_response(events_path: Path, schema_path: Path) -> dict:
    """Require one completed assistant JSON message to satisfy the supplied schema."""
    try:
        events = [json.loads(line) for line in events_path.read_text(
            encoding="utf-8").splitlines() if line.strip()]
    except (OSError, UnicodeError, json.JSONDecodeError):
        return {"turns": 0, "messages": 0,
                "status": "STOP_MALFORMED_MODEL_RESPONSE"}
    turns = [event for event in events if event.get("type") == "turn.completed"]
    messages = [event["item"] for event in events
                if event.get("type") == "item.completed"
                and isinstance(event.get("item"), dict)
                and event["item"].get("type") == "agent_message"]
    result = {"turns": len(turns), "messages": len(messages)}
    if len(turns) != 1 or len(messages) != 1:
        return {**result, "status": "STOP_MALFORMED_MODEL_RESPONSE"}

    result["usage"] = turns[0].get("usage")
    response_text = messages[0].get("text")
    if not isinstance(response_text, str):
        return {**result, "status": "STOP_INVALID_JSON_OUTPUT"}
    response_bytes = response_text.encode("utf-8")
    result["response_sha256"] = hashlib.sha256(response_bytes).hexdigest()
    try:
        instance = json.loads(response_text)
    except (json.JSONDecodeError, UnicodeError):
        return {**result, "status": "STOP_INVALID_JSON_OUTPUT"}

    try:
        import jsonschema
    except ImportError:
        return {**result, "status": "STOP_SCHEMA_VALIDATOR_UNAVAILABLE"}

    try:
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
        if not isinstance(schema, dict):
            return {**result, "status": "STOP_INVALID_OUTPUT_SCHEMA"}
        if not isinstance(schema.get("$schema"), str):
            return {**result, "status": "STOP_SCHEMA_DIALECT_UNDECLARED"}
        if has_remote_schema_reference(schema):
            return {**result, "status": "STOP_REMOTE_SCHEMA_REFERENCE"}
        validator_class = jsonschema.validators.validator_for(schema)
        if validator_class.META_SCHEMA.get("$id") != schema["$schema"]:
            return {**result, "status": "STOP_UNSUPPORTED_SCHEMA_DIALECT"}
        validator_class.check_schema(schema)
    except (json.JSONDecodeError, OSError, UnicodeError,
            jsonschema.exceptions.SchemaError, KeyError, TypeError, ValueError):
        return {**result, "status": "STOP_INVALID_OUTPUT_SCHEMA"}

    try:
        from referencing.exceptions import Unresolvable
        error = next(iter(validator_class(schema).iter_errors(instance)), None)
    except (ValueError, TypeError, Unresolvable):
        return {**result, "status": "STOP_INVALID_OUTPUT_SCHEMA"}
    if error is not None:
        # ValidationError.message may embed the complete model output; retain
        # structural diagnostics only.
        return {**result, "status": "STOP_SCHEMA_OUTPUT_INVALID",
                "schema_keyword": str(error.validator),
                "instance_path": [str(part) for part in error.absolute_path]}
    return {**result, "status": "PASS", "schema_valid": True,
            "schema_dialect": schema.get("$schema")}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--runner", type=Path, required=True)
    parser.add_argument("--prompt", type=Path, required=True)
    parser.add_argument("--working", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--instructions", type=Path, required=True)
    parser.add_argument("--schema", type=Path, required=True)
    parser.add_argument("--ipc", type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    runner_output = args.output / "runner"
    env = dict(os.environ)
    env["HOST_MODEL_IPC_DIR"] = str(args.ipc.resolve())
    started = time.time_ns()
    command = [
        sys.executable, str(args.runner), "/usr/bin/node", "/usr/bin/true",
        str(args.prompt), str(args.working), str(runner_output), "handle", "-",
        str(args.instructions), str(args.schema),
    ]
    completed = subprocess.run(command, env=env, capture_output=True, text=True)
    report = {
        "schema": "docker_schema_preflight_receipt_v1",
        "status": "PASS" if completed.returncode == 0 else "STOP_RUNNER",
        "returncode": completed.returncode, "authority_granted": False,
        "boundary": "container-to-host-model-ipc", "started_ns": started,
        "stdout": completed.stdout[-2000:], "stderr": completed.stderr[-2000:],
    }
    process_path = runner_output / "process.json"
    events_path = runner_output / "events.jsonl"
    if completed.returncode == 0 and process_path.exists() and events_path.exists():
        report.update(validate_model_response(events_path, args.schema))
    elif completed.returncode == 0:
        report["status"] = "STOP_MISSING_RUNNER_RECEIPT"
    (args.output / "report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
