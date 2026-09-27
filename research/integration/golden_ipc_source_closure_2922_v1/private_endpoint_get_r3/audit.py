"""Independent audit of the Chromium navigation-only Issue #2922 allocation."""
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
EXPECTED_PROBE = "11758084745384736c2c4b067483c8052f4eca79c106ccbacce30adf086e5b6f"
COMMIT = "01349d7bc76e5635f5568c53ffeec4d9ff49abb1"

def audit(result, repo_root, artifact_root):
    errors = []
    terminal = result.get("executor_terminal") or {}
    evaluation = result.get("independent_evaluation") or {}
    checks = {
        "schema": result.get("schema") == "issue2922_session_cli_chromium_navigation_v1",
        "allocation": result.get("allocation") == "issue2922-session-cli-chromium-navigation-20260928-r1",
        "seed": result.get("seed") == 992927,
        "commit": result.get("repository_commit") == COMMIT,
        "image": result.get("runtime_image") == "sha256:436172d89b145c6a9f9a57e655422c9558b3b0235347dd77607e9d61bcfa6393",
        "ready": result.get("ready_event") is True,
        "initial_sequence": result.get("initial_sequence") == 1,
        "private_loopback": result.get("session_endpoint_host") == "127.0.0.1",
        "navigation_method": result.get("request_method") == "GET by Chromium navigation",
        "program_accepted": result.get("accepted") is True,
        "program_completed": terminal.get("status") == "completed",
        "release_verified": terminal.get("release", {}).get("verified") is True,
        "no_keys_down": terminal.get("release", {}).get("keys_down") == [],
        "rendered_page": result.get("chromium_title_ready_observations", 0) >= 1,
        "final_title": "AI FORM READY" in str(result.get("final_context")),
        "input_count": result.get("input_admission_events") == 28,
        "no_form_submit": result.get("form_submit_steps_issued") == 0,
        "one_executor_program": result.get("executor_program_submissions") == 1,
        "not_task_allocated": result.get("task_allocated") is False,
        "no_model": result.get("model_calls") == 0,
        "server_counter_scope": result.get("server_POST_count") == "not instrumented",
        "evaluator_no_output": (
            evaluation.get("success") is False
            and "FileNotFoundError" in evaluation.get("actual", {}).get("error", "")),
        "exit_zero": result.get("container_exit_code") == 0,
        "disposition": result.get("disposition") == "PASS_CHROMIUM_PRIVATE_ROUTE_NAVIGATION_NO_TASK",
    }
    errors.extend(key for key, ok in checks.items() if not ok)
    if result.get("source_sha256") != EXPECTED_SOURCES:
        errors.append("source_hash_values")
    for path, digest in EXPECTED_SOURCES.items():
        blob = subprocess.run(["git", "-C", str(repo_root), "show", COMMIT + ":" + path],
                              stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
        if blob.returncode or hashlib.sha256(blob.stdout).hexdigest() != digest:
            errors.append("source_blob:" + path)
    probe = Path(repo_root) / "research/integration/golden_ipc_source_closure_2922_v1/session_cli_chromium_navigation_probe.py"
    if not probe.is_file() or hashlib.sha256(probe.read_bytes()).hexdigest() != EXPECTED_PROBE:
        errors.append("probe_hash")
    raw_events = Path(artifact_root) / "session/events.jsonl"
    try:
        events = [json.loads(line) for line in raw_events.read_text().splitlines() if line]
        names = [event.get("event") for event in events]
        if names[0:3] != ["ready", "observation", "command"] or names[-1] != "independent_evaluation":
            errors.append("event_sequence_envelope")
        nav_observations = [e for e in events if e.get("event") == "observation"
                            and e.get("id") == "private-url-navigation-992927"]
        if not any("AI FORM READY" in str(e.get("context")) for e in nav_observations):
            errors.append("raw_navigation_title")
        plans = [e.get("command", {}) for e in events if e.get("event") == "command"
                 and e.get("command", {}).get("op") == "submit"]
        operations = [step.get("op") for step in plans[0].get("steps", [])] if len(plans) == 1 else []
        if operations != ["chord", "text", "key", "wait_title", "observe"]:
            errors.append("navigation_plan_scope")
    except (OSError, ValueError, IndexError):
        errors.append("raw_events_invalid")
    sums_path = Path(artifact_root).parent / "SHA256SUMS"
    sums_ok = True
    try:
        entries = [line.split(maxsplit=1) for line in sums_path.read_text().splitlines() if line]
        if len(entries) != 20:
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
    return {"schema": "issue2922_session_cli_chromium_navigation_audit_v1",
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
