#!/usr/bin/env python3
"""Independent raw-only audit; intentionally does not import usage_audit.py."""

import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[3]
SOURCE = REPO / "research/doom/v16_visual_readmission_59_4d74_20261004"
RUN = HERE / "out/a01"


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def audit():
    freeze = read_json(HERE / "FREEZE.json")
    for relative, expected in freeze["raw_files"].items():
        raw = (SOURCE / relative).read_bytes()
        if len(raw) != expected["bytes"] or hashlib.sha256(raw).hexdigest() != expected["sha256"]:
            raise AssertionError("pinned_raw_file_mismatch:" + relative)

    report = read_json(SOURCE / "run/episode/report.json")
    host_rows = [json.loads(line) for line in (SOURCE / "run/host.stdout.jsonl").read_text(encoding="utf-8").splitlines() if line]
    notifications = {}
    for row in host_rows:
        if row.get("method") == "thread/tokenUsage/updated":
            turn_id = row.get("params", {}).get("turnId")
            if not turn_id or turn_id in notifications:
                raise AssertionError("missing_or_duplicate_raw_turn_notification")
            notifications[turn_id] = row["params"]["tokenUsage"]

    completed_sum = {"inputTokens": 0, "outputTokens": 0}
    completed_ids = []
    interrupted = []
    prior_completed = None
    report_ids = []
    for decision in report["decisions"]:
        terminal = decision["final_action_admission"]["planner_terminal"]
        turn_id = terminal["turn_id"]
        status = terminal["status"]
        report_ids.append(turn_id)
        usage = notifications.get(turn_id)
        if usage is None:
            raise AssertionError("report_turn_has_no_raw_usage_notification")
        if status == "completed":
            last = usage["last"]
            completed_sum["inputTokens"] += last["inputTokens"]
            completed_sum["outputTokens"] += last["outputTokens"]
            completed_ids.append(turn_id)
            prior_completed = usage
        elif status == "interrupted":
            exact_repeat = bool(prior_completed and usage["last"] == prior_completed["last"]
                                and usage["total"] == prior_completed["total"])
            interrupted.append({"turn_id": turn_id, "increment": "UNKNOWN", "exact_repeat": exact_repeat})
        else:
            raise AssertionError("unsupported_report_turn_status:" + str(status))
    if len(report_ids) != len(set(report_ids)) or set(report_ids) != set(notifications):
        raise AssertionError("report_raw_notification_identity_mismatch")
    if len(completed_ids) != 4 or len(interrupted) != 2:
        raise AssertionError("unexpected_status_counts")
    if completed_sum != {"inputTokens": 48773, "outputTokens": 1100}:
        raise AssertionError("completed_snapshot_sum_mismatch")
    if [item["exact_repeat"] for item in interrupted] != [True, True]:
        raise AssertionError("interrupted_repeat_relation_mismatch")

    qualification = read_json(SOURCE / "run/USAGE_QUALIFICATION.json")
    original_audit = read_json(SOURCE / "run/SAVED_READMISSION_AUDIT.json")
    if qualification["first_auditor_raw_preserved"] != "SAVED_READMISSION_AUDIT.json":
        raise AssertionError("original_audit_not_preserved")
    if original_audit["known_completed_input"] != 71597 or original_audit["known_completed_output"] != 1724:
        raise AssertionError("original_audit_snapshot_changed_or_wrong")
    if qualification["four_completed_turn_last_sum"] != {"input": 48773, "output": 1100}:
        raise AssertionError("qualification_completed_snapshot_mismatch")
    if qualification["interrupted_turn_increment"] != "UNKNOWN; neither repeated last nor unchanged cumulative proves actual zero cost":
        raise AssertionError("qualification_interrupted_scope_mismatch")

    result = read_json(RUN / "RESULT.json")
    if result["disposition"] != "PASS_STATUS_AWARE_RECORD_JOIN":
        raise AssertionError("candidate_result_not_pass")
    if result["completed_turn_last_snapshot_sum"] != completed_sum:
        raise AssertionError("candidate_completed_sum_mismatch")
    if result["unknown_interrupted_turns"] != [row["turn_id"] for row in interrupted]:
        raise AssertionError("candidate_interrupted_status_mismatch")
    if result["interrupted_usage_interpretation"].split(";")[0] != "UNKNOWN":
        raise AssertionError("candidate_promoted_interrupted_usage")
    return {
        "audit": "PASS_SCOPED_STATUS_AWARE_USAGE_RECONSTRUCTION",
        "errors": [],
        "report_turns": len(report_ids),
        "completed_turns": len(completed_ids),
        "completed_turn_last_snapshot_sum": completed_sum,
        "interrupted_turns": interrupted,
        "original_first_audit_preserved": True,
        "scope": "Retained usage snapshots only; no total-cost, billing, controller-defect, or live-control claim.",
    }


if __name__ == "__main__":
    output = audit()
    print(json.dumps(output, indent=2, sort_keys=True))
    (RUN / "AUDIT.json").write_text(json.dumps(output, indent=2, sort_keys=True) + "\n", encoding="utf-8")
