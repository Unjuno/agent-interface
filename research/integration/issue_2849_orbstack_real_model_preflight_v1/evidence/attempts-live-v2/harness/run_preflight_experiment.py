#!/usr/bin/env python3
"""Run the frozen Issue #2849 real host-model/OrbStack preflight once per schema."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time


BASE_IMAGE = "python:3.12-slim@sha256:2f17fc044b579bab302c2e8054d3a686e2cb9a83de48e70534b94cd8ebbe06a9"
AUDIT_IMAGE = "issue2849-py312-pytest-jsonschema:v1"
AUDIT_IMAGE_ID = "sha256:5cc4d237e6af4548147ddfffc35413faf2487fd585f6a0216221f153f61cf073"
SCHEMAS = {
    "plain": "plain_form_points_schema_v1.json",
    "compiled": "compiled_form_grounding_schema_v1.json",
}
PROMPT = "Schema compatibility probe. Produce any object accepted by the supplied schema."


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def independently_audit(source: Path, events: Path, schema: Path,
                        process: Path, request: Path, broker: Path) -> dict:
    audit_code = r'''import json, sys
from pathlib import Path
sys.path.insert(0, "/src")
from runtime.docker_schema_preflight_v1 import validate_model_response
events_path, schema_path, process_path, request_path, broker_path = map(Path, sys.argv[1:])
rows = [json.loads(line) for line in events_path.read_text(encoding="utf-8").splitlines() if line.strip()]
messages = [r for r in rows if r.get("type") == "item.completed" and isinstance(r.get("item"), dict) and r["item"].get("type") == "agent_message"]
turns = [r for r in rows if r.get("type") == "turn.completed"]
failures = [r for r in rows if r.get("type") in ("error", "turn.failed")]
instance = None
message_error = None
if len(messages) == 1:
    item = messages[0]["item"]
    text = item.get("text")
    if isinstance(text, str):
        try: instance = json.loads(text)
        except json.JSONDecodeError as exc: message_error = type(exc).__name__
    else:
        message_error = "MISSING_AGENT_MESSAGE_TEXT"
schema_result = validate_model_response(events_path, schema_path)
process = json.loads(process_path.read_text(encoding="utf-8"))
request = json.loads(request_path.read_text(encoding="utf-8"))
broker = json.loads(broker_path.read_text(encoding="utf-8"))
checks = {
  "one_completed_agent_message": len(messages) == 1,
  "one_completed_turn_with_usage": len(turns) == 1 and turns[0].get("usage") is not None,
  "no_failure_events": len(failures) == 0,
  "agent_message_is_json_object": isinstance(instance, dict),
  "independent_schema_validator_pass": schema_result.get("status") == "PASS",
  "container_process_returned_without_authority": process.get("exit_code") == 0 and process.get("authority_granted") is False and process.get("boundary") == "container-to-host-model-ipc",
  "request_is_non_authoritative_no_image_handle": request.get("authority_granted") is False and request.get("mode") == "handle" and request.get("image") is None,
  "host_cli_invoked_once_and_returned_zero": broker.get("host_cli_invoked") is True and broker.get("host_cli_spawn_attempted") is True and broker.get("returncode") == 0 and broker.get("authority_granted") is False,
}
print(json.dumps({"checks": checks, "status": "PASS" if all(checks.values()) else "FAIL", "event_types": [r.get("type") for r in rows], "usage": turns[0].get("usage") if len(turns) == 1 else None, "schema_validation": schema_result, "host_cli_identity": broker.get("host_cli_identity"), "message_error": message_error}, sort_keys=True))
'''
    cmd = [
        "docker", "--context", "orbstack", "run", "--rm", "--network", "none",
        "--read-only", "--mount", f"type=bind,src={source},dst=/src,readonly",
        "--mount", f"type=bind,src={events},dst=/events.jsonl,readonly",
        "--mount", f"type=bind,src={schema},dst=/schema.json,readonly",
        "--mount", f"type=bind,src={process},dst=/process.json,readonly",
        "--mount", f"type=bind,src={request},dst=/request.json,readonly",
        "--mount", f"type=bind,src={broker},dst=/broker.json,readonly",
        "--entrypoint", "python", AUDIT_IMAGE_ID, "-c", audit_code,
        "/events.jsonl", "/schema.json", "/process.json", "/request.json", "/broker.json",
    ]
    completed = subprocess.run(cmd, capture_output=True, text=True, check=False, timeout=30)
    return {"command": cmd, "returncode": completed.returncode,
            "stdout": completed.stdout, "stderr": completed.stderr}


def attempt(name: str, source: Path, evidence: Path, broker_source: Path,
            container_runner: Path, schema_source: Path, instruction_source: Path,
            codex_exe: str) -> dict:
    root = evidence / name
    repo = root / "repo"
    ipc = root / "ipc"
    result_dir = repo / "preflight-result"
    workspace = repo / "workspace"
    for path in (repo, ipc, result_dir, workspace):
        path.mkdir(parents=True, exist_ok=False)
    prompt = repo / "prompt.txt"
    instructions = repo / "instructions.txt"
    schema = repo / "schema.json"
    prompt.write_text(PROMPT + "\n", encoding="utf-8")
    shutil.copyfile(instruction_source, instructions)
    shutil.copyfile(schema_source, schema)
    runner = repo / "container_host_model_ipc_runner_v1.py"
    shutil.copyfile(container_runner, runner)

    ipc_env = dict(os.environ)
    ipc_env["CODEX_EXE"] = codex_exe
    ipc_env["HOST_MODEL_BROKER_TIMEOUT_S"] = "90"
    broker_cmd = [sys.executable, str(broker_source), "--ipc", str(ipc), "--repo", str(repo), "--once"]
    started_ns = time.time_ns()
    broker_proc = subprocess.Popen(broker_cmd, env=ipc_env, stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE, text=True)

    source_path = str(source / "research/live_control")
    runtime_path = str(source / "runtime")
    call_env = dict(os.environ)
    call_env.update({
        "AGENT_INTERFACE_MODEL_BACKEND": "module",
        "AGENT_INTERFACE_MODEL_CALL_MODULE": "docker_model_call_backend_v1",
        "AGENT_INTERFACE_DOCKER_RUNNER": str(runner),
        "AGENT_INTERFACE_DOCKER_IMAGE": BASE_IMAGE,
        "AGENT_INTERFACE_DOCKER_IPC": str(ipc),
        "DOCKER_CONTEXT": "orbstack",
        "PYTHONPATH": os.pathsep.join((source_path, runtime_path,
                                        call_env.get("PYTHONPATH", ""))),
    })
    os.environ.update(call_env)
    sys.path.insert(0, source_path)
    from docker_model_call_backend_v1 import preflight_call
    from model_call_backend_v1 import resolve_preflight_call
    selected = resolve_preflight_call(lambda *args, **kwargs: (_ for _ in ()).throw(
        AssertionError("selected Docker preflight backend was bypassed")))
    selection_ok = selected is preflight_call
    call_output = result_dir / "model-call"
    run_started_ns = time.time_ns()
    status = "STOP_NOT_RUN_SELECTED_BACKEND_MISMATCH"
    call = None
    error = None
    try:
        if not selection_ok:
            raise RuntimeError(status)
        call = selected(prompt, workspace, call_output, instructions, schema)
        status = "CONTAINER_RETURNED"
    except Exception as exc:  # retain the exact bounded stop; never retry
        error = {"class": type(exc).__name__, "message": str(exc)}
        status = "STOP_PREFLIGHT_CALL_EXCEPTION"
    run_ended_ns = time.time_ns()

    try:
        broker_stdout, broker_stderr = broker_proc.communicate(timeout=5)
    except subprocess.TimeoutExpired:
        broker_proc.terminate()
        try:
            broker_stdout, broker_stderr = broker_proc.communicate(timeout=5)
        except subprocess.TimeoutExpired:
            broker_proc.kill()
            broker_stdout, broker_stderr = broker_proc.communicate(timeout=5)
    (root / "broker.stdout.txt").write_text(broker_stdout, encoding="utf-8")
    (root / "broker.stderr.txt").write_text(broker_stderr, encoding="utf-8")
    if call is not None:
        (root / "container.stdout.txt").write_bytes(call.stdout or b"")
        (root / "container.stderr.txt").write_bytes(call.stderr or b"")

    requests = sorted(ipc.glob("*.request.json"))
    brokers = sorted(ipc.glob("*.broker.json"))
    responses = sorted(ipc.glob("*.response.jsonl"))
    result = {"schema_name": name, "status": status, "started_ns": started_ns,
              "run_started_ns": run_started_ns, "run_ended_ns": run_ended_ns,
              "backend_selected_by_resolver": selection_ok,
              "container_returncode": None if call is None else call.returncode,
              "broker_returncode": broker_proc.returncode, "exception": error,
              "counts": {"requests": len(requests), "broker_receipts": len(brokers),
                         "responses": len(responses)}}
    write_json(root / "attempt-result.json", result)
    if call is None or call.returncode != 0 or broker_proc.returncode != 0 or len(requests) != 1 or len(brokers) != 1 or len(responses) != 1:
        result["status"] = "STOP_TRANSPORT_OR_CALL_FAILED"
        write_json(root / "attempt-result.json", result)
        return result

    request = json.loads(requests[0].read_text(encoding="utf-8"))
    broker = json.loads(brokers[0].read_text(encoding="utf-8"))
    process_path = call_output / "process.json"
    events_path = call_output / "events.jsonl"
    if not process_path.is_file() or not events_path.is_file():
        result["status"] = "STOP_CONTAINER_RECEIPT_MISSING"
        write_json(root / "attempt-result.json", result)
        return result

    audit = independently_audit(source, events_path, schema, process_path,
                                requests[0], brokers[0])
    (root / "independent-audit.stdout.txt").write_text(audit["stdout"], encoding="utf-8")
    (root / "independent-audit.stderr.txt").write_text(audit["stderr"], encoding="utf-8")
    write_json(root / "independent-audit-command.json", audit["command"])
    try:
        audit_value = json.loads(audit["stdout"].strip().splitlines()[-1])
    except (json.JSONDecodeError, IndexError):
        audit_value = {"status": "STOP_AUDIT_OUTPUT_INVALID"}
    result.update({"status": "PASS" if audit["returncode"] == 0 and audit_value.get("status") == "PASS" else "FAIL_INDEPENDENT_GATE",
                   "independent_audit_returncode": audit["returncode"],
                   "independent_audit": audit_value,
                   "request_sha256": sha(requests[0]),
                   "broker_receipt_sha256": sha(brokers[0]),
                   "events_sha256": sha(events_path),
                   "process_receipt_sha256": sha(process_path),
                   "schema_sha256": sha(schema),
                   "broker_host_cli_invoked": broker.get("host_cli_invoked"),
                   "authority_granted": request.get("authority_granted")})
    write_json(root / "attempt-result.json", result)
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-checkout", type=Path, required=True)
    parser.add_argument("--evidence", type=Path, required=True)
    parser.add_argument("--codex-exe", default="/opt/homebrew/bin/codex")
    args = parser.parse_args()
    source = args.source_checkout.resolve()
    evidence = args.evidence.resolve()
    if evidence.exists():
        raise FileExistsError(evidence)
    evidence.mkdir(parents=True)
    results = []
    for name, schema_name in SCHEMAS.items():
        result = attempt(name, source, evidence,
                         source / "runtime/host_model_ipc_broker_v1.py",
                         source / "research/live_control/container_host_model_ipc_runner_v1.py",
                         source / "research/live_control" / schema_name,
                         source / "research/live_control/schema_preflight_responder_v1.txt",
                         args.codex_exe)
        results.append(result)
        if result.get("status") != "PASS":
            break
    overall = "PASS_TWO_SCHEMA_PREFLIGHTS" if len(results) == 2 and all(r["status"] == "PASS" for r in results) else "STOP_OR_FAIL"
    write_json(evidence / "experiment-result.json", {
        "schema": "issue_2849_orbstack_real_model_preflight_v1",
        "overall_status": overall,
        "attempt_order": [r["schema_name"] for r in results],
        "attempts": results,
        "formal_six_task_allocation_started": False,
        "scope": "one real host Codex no-image output-schema probe per contract over OrbStack host IPC; no GUI/task effect claim",
    })
    return 0 if overall == "PASS_TWO_SCHEMA_PREFLIGHTS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
