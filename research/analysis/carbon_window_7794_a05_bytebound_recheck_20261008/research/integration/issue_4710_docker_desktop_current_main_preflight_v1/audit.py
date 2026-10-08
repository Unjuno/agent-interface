from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _matches_type(value, kind: str) -> bool:
    if kind == "object":
        return isinstance(value, dict)
    if kind == "array":
        return isinstance(value, list)
    if kind == "string":
        return isinstance(value, str)
    if kind == "integer":
        return isinstance(value, int) and not isinstance(value, bool)
    if kind == "number":
        return isinstance(value, (int, float)) and not isinstance(value, bool)
    if kind == "boolean":
        return isinstance(value, bool)
    if kind == "null":
        return value is None
    return False


def validate_schema(value, schema, at="$", errors=None):
    if errors is None:
        errors = []
    if not isinstance(schema, dict):
        errors.append(f"{at}: schema node is not an object")
        return errors
    expected_type = schema.get("type")
    if expected_type is not None and not _matches_type(value, expected_type):
        errors.append(f"{at}: expected {expected_type}")
        return errors
    if "const" in schema and value != schema["const"]:
        errors.append(f"{at}: const mismatch")
    if isinstance(value, dict):
        required = schema.get("required", [])
        for key in required:
            if key not in value:
                errors.append(f"{at}: missing {key}")
        properties = schema.get("properties", {})
        if schema.get("additionalProperties") is False:
            extra = sorted(set(value) - set(properties))
            if extra:
                errors.append(f"{at}: additional properties {extra}")
        for key, subschema in properties.items():
            if key in value:
                validate_schema(value[key], subschema, f"{at}.{key}", errors)
    elif isinstance(value, list) and "items" in schema:
        for index, child in enumerate(value):
            validate_schema(child, schema["items"], f"{at}[{index}]", errors)
    return errors


def audit(repo: Path, evidence: Path, ipc: Path) -> dict:
    manifest_path = repo / "research/integration/issue_4710_docker_desktop_current_main_preflight_v1/SOURCE_MANIFEST.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    errors = []
    source_checks = {}
    for relative, expected in manifest["source_sha256"].items():
        path = repo / relative
        actual = sha256(path) if path.is_file() else None
        source_checks[relative] = actual == expected
        if actual != expected:
            errors.append(f"source hash mismatch: {relative}")

    out = evidence / "formal01"
    required_out = ["prompt.txt", "plan.json", "events.jsonl",
                    "event-accounting.json", "process.json"]
    output_checks = {}
    for name in required_out:
        output_checks[name] = (out / name).is_file()
        if not output_checks[name]:
            errors.append(f"missing output artifact: {name}")

    reqs = sorted(ipc.glob("*.request.json"))
    responses = sorted(ipc.glob("*.response.jsonl"))
    brokers = sorted(ipc.glob("*.broker.json"))
    if not (len(reqs) == len(responses) == len(brokers) == 1):
        errors.append("expected exactly one request, response, and broker receipt")
    request = json.loads(reqs[0].read_text(encoding="utf-8")) if len(reqs) == 1 else {}
    broker = json.loads(brokers[0].read_text(encoding="utf-8")) if len(brokers) == 1 else {}
    process = json.loads((out / "process.json").read_text(encoding="utf-8")) if (out / "process.json").is_file() else {}
    accounting = json.loads((out / "event-accounting.json").read_text(encoding="utf-8")) if (out / "event-accounting.json").is_file() else {}
    launcher = json.loads((evidence / "launcher-result.json").read_text(encoding="utf-8")) if (evidence / "launcher-result.json").is_file() else {}
    env = json.loads((evidence / "environment.json").read_text(encoding="utf-8")) if (evidence / "environment.json").is_file() else {}

    checks = {}
    def check(name, predicate):
        checks[name] = bool(predicate)
        if not predicate:
            errors.append(name)

    check("one_model_call_limit", manifest["model_call_limit"] == 1)
    check("request_authority_false", request.get("authority_granted") is False)
    check("request_has_no_image", request.get("image") is None and request.get("image_sha256") is None)
    check("request_model_route_fixed", request.get("runner") == manifest["runner_name"] and request.get("mode") == manifest["mode"])
    check("prompt_exact", request.get("prompt") == manifest["prompt"])
    check("instructions_path", request.get("instructions") == "/repo/" + manifest["instructions_path"])
    check("instructions_hash", request.get("instructions_sha256") == manifest["source_sha256"][manifest["instructions_path"]])
    check("schema_path", request.get("schema") == "/repo/" + manifest["schema_path"])
    check("schema_hash", request.get("schema_sha256") == manifest["source_sha256"][manifest["schema_path"]])
    check("working_path_is_empty_scratch", request.get("working") == "/repo/.empty-workspace")
    check("broker_receipt_matches_request", broker.get("request_id") == request.get("request_id"))
    check("broker_return_zero", broker.get("returncode") == 0)
    check("broker_authority_false", broker.get("authority_granted") is False)
    check("broker_boundary", broker.get("boundary") == "host-local-codex-exe")
    check("runner_exit_zero", process.get("exit_code") == 0)
    check("runner_status", process.get("status") == "PASS")
    check("runner_model", process.get("requested_model") == manifest["model"])
    check("runner_effort", process.get("requested_effort") == manifest["effort"])
    check("runner_authority_false", process.get("authority_granted") is False)
    check("runner_request_id", process.get("request_id") == request.get("request_id"))
    check("accounting_pass", accounting.get("status") == "PASS")
    check("one_assistant_message", accounting.get("assistant_message_count") == 1)
    check("response_is_object", accounting.get("response_is_object") is True)
    usage = accounting.get("turn_usage")
    check("usage_present_and_nonnegative", isinstance(usage, dict) and bool(usage) and
          all(isinstance(v, int) and not isinstance(v, bool) and v >= 0 for v in usage.values()))

    event_rows = [json.loads(line) for line in (out / "events.jsonl").read_text(encoding="utf-8").splitlines() if line.strip()] if (out / "events.jsonl").is_file() else []
    messages = [r for r in event_rows if r.get("type") == "item.completed" and isinstance(r.get("item"), dict) and r["item"].get("type") == "agent_message"]
    turns = [r for r in event_rows if r.get("type") == "turn.completed"]
    check("raw_one_agent_message", len(messages) == 1)
    check("raw_one_completed_turn", len(turns) == 1)
    check("raw_event_stream_lineage", len(reqs) == 1 and len(responses) == 1 and responses[0].stem.replace(".response", "") == request.get("request_id"))
    check("launcher_exactly_one_request", launcher.get("request_count") == 1)
    check("launcher_exactly_one_response", launcher.get("response_count") == 1)
    check("launcher_exactly_one_broker_receipt", launcher.get("broker_receipt_count") == 1)

    schema = json.loads((repo / manifest["schema_path"]).read_text(encoding="utf-8"))
    assistant_text = messages[0].get("item", {}).get("text") if len(messages) == 1 else None
    try:
        decoded = json.loads(assistant_text) if isinstance(assistant_text, str) else None
        schema_errors = validate_schema(decoded, schema)
    except (json.JSONDecodeError, TypeError):
        decoded = None
        schema_errors = ["assistant response is not JSON"]
    check("schema_valid_json_object", isinstance(decoded, dict) and not schema_errors)
    check("container_exit_zero", launcher.get("container_exit_code") == 0)
    check("broker_process_exit_zero", launcher.get("broker_process_exit_code") == 0)
    check("container_cleanup_succeeded", launcher.get("docker_cleanup_exit_code") == 0)
    check("docker_network_none", launcher.get("docker_network") == "none")
    check("read_only_root", launcher.get("read_only_root") is True)
    check("source_read_only", launcher.get("source_read_only") is True)
    inspect = launcher.get("container_inspect") or {}
    check("inspect_network_none", inspect.get("NetworkMode") == "none")
    check("inspect_root_read_only", inspect.get("ReadonlyRootfs") is True)
    check("inspect_drop_all_capabilities", "ALL" in (inspect.get("CapDrop") or []))
    mounts = {item.get("Target"): item for item in inspect.get("Mounts", [])}
    check("inspect_source_mount_read_only", mounts.get("/repo", {}).get("RW") is False)
    check("inspect_output_mount_writable", mounts.get("/output", {}).get("RW") is True)
    check("inspect_ipc_mount_writable", mounts.get("/ipc", {}).get("RW") is True)
    check("image_identity", launcher.get("image_id") == manifest["image_id"] and launcher.get("image_platform") == manifest["image_platform"])
    check("host_codex_identity", env.get("codex_cli_version") == manifest["codex_cli_version"] and env.get("codex_exe_sha256") == manifest["codex_exe_sha256"])

    return {
        "disposition": "PASS_DOCKER_DESKTOP_CURRENT_MAIN_INSTRUCTIONS_PREFLIGHT_ONLY" if not errors else "HOLD_PREFLIGHT_AUDIT_OR_USAGE",
        "allocation_id": manifest["allocation_id"],
        "main_sha": manifest["intake_main_sha"],
        "source_checks": source_checks,
        "output_checks": output_checks,
        "checks": checks,
        "schema_errors": schema_errors,
        "usage": usage,
        "errors": errors,
        "scope": "one no-image host Codex CLI compiled-schema/instructions IPC preflight; no GUI, input, task or efficiency claim"
    }


def main():
    if len(sys.argv) != 4:
        raise SystemExit("usage: audit.py REPO EVIDENCE IPC")
    result = audit(Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3]))
    target = Path("/audit/AUDIT.json")
    target.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"disposition": result["disposition"], "checks": sum(result["checks"].values()), "errors": len(result["errors"])}))
    return 0 if result["disposition"].startswith("PASS_") else 1


if __name__ == "__main__":
    raise SystemExit(main())
