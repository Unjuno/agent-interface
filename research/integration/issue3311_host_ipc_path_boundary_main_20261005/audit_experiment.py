"""Raw-only audit of the inert host-IPC boundary experiment."""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import sys

from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[3]


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def audit(directory: Path, source_root: Path = ROOT) -> dict:
    d = Path(directory).resolve()
    source_root = Path(source_root).resolve()
    errors = []
    execution = load(d / "execution.json")
    environment = load(d / "environment.json")
    if execution.get("runner_returncode") != 0: errors.append("runner_exit")
    if execution.get("broker_returncode") != 0: errors.append("broker_exit")
    if environment.get("container_launched") is not False: errors.append("container_scope")
    if environment.get("real_model_called") is not False: errors.append("model_scope")
    if environment.get("gui_or_native_input") is not False: errors.append("input_scope")

    sources = load(d / "source_sha256.json")
    source_results = {}
    for name, expected in sources.items():
        try:
            relative = Path(name)
            if not isinstance(name, str) or relative.is_absolute() or ".." in relative.parts:
                raise ValueError("source path is not repository-relative")
            source = (source_root / relative).resolve(strict=True)
            source.relative_to(source_root)
            if not source.is_file():
                raise OSError("source is not a file")
            actual = digest(source)
        except (OSError, RuntimeError, TypeError, ValueError):
            actual = None
            errors.append("source_path_unavailable:" + str(name))
        source_results[name] = {"expected": expected, "actual": actual,
                                "match": actual == expected}
        if actual != expected: errors.append("source_hash:" + name)

    request = load(d / "ipc.request.json")
    broker = load(d / "ipc.broker.json")
    process = load(d / "runner.process.json")
    commands = load(d / "commands.json")
    request_id = request.get("request_id")
    if not isinstance(request_id, str) or request_id != execution.get("request_id"):
        errors.append("request_identity")
    if process.get("request_id") != request_id or process.get("exit_code") != 0:
        errors.append("process_receipt")
    if request.get("mode") != "handle" or request.get("authority_granted") is not False:
        errors.append("request_authority")
    if request.get("image") is not None or request.get("image_sha256") is not None:
        errors.append("preflight_no_image")
    if (broker.get("request_id") != request_id or broker.get("returncode") != 0
            or broker.get("authority_granted") is not False
            or broker.get("boundary") != "host-local-codex-exe"):
        errors.append("broker_receipt")

    schema_path = d / "schema.json"
    instruction_path = d / "instructions.txt"
    workspace = d / "workspace"
    if request.get("schema_sha256") != digest(schema_path): errors.append("request_schema_hash")
    if request.get("instructions_sha256") != digest(instruction_path):
        errors.append("request_instructions_hash")

    events_bytes = (d / "runner.events.jsonl").read_bytes()
    if events_bytes != (d / "ipc.response.jsonl").read_bytes(): errors.append("response_copy")
    if events_bytes != (d / "ipc" / f"{request_id}.response.jsonl").read_bytes():
        errors.append("response_raw")
    events = [json.loads(line) for line in events_bytes.decode("utf-8").splitlines()]
    starts = [e for e in events if e.get("type") == "thread.started"]
    messages = [e.get("item", {}).get("text") for e in events
                if e.get("type") == "item.completed"
                and e.get("item", {}).get("type") == "agent_message"]
    turns = [e for e in events if e.get("type") == "turn.completed"]
    if len(starts) != 1 or starts[0].get("thread_id") != "inert-call":
        errors.append("one_call_identity")
    if len(messages) != 1: errors.append("one_model_message")
    else:
        try:
            result = json.loads(messages[0])
            Draft202012Validator(load(schema_path)).validate(result)
        except Exception as error:
            errors.append("schema_validation:" + type(error).__name__)
    if len(turns) != 1 or turns[0].get("usage") != {"input_tokens": 5, "output_tokens": 2}:
        errors.append("usage_record")

    path_map = load(d / "out" / "host-path-map.json")
    repo = d / "broker-repo"
    manifest_path = d / "evidence-manifest.json"
    manifest_files = (load(manifest_path).get("files", {})
                      if manifest_path.is_file() else {})
    if path_map.get("schema") != "docker-host-ipc-path-map-v1": errors.append("path_map_schema")
    runner_command = commands.get("runner", [])
    broker_command = commands.get("broker", [])
    command_positions = {"runner": 1, "prompt": 4, "workspace": 5,
                         "instructions": 9, "schema": 10}
    source_name = "research/live_control/container_host_model_ipc_runner_v1.py"
    expected_hashes = {"runner": sources.get(source_name),
                       "schema": digest(schema_path),
                       "instructions": digest(instruction_path),
                       "prompt": digest(d / "out/prompt.txt"),
                       "workspace": None}
    paths = path_map.get("paths", {})
    resolved_paths = {"schema": paths.get("schema", {}).get("host_path"),
                      "working": paths.get("workspace", {}).get("host_path"),
                      "image": None}
    if broker.get("resolved_paths") != resolved_paths: errors.append("resolved_paths")
    try:
        if broker_command[broker_command.index("--repo") + 1] != path_map.get("host_repo"):
            errors.append("broker_repo_argument")
    except (ValueError, IndexError):
        errors.append("broker_repo_argument")
    path_map_results = {}
    for name, expected_hash in expected_hashes.items():
        link_name = {"runner": "runner.py", "schema": "schema.json",
                     "instructions": "instructions.txt", "prompt": "prompt.txt",
                     "workspace": "workspace"}[name]
        link = repo / link_name
        record = paths.get(name, {})
        pos = command_positions[name]
        command_target = runner_command[pos] if len(runner_command) > pos else None
        manifest_link = manifest_files.get(f"broker-repo/{link_name}", {})
        link_matches = (link.is_symlink() and os.readlink(link) == record.get("host_path"))
        if not link.exists() and not link.is_symlink():
            link_matches = (manifest_link.get("type") == "symlink"
                            and manifest_link.get("target") == record.get("host_path"))
        okay = (isinstance(record.get("host_path"), str)
                and record.get("host_path") == command_target
                and record.get("sha256") == expected_hash
                and link_matches)
        path_map_results[name] = okay
        if not okay: errors.append("path_map:" + name)

    audit_result = {
        "schema": "issue3311-inert-host-ipc-boundary-audit-v1",
        "auditor_sha256": digest(Path(__file__).resolve()),
        "decision": "PASS_BOUNDARY_ONLY" if not errors else "HOLD",
        "error_count": len(errors), "errors": errors,
        "request_id": request_id,
        "runner_exit": execution.get("runner_returncode"),
        "broker_exit": execution.get("broker_returncode"),
        "no_authority": request.get("authority_granted") is False
                       and broker.get("authority_granted") is False,
        "source_hashes": source_results,
        "path_map_checks": path_map_results,
        "schema_valid": not any(e.startswith("schema_validation") for e in errors),
        "scope": "inert local process IPC; no Docker, real model, GUI, or task effect",
    }
    (d / "independent-audit.json").write_text(
        json.dumps(audit_result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(audit_result, indent=2))
    return audit_result


if __name__ == "__main__":
    if len(sys.argv) not in (2, 4) or (len(sys.argv) == 4 and sys.argv[2] != "--source-root"):
        raise SystemExit("usage: audit_experiment.py EVIDENCE_DIRECTORY [--source-root REPOSITORY_SNAPSHOT]")
    source_root = Path(sys.argv[3]) if len(sys.argv) == 4 else ROOT
    result = audit(Path(sys.argv[1]), source_root=source_root)
    raise SystemExit(0 if result["decision"] == "PASS_BOUNDARY_ONLY" else 1)
