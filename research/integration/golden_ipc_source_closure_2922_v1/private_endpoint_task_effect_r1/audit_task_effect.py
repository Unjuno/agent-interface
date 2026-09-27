"""Independent raw-only audit for Issue #4924; does not trust candidate disposition."""
import hashlib
import json
import urllib.parse
from pathlib import Path

COMMIT = "01349d7bc76e5635f5568c53ffeec4d9ff49abb1"
SEED = 992928
IMAGE = "sha256:436172d89b145c6a9f9a57e655422c9558b3b0235347dd77607e9d61bcfa6393"
ALLOCATION = "issue2922-chromium-task-effect-20260928-r1"
RUNNER_SHA256 = "258ba79c9530187ec3b6eb4bc752b0891d40d7e432bf6eaf84d9a5c41a89e3cd"
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
STEPS = [
    ("chord", None), ("text", "url"), ("key", None),
    ("wait_title", "AI FORM READY"), ("text", "token"),
    ("key", None), ("key", None), ("wait_title", "AI FORM SAVED"),
    ("observe", None),
]

def _jsonl(path):
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]

def audit(result, repo_root, artifact_root, events_override=None, submitted_bytes_override=None):
    root, out = Path(repo_root), Path(artifact_root)
    raw = out / "session"
    errors = []
    events = events_override if events_override is not None else _jsonl(raw / "events.jsonl")
    ready_rows = [e for e in events if e.get("event") == "ready"]
    ready = ready_rows[0] if len(ready_rows) == 1 else {}
    goals = ready.get("goal") or {}
    token, url = goals.get("token"), goals.get("url", "")
    parsed = urllib.parse.urlparse(url)
    expected_token = f"t{SEED:06d}"
    initial = [e for e in events if e.get("event") == "observation" and e.get("id") == "initial"]
    submitted = [e for e in events if e.get("event") == "command"
                 and e.get("command", {}).get("op") == "submit"]
    terminals = [e for e in events if e.get("event") == "terminal"
                 and e.get("id") == "chromium-task-effect-992928"]
    evaluations = [e for e in events if e.get("event") == "independent_evaluation"]
    steps = submitted[0].get("command", {}).get("steps", []) if len(submitted) == 1 else []
    operations = [s.get("op") for s in steps]
    exact_step_content = (
        len(steps) == 9
        and steps[0] == {"op": "chord", "modifier": "Control_L", "key": "l"}
        and steps[1] == {"op": "text", "text": url}
        and steps[2] == {"op": "key", "key": "Return"}
        and steps[3] == {"op": "wait_title", "contains": "AI FORM READY", "timeout_ms": 5000}
        and steps[4] == {"op": "text", "text": token}
        and steps[5] == {"op": "key", "key": "Tab"}
        and steps[6] == {"op": "key", "key": "Return"}
        and steps[7] == {"op": "wait_title", "contains": "AI FORM SAVED", "timeout_ms": 5000}
        and steps[8] == {"op": "observe"}
    )
    terminal = terminals[0] if len(terminals) == 1 else {}
    evaluation = evaluations[0] if len(evaluations) == 1 else {}
    evaluator_actual = evaluation.get("actual")
    observed = [e for e in events if e.get("event") == "observation"]
    rendered_saved = any("AI FORM SAVED" in str(e.get("context")) for e in observed)
    rendered_ready = any("AI FORM READY" in str(e.get("context")) for e in observed)
    result_checks = {
        "schema": result.get("schema") == "issue2924_chromium_fixture_task_effect_v1",
        "allocation": result.get("allocation") == ALLOCATION,
        "seed": result.get("seed") == SEED,
        "commit": result.get("repository_commit") == COMMIT,
        "image": result.get("runtime_image") == IMAGE,
        "one_ready_event": len(ready_rows) == 1,
        "private_loopback": parsed.scheme == "http" and parsed.hostname == "127.0.0.1",
        "ready_token": token == expected_token and result.get("ready_token") == token,
        "initial_observation": len(initial) == 1 and initial[0].get("sequence") == 1
                               and result.get("initial_sequence") == 1,
        "one_submission": len(submitted) == 1 and result.get("executor_program_submissions") == 1,
        "exact_nine_steps": operations == [x[0] for x in STEPS] and exact_step_content,
        "validity_window": (
            len(submitted) == 1
            and type(submitted[0].get("command", {}).get("valid_until_ns")) is int
            and 0 < submitted[0]["command"]["valid_until_ns"] - submitted[0].get("received_ns", 0)
                    <= 20_000_000_000
        ),
        "program_accepted": result.get("accepted") is True
                            and any(e.get("event") == "accepted" for e in events),
        "one_terminal": len(terminals) == 1,
        "program_completed": terminal.get("status") == "completed",
        "release_verified": terminal.get("release", {}).get("verified") is True
                            and terminal.get("release", {}).get("keys_down") == [],
        "ready_page_rendered": rendered_ready and result.get("ready_title_observations", 0) >= 1,
        "saved_page_rendered": rendered_saved and result.get("saved_title_observations", 0) >= 1,
        "one_evaluation": len(evaluations) == 1,
        "evaluator_success": evaluation.get("success") is True,
        "evaluator_exact_value": evaluator_actual == {"value": [token]},
        "no_model_or_broker": result.get("model_calls") == 0 and result.get("broker_calls") == 0
                              and not any("model_call" in str(e.get("event")) or "broker_call" in str(e.get("event")) for e in events),
        "task_allocation": result.get("task_allocated") is True,
        "post_counter_scope": result.get("server_POST_count") == "not instrumented",
        "exit_zero": result.get("container_exit_code") == 0,
    }
    errors.extend(k for k, ok in result_checks.items() if not ok)
    actual_sources = {p: hashlib.sha256((root / p).read_bytes()).hexdigest()
                      for p in SOURCES if (root / p).is_file()}
    if actual_sources != SOURCES:
        errors.append("source_files_or_hashes")
    if result.get("source_sha256") != SOURCES:
        errors.append("result_source_manifest")
    emitted_path = raw / "sources.json"
    try:
        emitted = json.loads(emitted_path.read_text())
        expected_emitted = {p.removeprefix("research/"): digest for p, digest in SOURCES.items()}
        if emitted != expected_emitted:
            errors.append("session_source_receipt")
    except (OSError, ValueError):
        errors.append("session_source_receipt")
    probe = root / "research/integration/golden_ipc_source_closure_2922_v1/private_endpoint_task_effect_r1/session_cli_chromium_task_effect_probe.py"
    if not probe.is_file() or hashlib.sha256(probe.read_bytes()).hexdigest() != RUNNER_SHA256:
        errors.append("runner_hash")
    try:
        body = submitted_bytes_override if submitted_bytes_override is not None else (raw / "submitted.txt").read_bytes()
    except OSError:
        body = None
        errors.append("submitted_bytes_unavailable")
    if body is None:
        output_ok = False
    else:
        try:
            decoded = body.decode("ascii")
            parsed_body = urllib.parse.parse_qs(decoded, keep_blank_values=True, strict_parsing=True)
            output_ok = body == f"value={token}".encode("ascii") and parsed_body == {"value": [token]}
        except (UnicodeDecodeError, ValueError):
            output_ok = False
    if not output_ok:
        errors.append("submitted_bytes_exact_token")
    manifest_ok = True
    try:
        manifest = out / "SHA256SUMS"
        rows = [line.split(maxsplit=1) for line in manifest.read_text().splitlines() if line.strip()]
        listed = set()
        for digest, rel in rows:
            rel = rel.strip()
            target = (out / rel).resolve()
            if target != out.resolve() and out.resolve() not in target.parents:
                manifest_ok = False
                break
            if rel in listed or not target.is_file() or hashlib.sha256(target.read_bytes()).hexdigest() != digest:
                manifest_ok = False
                break
            listed.add(rel)
        actual_files = {
            p.relative_to(out).as_posix() for p in out.rglob("*")
            if p.is_file() and p.name not in {"SHA256SUMS", "AUDIT.json"}
        }
        if listed != actual_files or not listed:
            manifest_ok = False
    except (OSError, ValueError):
        manifest_ok = False
    if not manifest_ok:
        errors.append("sha256_manifest")
    semantic_failures = {
        "saved_page_rendered", "evaluator_success", "evaluator_exact_value",
        "submitted_bytes_exact_token",
    }
    stop_errors = [error for error in errors if error not in semantic_failures]
    verdict = (
        "STOP_CHROMIUM_FIXTURE_TASK_EFFECT" if stop_errors
        else "FAIL_CHROMIUM_FIXTURE_TASK_EFFECT" if errors
        else "PASS_CHROMIUM_FIXTURE_TASK_EFFECT_SCOPED"
    )
    return {
        "schema": "issue2924_chromium_fixture_task_effect_audit_v1",
        "checks": result_checks | {"source_files_or_hashes": "source_files_or_hashes" not in errors,
                                   "result_source_manifest": "result_source_manifest" not in errors,
                                   "session_source_receipt": "session_source_receipt" not in errors,
                                   "runner_hash": "runner_hash" not in errors,
                                   "submitted_bytes_exact_token": output_ok,
                                   "sha256_manifest": manifest_ok},
        "errors": errors,
        "stop_errors": stop_errors,
        "semantic_failures": [error for error in errors if error in semantic_failures],
        "verdict": verdict,
    }

def main():
    here = Path(__file__).resolve().parent
    root = here.parents[3]
    out = Path("/out")
    result = json.loads((out / "session_cli_result.json").read_text())
    receipt = audit(result, root, out)
    (out / "AUDIT.json").write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n")
    print(json.dumps(receipt, sort_keys=True), flush=True)
    return 0 if not receipt["errors"] else 1

if __name__ == "__main__":
    raise SystemExit(main())
