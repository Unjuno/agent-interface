"""Independent offline audit of the retained single-task experiment bundle."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import subprocess

REPO = Path(__file__).resolve().parents[3]
BASE = REPO / "research/integration/issue_2849_task1_orbstack_smoke_v2/evidence"
RUN = BASE / "formal-task1-seed-284902"
IPC = BASE / "ipc"


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    manifest = read_json(RUN / "pre-call-source-manifest.json")
    failures = []
    if manifest.get("status") != "FROZEN_BEFORE_MODEL_CALL":
        failures.append("source_manifest_not_frozen")
    for entry in manifest.get("source_files", []):
        path = REPO / entry["path"]
        if not path.is_file() or sha(path) != entry["sha256"]:
            failures.append("source_hash_mismatch:" + entry["path"])
    frozen = read_json(RUN / "frozen-task.json")
    trace = read_json(RUN / "task-trace.json")
    scope = read_json(RUN / "task1-scope-result.json")
    fixture_eval = read_json(RUN / "six-task-fixture-evaluation.json")
    history = read_json(RUN / "submission-history.snapshot.json")
    detail = read_json(RUN / "task-detail.json")
    if (frozen.get("seed"), frozen.get("task_id"), frozen.get("layout"),
            frozen.get("phase"), frozen.get("route")) != (
            284902, "task-1", "A", "cold", "plain"):
        failures.append("frozen_task_scope_mismatch")
    task_rows = [row for row in history if row.get("task_id") == "task-1"]
    if len(history) != 1 or len(task_rows) != 1:
        failures.append("unexpected_or_duplicate_fixture_effect")
    elif not (task_rows[0].get("exact") is True
              and task_rows[0].get("expected_token") == frozen.get("token")
              and task_rows[0].get("submitted_values") == [frozen.get("token")]
              and task_rows[0].get("layout") == "A"):
        failures.append("independent_fixture_effect_mismatch")
    if not (trace.get("typed_outcome") == "completed"
            and trace.get("model_visible_images") == 1
            and len(trace.get("model_calls", [])) == 1
            and trace.get("submission_count") == 1
            and trace.get("exact_submission") is True
            and trace.get("releases_verified") is True):
        failures.append("runtime_trace_gate_mismatch")
    if scope.get("status") != "PASS_TASK1_SCOPED":
        failures.append("runner_scoped_result_not_pass")
    if detail.get("adaptive", {}).get("outcome") != "TASK_SUCCEEDED":
        failures.append("adaptive_task_outcome_not_success")
    if fixture_eval.get("success") is not False:
        failures.append("six_task_evaluator_boundary_unexpected")
    if fixture_eval.get("record_count") != 1:
        failures.append("six_task_evaluator_record_count_mismatch")

    requests = sorted(IPC.glob("*.request.json"))
    responses = sorted(IPC.glob("*.response.jsonl"))
    brokers = sorted(IPC.glob("*.broker.json"))
    if not (len(requests) == len(responses) == len(brokers) == 1):
        failures.append("ipc_request_response_broker_count_mismatch")
    model_event_paths = sorted(RUN.glob("model-calls/**/runner/events.jsonl"))
    if len(model_event_paths) != 1:
        failures.append("model_event_stream_count_mismatch")
    else:
        events_path = model_event_paths[0]
        event_rows = [json.loads(line) for line in
                      events_path.read_text(encoding="utf-8").splitlines() if line]
        messages = [row for row in event_rows if row.get("type") == "item.completed"
                    and row.get("item", {}).get("type") == "agent_message"]
        turns = [row for row in event_rows if row.get("type") == "turn.completed"]
        if len(messages) != 1 or len(turns) != 1:
            failures.append("assistant_message_or_completed_turn_count_mismatch")
        try:
            json.loads(messages[0]["item"]["text"])
        except (IndexError, KeyError, json.JSONDecodeError, TypeError):
            failures.append("assistant_json_invalid")
        receipt_path = events_path.parent / "process.json"
        accounting_path = events_path.parent / "event-accounting.json"
        if not receipt_path.is_file() or read_json(receipt_path).get("exit_code") != 0:
            failures.append("container_runner_receipt_not_success")
        if not accounting_path.is_file() or read_json(accounting_path).get("status") != "PASS":
            failures.append("event_accounting_not_pass")
        schema_path = events_path.parents[1] / "schema-validation.json"
        if not schema_path.is_file() or read_json(schema_path).get("status") != "PASS":
            failures.append("independent_schema_validation_not_pass")
    if requests and brokers:
        request = read_json(requests[0])
        broker = read_json(brokers[0])
        if request.get("authority_granted") is not False:
            failures.append("authority_not_false")
        if request.get("mode") != "coordinate" or not request.get("image_sha256"):
            failures.append("image_backed_request_shape_mismatch")
        if broker.get("returncode") != 0 or broker.get("authority_granted") is not False:
            failures.append("host_broker_not_success_or_authority_not_false")
    runtime_events = RUN / "runtime/events.jsonl"
    releases = []
    if runtime_events.is_file():
        for line in runtime_events.read_text(encoding="utf-8").splitlines():
            if line:
                row = json.loads(line)
                if row.get("event") == "terminal" and isinstance(row.get("release"), dict):
                    releases.append(row["release"])
        if not releases or any(not (r.get("verified") is True
                                    and r.get("keys_down") == []
                                    and r.get("buttons_down") == []) for r in releases):
            failures.append("raw_runtime_empty_release_not_verified")
    else:
        failures.append("raw_runtime_events_missing")

    audit = {
        "status": "PASS_TASK1_INDEPENDENT_AUDIT" if not failures
                  else "FAIL_TASK1_INDEPENDENT_AUDIT",
        "scope": "one task-1/layout-A/plain fixture path only",
        "failures": failures,
        "source_file_count": manifest.get("source_file_count"),
        "task_seed": frozen.get("seed"),
        "fixture_submission_count": len(history),
        "task1_exact_submission_count": len(task_rows),
        "image_model_event_stream_count": len(model_event_paths),
        "ipc_request_response_broker_counts": [len(requests), len(responses), len(brokers)],
        "raw_verified_empty_release_count": len(releases),
        "six_task_full_evaluation_success": fixture_eval.get("success"),
        "authority_granted": False,
    }
    (RUN / "independent-audit.json").write_text(
        json.dumps(audit, indent=2, sort_keys=True) + "\n",
        encoding="utf-8", newline="\n")
    if failures:
        return 1
    artifact_paths = sorted(p for p in list(RUN.rglob("*")) + list(IPC.rglob("*"))
                            if p.is_file() and p.name != "SHA256SUMS")
    sums = "".join(f"{sha(path)}  {path.relative_to(REPO)}\n"
                   for path in artifact_paths)
    (RUN / "SHA256SUMS").write_text(sums, encoding="utf-8", newline="\n")
    checked = subprocess.run(["shasum", "-a", "256", "-c", "SHA256SUMS"],
                             cwd=REPO, capture_output=True, text=True, check=False)
    if checked.returncode:
        (RUN / "checksum-audit.stderr.txt").write_text(
            checked.stdout + checked.stderr, encoding="utf-8")
        return checked.returncode
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
