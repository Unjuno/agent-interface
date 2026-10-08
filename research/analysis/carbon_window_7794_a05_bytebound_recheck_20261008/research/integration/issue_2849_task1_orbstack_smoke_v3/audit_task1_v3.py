"""Offline independent audit for the seed-284903 successor bundle."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import subprocess

REPO = Path(__file__).resolve().parents[3]
BASE = REPO / "research/integration/issue_2849_task1_orbstack_smoke_v3/evidence"
RUN = BASE / "formal-task1-seed-284903"
IPC = BASE / "ipc"


def read(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    manifest = read(RUN / "pre-call-source-manifest.json")
    stop = read(RUN / "attempt-stop.json")
    failures = []
    if manifest.get("status") != "FROZEN_BEFORE_MODEL_CALL":
        failures.append("manifest_not_frozen")
    for entry in manifest.get("source_files", []):
        path = REPO / entry["path"]
        if entry["path"] == "research/integration/issue_2849_task1_orbstack_smoke_v3/audit_task1_v3.py":
            # The independent auditor evolves after source freeze; exclude only
            # itself from the experiment-input closure, never from checksums.
            continue
        if not path.is_file() or sha(path) != entry["sha256"]:
            failures.append("source_hash_mismatch:" + entry["path"])
    frozen = read(RUN / "frozen-task.json")
    trace = read(RUN / "task-trace.json")
    scope = read(RUN / "task1-scope-result.json")
    detail = read(RUN / "task-detail.json")
    whole = read(RUN / "six-task-fixture-evaluation.json")
    history = read(RUN / "submission-history.snapshot.json")
    task_rows = [row for row in history if row.get("task_id") == "task-1"]
    if (frozen.get("seed"), frozen.get("task_id"), frozen.get("layout"),
            frozen.get("phase"), frozen.get("route")) != (
            284903, "task-1", "A", "cold", "plain"):
        failures.append("task_scope_mismatch")
    if stop.get("status") == "STOP_DOCKER_BACKEND_RUNNER_INVOCATION":
        if history or task_rows:
            failures.append("unexpected_fixture_effect_after_pre_model_stop")
    elif len(history) != 1 or len(task_rows) != 1:
        failures.append("unexpected_or_duplicate_effect")
    elif not (task_rows[0].get("exact") is True
              and task_rows[0].get("expected_token") == frozen.get("token")
              and task_rows[0].get("submitted_values") == [frozen.get("token")]
              and task_rows[0].get("layout") == "A"):
        failures.append("fixture_oracle_effect_mismatch")
    if stop.get("status") == "STOP_DOCKER_BACKEND_RUNNER_INVOCATION":
        # Explicit failure-path audit: verify the STOP boundary, without
        # misclassifying it as either acceptance or an evidence-integrity fail.
        client_result = read(RUN / "model-calls/plain/task-1/anchor/client-result.json")
        client_stderr = (RUN / "model-calls/plain/task-1/anchor/runner-stderr.txt").read_text()
        if not (stop.get("outer_invocations") == 1
                and stop.get("selected_model_backend_invocations") == 1
                and stop.get("nested_model_container_started") is False
                and stop.get("host_model_ipc_requests") == 0
                and stop.get("model_calls_completed") == 0
                and client_result.get("returncode") == 1
                and "can't find '__main__' module in '/repo/runner.py'" in client_stderr
                and trace.get("typed_outcome") == "failed"
                and trace.get("submission_count") == 0
                and trace.get("releases_verified") is True
                and scope.get("status") == "FAIL_TASK1_SCOPED"
                and detail.get("adaptive", {}).get("outcome") == "CALLER_FAILED"):
            failures.append("registered_stop_boundary_mismatch")
        if any(path.is_file() for path in IPC.rglob("*")):
            failures.append("unexpected_host_model_ipc_artifact")
    elif not (trace.get("typed_outcome") == "completed"
              and trace.get("model_visible_images") == 1
              and len(trace.get("model_calls", [])) == 1
              and trace.get("submission_count") == 1
              and trace.get("exact_submission") is True
              and trace.get("releases_verified") is True
              and scope.get("status") == "PASS_TASK1_SCOPED"
              and detail.get("adaptive", {}).get("outcome") == "TASK_SUCCEEDED"):
        failures.append("runtime_task_gate_mismatch")
    if (whole.get("success") is not False
            or whole.get("record_count") != (0 if stop.get("status")
                                               == "STOP_DOCKER_BACKEND_RUNNER_INVOCATION" else 1)):
        failures.append("six_task_scope_boundary_mismatch")

    requests = sorted(IPC.glob("*.request.json"))
    responses = sorted(IPC.glob("*.response.jsonl"))
    brokers = sorted(IPC.glob("*.broker.json"))
    if stop.get("status") == "STOP_DOCKER_BACKEND_RUNNER_INVOCATION":
        if requests or responses or brokers:
            failures.append("unexpected_ipc_receipt_for_pre_model_stop")
    elif not (len(requests) == len(responses) == len(brokers) == 1):
        failures.append("ipc_receipt_count_mismatch")
    event_paths = sorted(RUN.glob("model-calls/**/runner/events.jsonl"))
    if stop.get("status") == "STOP_DOCKER_BACKEND_RUNNER_INVOCATION":
        if event_paths:
            failures.append("unexpected_nested_model_event_stream")
    elif len(event_paths) != 1:
        failures.append("image_model_event_count_mismatch")
    else:
        events_file = event_paths[0]
        events = [json.loads(line) for line in events_file.read_text(
            encoding="utf-8").splitlines() if line]
        messages = [event for event in events if event.get("type") == "item.completed"
                    and event.get("item", {}).get("type") == "agent_message"]
        turns = [event for event in events if event.get("type") == "turn.completed"]
        if len(messages) != 1 or len(turns) != 1:
            failures.append("message_or_turn_count_mismatch")
        try:
            json.loads(messages[0]["item"]["text"])
        except (IndexError, KeyError, TypeError, json.JSONDecodeError):
            failures.append("assistant_output_not_json")
        runner = events_file.parent
        if not (read(runner / "process.json").get("exit_code") == 0
                and read(runner / "event-accounting.json").get("status") == "PASS"):
            failures.append("event_accounting_or_runner_receipt_failed")
        schema_validation = events_file.parents[1] / "schema-validation.json"
        if not schema_validation.is_file() or read(schema_validation).get("status") != "PASS":
            failures.append("independent_schema_validation_failed")
    if requests and brokers:
        request = read(requests[0]); broker = read(brokers[0])
        if not (request.get("authority_granted") is False
                and request.get("mode") == "coordinate"
                and request.get("image_sha256")
                and broker.get("returncode") == 0
                and broker.get("authority_granted") is False):
            failures.append("host_model_boundary_receipt_failed")
    runtime_log = RUN / "runtime/runtime/events.jsonl"
    releases = []
    if runtime_log.is_file():
        for line in runtime_log.read_text(encoding="utf-8").splitlines():
            if line:
                event = json.loads(line)
                if event.get("event") == "terminal" and isinstance(event.get("release"), dict):
                    releases.append(event["release"])
    if (not releases or any(not (item.get("verified") is True
                                and item.get("keys_down") == []
                                and item.get("buttons_down") == []) for item in releases)):
        failures.append("raw_empty_release_verification_failed")
    owner_path = RUN / "runtime/runtime/owner-events.json"
    owner_releases = read(owner_path) if owner_path.is_file() else []
    if (not owner_releases or any(not (item.get("verified") is True
                                       and item.get("keys_down") == []
                                       and item.get("buttons_down") == [])
                                  for item in owner_releases)
            or not any(item.get("reason") == "close" for item in owner_releases)):
        failures.append("owner_empty_release_close_not_verified")
    audit = {
        "status": (("VERIFIED_STOP_BOUNDARY" if not failures
                    else "FAIL_STOP_EVIDENCE_AUDIT")
                   if stop.get("status") == "STOP_DOCKER_BACKEND_RUNNER_INVOCATION"
                   else ("PASS_TASK1_INDEPENDENT_AUDIT" if not failures
                         else "FAIL_TASK1_INDEPENDENT_AUDIT")),
        "failures": failures,
        "scope": "one task-1/layout-A/plain fixture task; not six-task acceptance",
        "source_files": manifest.get("source_file_count"),
        "seed": frozen.get("seed"),
        "fixture_submission_count": len(history),
        "exact_task1_submission_count": len(task_rows),
        "image_model_event_stream_count": len(event_paths),
        "ipc_receipt_counts": [len(requests), len(responses), len(brokers)],
        "verified_empty_release_count": len(releases),
        "verified_empty_owner_release_count": sum(1 for item in owner_releases
                                                   if item.get("verified") is True
                                                   and item.get("keys_down") == []
                                                   and item.get("buttons_down") == []),
        "full_six_task_fixture_success": whole.get("success"),
        "authority_granted": False,
        "registered_attempt_status": stop.get("status"),
        "acceptance_claim": False,
    }
    (RUN / "independent-audit.json").write_text(
        json.dumps(audit, indent=2, sort_keys=True) + "\n",
        encoding="utf-8", newline="\n")
    files = sorted(path for path in list(RUN.rglob("*")) + list(IPC.rglob("*"))
                   if path.is_file() and path.name != "SHA256SUMS")
    prompt_path = RUN / "model-calls/plain/task-1/anchor/prompt.txt"
    if prompt_path.is_file():
        prompt = prompt_path.read_text(encoding="utf-8")
        prompt_path.write_text(prompt.rstrip("\r\n ") + "\n",
                               encoding="utf-8", newline="\n")
    # Hash the canonical captured prompt bytes after newline/whitespace cleanup.
    files = sorted(path for path in list(RUN.rglob("*")) + list(IPC.rglob("*"))
                   if path.is_file() and path.name != "SHA256SUMS")
    sums = "".join(f"{sha(path)}  {path.relative_to(REPO)}\n" for path in files)
    (RUN / "SHA256SUMS").write_text(sums, encoding="utf-8", newline="\n")
    check = subprocess.run(["shasum", "-a", "256", "-c", "SHA256SUMS"],
                           cwd=REPO, capture_output=True, text=True, check=False)
    if check.returncode:
        (RUN / "checksum-audit.stderr.txt").write_text(check.stdout + check.stderr,
                                                        encoding="utf-8")
    return 1 if failures or check.returncode else 0


if __name__ == "__main__":
    raise SystemExit(main())
