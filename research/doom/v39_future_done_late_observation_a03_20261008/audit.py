"""Independent source, queue-order, and pre-executor-readiness auditor."""
import hashlib
import json
import subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent
FREEZE = json.loads((HERE / "FREEZE.json").read_text(encoding="utf-8"))


def repo_root():
    for parent in HERE.parents:
        if (parent / ".git").exists():
            return parent
    raise RuntimeError("repository root not found")


def verify_sources(repo=None):
    repo = Path(repo) if repo is not None else repo_root()
    for name, spec in FREEZE["sources"].items():
        data = subprocess.check_output(
            ["git", "-C", str(repo), "show",
             f"{FREEZE['main_commit']}:{spec['path']}"])
        blob = subprocess.check_output(
            ["git", "-C", str(repo), "rev-parse",
             f"{FREEZE['main_commit']}:{spec['path']}"], text=True).strip()
        if blob != spec["git_blob"] or hashlib.sha256(data).hexdigest() != spec["sha256"]:
            raise ValueError(f"frozen source identity mismatch: {name}")


def validate(result, raw, freeze=None, repo=None):
    freeze = FREEZE if freeze is None else freeze
    verify_sources(repo)
    if (result.get("schema") != "issue59-v39-future-done-late-observation-result-a03" or
            result.get("status") != "CONSTRUCTION_OBSERVATION" or
            result.get("main_commit") != freeze["main_commit"] or
            result.get("source_health") != 100 or result.get("late_health") != 70 or
            result.get("hard_minimum") != 80):
        raise ValueError("result identity or signal claim mismatch")
    events = result.get("events")
    if events != raw:
        raise ValueError("raw event stream mismatch")
    kinds = [row.get("event") for row in events]
    required = ["planner_future_poll", "queue_snapshot", "late_observation_enqueued",
                "terminal_dequeued", "planner_result_consumed",
                "action_admission_evaluated", "late_observation_dequeued",
                "monitor_received", "monitor_invalidated",
                "late_observation_processed_after_admission"]
    positions = []
    for kind in required:
        if kinds.count(kind) != 1:
            raise ValueError(f"expected exactly one {kind}")
        positions.append(kinds.index(kind))
    if positions != sorted(positions):
        raise ValueError("late observation/admission ordering mismatch")
    if events[kinds.index("queue_snapshot")].get("count") != 1:
        raise ValueError("queue snapshot precondition mismatch")
    if (events[kinds.index("action_admission_evaluated")].get("status") !=
            "READY_FOR_FRESH_EXECUTOR_ADMISSION" or
            events[kinds.index("action_admission_evaluated")].get(
                "current_health_value") != 100 or
            events[kinds.index("action_admission_evaluated")].get(
                "current_health_sequence") != 1):
        raise ValueError("stale-signal readiness claim mismatch")
    if (result.get("latest_used_for_action_admission") != {
            "sequence": 1, "health": 100} or
            result.get("late_monitor_invalidated") is not True or
            result.get("monitor_observed_sequences") != [2]):
        raise ValueError("late invalidation claim mismatch")
    admission = result.get("action_admission", {})
    if (admission.get("status") != "READY_FOR_FRESH_EXECUTOR_ADMISSION" or
            admission.get("input_authority_admitted") is not False or
            admission.get("grants_input_authority") is not False):
        raise ValueError("pre-executor readiness scope mismatch")
    if any(kind in ("executor_submit", "input_issued", "key_down") for kind in kinds):
        raise ValueError("candidate must not submit executor input")
    terminal = result.get("drain_result", {}).get("terminal_id")
    if terminal != "cover-0":
        raise ValueError("matching terminal was not drained")
    return True


def main():
    result_path = HERE / "RESULT.json"
    events_path = HERE / "events.jsonl"
    result = json.loads(result_path.read_text(encoding="utf-8"))
    raw = [json.loads(line) for line in events_path.read_text(encoding="utf-8").splitlines()]
    validate(result, raw)
    audit = {
        "schema": "issue59-v39-future-done-late-observation-audit-v1",
        "status": "PASS_STALE_READINESS_INTERLEAVING",
        "frozen_main": FREEZE["main_commit"],
        "event_rows": len(raw),
        "result_sha256": hashlib.sha256(result_path.read_bytes()).hexdigest(),
        "events_sha256": hashlib.sha256(events_path.read_bytes()).hexdigest(),
        "checks": {"frozen_sources": True,
                   "late_observation_remained_queued_through_action_check": True,
                   "production_action_helper_returned_pre_executor_ready": True,
                   "late_row_later_hard_invalidated": True,
                   "no_executor_submission_or_input": True},
    }
    path = HERE / "AUDIT.json"
    if path.exists():
        raise FileExistsError(f"refusing to overwrite {path}")
    path.write_text(json.dumps(audit, indent=2) + "\n", encoding="utf-8",
                    newline="\n")
    print(json.dumps(audit, separators=(",", ":")))


if __name__ == "__main__":
    main()
