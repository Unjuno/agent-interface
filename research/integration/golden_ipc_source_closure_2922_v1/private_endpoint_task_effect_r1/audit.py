"""Independently audit Issue #4924's one Chromium task-effect allocation."""
import hashlib
import json
import subprocess
import urllib.parse
from pathlib import Path

COMMIT = "01349d7bc76e5635f5568c53ffeec4d9ff49abb1"
ALLOCATION = "issue2922-chromium-task-effect-20260928-r1"
RUNNER_SHA256 = "ad207a27231259f99961dc5875a28097887aca48e02d3c9adff769f0dabf72d4"
ALTERNATE_RUNNER_SHA256 = "7a67c411c32a626524f0575e9cef2ba6988130ad55886bc1ebb6019485db7b75"
SOURCES = {
    "research/live_control/executor_v3.py": "ea3fa8c9751a6a41b4814ad6e0d03bec85166765b0a41d2488a51750d17b3a4a",
    "research/live_control/lease.py": "e71f9850d3999a31fcb86c00f9ef7a8ba19bae8d3a8bdc11bf7bd620817a535f",
    "research/live_control/session_v4.py": "04f06d7b787baa77cae20d0c51b563ccc4985dc19b47308d7c24318c5a9e7fee",
    "research/observation_gating/exact_gate.py": "6780624513a95039657734e76c0420447a3f9ab49f98e1f3137a19a91bc31944",
    "research/observation_gating/gui_suite.py": "953a078a06d55b9278bd7b31e176404912340a4f13407e1db343b7776645e97f",
    "research/observation_tiles/image_artifact.py": "7bf6b71d811aaefa75e87f5d9d20fd9275fc928104e910deaca9e3f00c55363e",
    "research/observation_tiles/tile_transport.py": "f74caf4f2bea59fe3a73b3f04975384d8520bb06c296765566c4dd2542ef12b0",
    "research/real_apps_v1/real_app_suite_v1.py": "22b4cc86af68a0ae866fe24735faaeefa40c0e1722238ab8c04723e1a564db24",
}
EXPECTED_STEPS = ["chord", "text", "key", "wait_title", "text", "key", "key", "wait_title", "observe"]


def audit(result, repo, raw):
    errors = []
    terminal = result.get("executor_terminal") or {}
    evaluation = result.get("independent_evaluation") or {}
    checks = {
        "schema": result.get("schema") == "issue4924_chromium_fixture_task_effect_v1",
        "allocation": result.get("allocation") == ALLOCATION,
        "seed": result.get("seed") == 992928,
        "source_commit": result.get("repository_commit") == COMMIT,
        "image": result.get("runtime_image") == "sha256:436172d89b145c6a9f9a57e655422c9558b3b0235347dd77607e9d61bcfa6393",
        "task_effect_intended": result.get("task_effect_intended") is True,
        "initial_sequence": result.get("initial_sequence") == 1,
        "private_loopback": result.get("session_endpoint_host") == "127.0.0.1",
        "program_completed": terminal.get("status") == "completed",
        "release_verified": terminal.get("release", {}).get("verified") is True,
        "keys_released": terminal.get("release", {}).get("keys_down") == [],
        "one_executor_program": result.get("executor_program_submissions") == 1,
        "no_model_or_broker": result.get("model_calls") == 0 and result.get("broker_calls") == 0,
        "exit_zero": result.get("container_exit_code") == 0,
        "candidate_pass": result.get("disposition") == "PASS_CHROMIUM_FIXTURE_TASK_EFFECT_SCOPED",
    }
    if result.get("source_sha256") != SOURCES:
        errors.append("source_hash_values")
    for path, digest in SOURCES.items():
        blob = subprocess.run(["git", "-C", str(repo), "show", COMMIT + ":" + path],
                              capture_output=True, check=False)
        if blob.returncode or hashlib.sha256(blob.stdout).hexdigest() != digest:
            errors.append("source_blob:" + path)
    runner = Path(repo) / "research/integration/golden_ipc_source_closure_2922_v1/private_endpoint_task_effect_r1/run_task_effect.py"
    checks["runner_hash"] = runner.is_file() and hashlib.sha256(runner.read_bytes()).hexdigest() == RUNNER_SHA256
    alternate = Path(repo) / "research/integration/golden_ipc_source_closure_2922_v1/private_endpoint_task_effect_r1/session_cli_chromium_task_effect_probe.py"
    checks["retained_alternate_runner_hash"] = (
        alternate.is_file() and hashlib.sha256(alternate.read_bytes()).hexdigest() == ALTERNATE_RUNNER_SHA256)
    events_file = Path(raw) / "session/events.jsonl"
    output_file = Path(raw) / "session/submitted.txt"
    try:
        events = [json.loads(x) for x in events_file.read_text().splitlines() if x]
        names = [e.get("event") for e in events]
        checks["event_envelope"] = names[0:2] == ["ready", "observation"] and names[-1] == "independent_evaluation"
        ready = next(e for e in events if e.get("event") == "ready")
        token = ready.get("goal", {}).get("token", "")
        checks["ready_token"] = bool(token) and token == "t" + str(992928)
        submit_events = [e for e in events if e.get("event") == "command" and e.get("command", {}).get("op") == "submit"]
        steps = submit_events[0].get("command", {}).get("steps", []) if len(submit_events) == 1 else []
        checks["exact_plan"] = (
            [s.get("op") for s in steps] == EXPECTED_STEPS
            and steps[1].get("text") == ready.get("goal", {}).get("url")
            and steps[3] == {"op": "wait_title", "contains": "AI FORM READY", "timeout_ms": 5000}
            and steps[7] == {"op": "wait_title", "contains": "AI FORM SAVED", "timeout_ms": 5000})
        checks["only_exact_token"] = len(steps) == 9 and steps[4].get("text") == token
        checks["program_accepted"] = any(e.get("event") == "accepted" for e in events)
        checks["saved_page_observed"] = any(
            e.get("event") == "observation" and "AI FORM SAVED" in str(e.get("context")) for e in events)
        checks["independent_evaluator_event"] = names.count("independent_evaluation") == 1
        posted = urllib.parse.parse_qsl(output_file.read_bytes().decode("ascii"), keep_blank_values=True)
        checks["raw_saved_output_exact"] = posted == [("value", token)]
    except (OSError, ValueError, StopIteration, IndexError, UnicodeError):
        errors.append("events_or_saved_output_unreadable")
        checks.update(event_envelope=False, ready_token=False, exact_plan=False,
                      only_exact_token=False, saved_page_observed=False,
                      program_accepted=False, independent_evaluator_event=False,
                      raw_saved_output_exact=False)
    actual = evaluation.get("actual")
    checks["evaluator_exact_success"] = (
        evaluation.get("success") is True and actual == {"value": [token]}
        if "token" in locals() else False)
    checks["sources_receipt"] = False
    try:
        receipt = json.loads((Path(raw) / "session/sources.json").read_text())
        checks["sources_receipt"] = {
            key.removeprefix("research/"): digest for key, digest in SOURCES.items()
        } == receipt
    except (OSError, ValueError):
        pass
    runner_rel = "run_task_effect.py"
    sums = Path(raw).parent / "SHA256SUMS"
    try:
        entries = [line.split(maxsplit=1) for line in sums.read_text().splitlines() if line]
        manifest_ok = len(entries) >= 8
        seen = set()
        for digest, rel in entries:
            name = rel.strip()
            target = (sums.parent / name).resolve()
            if name in seen or not target.is_file() or hashlib.sha256(target.read_bytes()).hexdigest() != digest:
                manifest_ok = False
            seen.add(name)
        expected_raw = {str(p.relative_to(sums.parent)) for p in (Path(raw)).rglob("*") if p.is_file()}
        expected = expected_raw | {runner_rel, "REPORT.md", "audit.py", "test_audit.py", "write_manifest.py",
                                   "session_cli_chromium_task_effect_probe.py"}
        checks["sha256_manifest"] = manifest_ok and seen == expected
    except (OSError, ValueError):
        checks["sha256_manifest"] = False
    errors.extend(k for k, v in checks.items() if not v)
    return {"schema": "issue4924_chromium_fixture_task_effect_audit_v1",
            "checks": checks, "errors": sorted(set(errors)),
            "verdict": "PASS_RAW_AUDIT" if not errors else "FAIL_RAW_AUDIT"}


def main():
    here = Path(__file__).resolve().parent
    repo = here.parents[3]
    raw = here / "raw"
    result = json.loads((raw / "session_cli_result.json").read_text())
    receipt = audit(result, repo, raw)
    (here / "AUDIT.json").write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n")
    print(json.dumps(receipt, sort_keys=True))
    return 0 if receipt["verdict"] == "PASS_RAW_AUDIT" else 1


if __name__ == "__main__":
    raise SystemExit(main())
