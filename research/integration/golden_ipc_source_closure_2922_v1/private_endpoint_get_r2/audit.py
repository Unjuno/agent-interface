"""Independent audit of the actual session_v4 CLI GET-only allocation."""
import hashlib
import json
import subprocess
from pathlib import Path

EXPECTED_SOURCES = {
    "research/live_control/executor_v3.py": "ea3fa8c9751a6a41b4814ad6e0d03bec85166765b0a41d2488a51750d17b3a4a",
    "research/live_control/lease.py": "e71f9850d3999a31fcb86c00f9ef7a8ba19bae8d3a8bdc11bf7bd620817a535f",
    "research/live_control/session_v4.py": "04f06d7b787baa77cae20d0c51b563ccc4985dc19b47308d7c24318c5a9e7fee",
    "research/observation_gating/exact_gate.py": "6780624513a95039657734e76c0420447a3f9ab49f98e1f3137a19a91bc31944",
    "research/observation_gating/gui_suite.py": "953a078a06d55b9278bd7b31e176404912340a4f13407e1db343b7776645e97f",
    "research/observation_tiles/image_artifact.py": "7bf6b71d811aaefa75e87f5d9d20fd9275fc928104e910deaca9e3f00c55363e",
    "research/observation_tiles/tile_transport.py": "f74caf4f2bea59fe3a73b3f04975384d8520bb06c296765566c4dd2542ef12b0",
    "research/real_apps_v1/real_app_suite_v1.py": "22b4cc86af68a0ae866fe24735faaeefa40c0e1722238ab8c04723e1a564db24",
}
EXPECTED_PROBE = "9e8f8d8751fd799dd25b9c97ca78a111a6f61f9ab2b4068de09fe38995e47fc1"

def audit(result, repo_root, artifact_root):
    errors = []
    checks = {
        "schema": result.get("schema") == "issue2922_session_cli_endpoint_get_v1",
        "allocation": result.get("allocation") == "issue2922-session-cli-endpoint-get-20260927-r1",
        "seed": result.get("seed") == 992926,
        "commit": result.get("repository_commit") == "01349d7bc76e5635f5568c53ffeec4d9ff49abb1",
        "image": result.get("runtime_image") == "sha256:436172d89b145c6a9f9a57e655422c9558b3b0235347dd77607e9d61bcfa6393",
        "ready": result.get("ready_event") is True,
        "ready_before_get": result.get("ready_before_get") is True,
        "loopback": result.get("session_endpoint_host") == "127.0.0.1",
        "GET": result.get("request_method") == "GET",
        "HTTP_200": result.get("http_status") == 200,
        "body_length": result.get("body_bytes") == 187,
        "body_marker": result.get("body_contains_ready_marker") is True,
        "exit_zero": result.get("container_exit_code") == 0,
        "no_task": result.get("task_allocated") is False,
        "no_submit": result.get("submit_commands") == 0,
        "no_input": result.get("input_admission_events") == 0,
        "no_model": result.get("model_calls") == 0,
        "no_probe_POST": result.get("probe_POST_calls_issued") == 0,
        "server_POST_honest": result.get("server_POST_count") == "not instrumented",
        "evaluation_absent_output": (
            isinstance(result.get("independent_evaluation"), dict)
            and result["independent_evaluation"].get("success") is False
            and "FileNotFoundError" in result["independent_evaluation"].get("actual", {}).get("error", "")),
        "disposition": result.get("disposition") == "PASS_CLI_READY_PRIVATE_ENDPOINT_GET_NO_TASK",
    }
    errors.extend(name for name, passed in checks.items() if not passed)
    if result.get("source_sha256") != EXPECTED_SOURCES:
        errors.append("source_sha256_values")
    for rel, expected in EXPECTED_SOURCES.items():
        proc = subprocess.run(["git", "-C", str(repo_root), "show",
                               result.get("repository_commit", "") + ":" + rel],
                              stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
        if proc.returncode or hashlib.sha256(proc.stdout).hexdigest() != expected:
            errors.append("source_blob:" + rel)
    probe = Path(repo_root) / "research/integration/golden_ipc_source_closure_2922_v1/session_cli_endpoint_get_probe.py"
    if not probe.is_file() or hashlib.sha256(probe.read_bytes()).hexdigest() != EXPECTED_PROBE:
        errors.append("probe_source_hash")
    raw_events = Path(artifact_root) / "session/events.jsonl"
    try:
        events = [json.loads(line) for line in raw_events.read_text().splitlines() if line]
        names = [event.get("event") for event in events]
        if names != ["ready", "observation", "command", "independent_evaluation"]:
            errors.append("event_order")
        if events[0].get("goal", {}).get("url", "").split("/")[2].split(":")[0] != "127.0.0.1":
            errors.append("raw_ready_url")
    except (OSError, ValueError, IndexError):
        errors.append("raw_events_invalid")
    sums_path = Path(artifact_root).parent / "SHA256SUMS"
    sums_ok = True
    try:
        entries = [line.split(maxsplit=1) for line in sums_path.read_text().splitlines() if line]
        if len(entries) != 8:
            sums_ok = False
        for expected, rel in entries:
            target = (sums_path.parent / rel.strip()).resolve()
            if not target.is_file() or hashlib.sha256(target.read_bytes()).hexdigest() != expected:
                sums_ok = False
    except (OSError, ValueError):
        sums_ok = False
    checks["sha256_manifest"] = sums_ok
    if not sums_ok:
        errors.append("sha256_manifest")
    return {"schema": "issue2922_session_cli_endpoint_get_audit_v1",
            "checks": checks, "errors": errors,
            "verdict": "PASS_RAW_AUDIT" if not errors else "FAIL_RAW_AUDIT"}

def main():
    here = Path(__file__).resolve().parent
    repo = here.parents[3]
    raw = here / "raw"
    result = json.loads((raw / "session_cli_result.json").read_text())
    receipt = audit(result, repo, raw)
    (here / "AUDIT.json").write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n")
    print(json.dumps(receipt, sort_keys=True))
    return 0 if not receipt["errors"] else 1

if __name__ == "__main__":
    raise SystemExit(main())
