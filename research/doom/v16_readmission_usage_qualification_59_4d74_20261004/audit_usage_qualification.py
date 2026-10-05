"""Status-aware qualification of retained V16 turn-usage snapshots.

The app-server thread/tokenUsage/updated payload is a snapshot. Its turn ID
routes the notification; it does not turn `last` into a per-turn delta or a
complete response-level usage record.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


PACKAGE = Path(__file__).resolve().parent
REPO = PACKAGE.parents[2]
RUN = REPO / "research/doom/v16_visual_readmission_59_4d74_20261004/run"
RESPONSE_USAGE_KEYS = {
    "tokenusagerecord",
    "turntokenusage",
    "turn_token_usage",
    "responsetokenusage",
    "response_token_usage",
}


def read_jsonl(path: Path) -> list[dict]:
    rows = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError as error:
            raise ValueError(f"invalid JSONL at {path}:{line_number}: {error}") from error
        if not isinstance(row, dict):
            raise ValueError(f"expected JSON object at {path}:{line_number}")
        rows.append(row)
    return rows


def _usage_notification_rows(host_rows: list[dict], thread_ids: set[str]):
    notifications = {}
    foreign_count = 0
    unmatched_turn_ids = []
    malformed_count = 0
    for row in host_rows:
        if row.get("method") != "thread/tokenUsage/updated":
            continue
        params = row.get("params")
        if not isinstance(params, dict):
            malformed_count += 1
            continue
        thread_id = params.get("threadId")
        turn_id = params.get("turnId")
        usage = params.get("tokenUsage")
        if not isinstance(thread_id, str) or not thread_id:
            malformed_count += 1
            continue
        if thread_ids and thread_id not in thread_ids:
            foreign_count += 1
            continue
        if not isinstance(turn_id, str) or not turn_id or not isinstance(usage, dict):
            if isinstance(turn_id, str) and turn_id:
                unmatched_turn_ids.append(turn_id)
            malformed_count += 1
            continue
        notifications.setdefault(turn_id, []).append(usage)
    return notifications, foreign_count, unmatched_turn_ids, malformed_count


def _sum_last_snapshot(turns: list[dict], statuses: set[str]):
    values = []
    missing = []
    input_total = output_total = 0
    for turn in turns:
        if turn["status"] not in statuses:
            continue
        snapshot = turn.get("latest_notification")
        last = snapshot.get("last") if isinstance(snapshot, dict) else None
        if not isinstance(last, dict):
            missing.append(turn["turn_id"])
            continue
        input_tokens, output_tokens = last.get("inputTokens"), last.get("outputTokens")
        if (not isinstance(input_tokens, int) or isinstance(input_tokens, bool) or
                not isinstance(output_tokens, int) or isinstance(output_tokens, bool)):
            missing.append(turn["turn_id"])
            continue
        input_total += input_tokens
        output_total += output_tokens
        values.append(turn["turn_id"])
    total = {"inputTokens": input_total, "outputTokens": output_total} if values else None
    return total, missing, values


def qualify_usage(report: dict, host_rows: list[dict], *,
                  response_level_usage_record_count: int) -> dict:
    decisions = report.get("decisions")
    if not isinstance(decisions, list):
        raise ValueError("report decisions must be a list")
    raw_thread_ids = report.get("model_session_ids", [])
    thread_ids = {value for value in raw_thread_ids if isinstance(value, str) and value}
    (notifications, foreign_count, unmatched_notifications,
     malformed_notification_count) = _usage_notification_rows(host_rows, thread_ids)

    turns = []
    seen_turn_ids = set()
    mismatch_ids = []
    missing_ids = []
    duplicate_ids = []
    previous_completed_snapshot = None
    for decision in decisions:
        admission = decision.get("final_action_admission")
        terminal = admission.get("planner_terminal") if isinstance(admission, dict) else None
        if not isinstance(terminal, dict):
            raise ValueError("decision is missing final-action planner terminal")
        turn_id = terminal.get("turn_id")
        status = terminal.get("status")
        if not isinstance(turn_id, str) or not turn_id:
            raise ValueError("planner terminal is missing turn_id")
        if turn_id in seen_turn_ids:
            duplicate_ids.append(turn_id)
        seen_turn_ids.add(turn_id)

        snapshots = notifications.get(turn_id, [])
        latest = snapshots[-1] if snapshots else None
        report_usage = decision.get("usage")
        if latest is None:
            missing_ids.append(turn_id)
            consistency = "MISSING_NOTIFICATION"
        elif not isinstance(report_usage, dict):
            mismatch_ids.append(turn_id)
            consistency = "REPORT_USAGE_MISSING"
        elif report_usage != latest:
            mismatch_ids.append(turn_id)
            consistency = "MISMATCH"
        else:
            consistency = "MATCH"

        repeats_previous = None
        if status == "interrupted" and previous_completed_snapshot is not None:
            repeats_previous = latest == previous_completed_snapshot
        turn = {
            "iteration": decision.get("iteration"),
            "turn_id": turn_id,
            "status": status,
            "notification_count": len(snapshots),
            "latest_notification": latest,
            "report_usage_matches_latest_notification": consistency == "MATCH",
            "snapshot_consistency": consistency,
            "snapshot_repeats_previous_completed": repeats_previous,
        }
        turns.append(turn)
        if status == "completed" and latest is not None:
            previous_completed_snapshot = latest

    completed_sum, completed_missing, completed_included = _sum_last_snapshot(
        turns, {"completed"})
    report_turn_ids = {turn["turn_id"] for turn in turns}
    orphan_notification_turn_ids = sorted(set(notifications) - report_turn_ids)
    interrupted_ids = [turn["turn_id"] for turn in turns
                       if turn["status"] == "interrupted"]
    unknown_status_ids = [turn["turn_id"] for turn in turns
                          if turn["status"] not in {"completed", "interrupted"}]
    if (mismatch_ids or duplicate_ids or unmatched_notifications or
            malformed_notification_count or orphan_notification_turn_ids):
        disposition = "HOLD_USAGE_SNAPSHOT_MISMATCH"
        consistency_status = "MISMATCH"
    elif missing_ids or completed_missing or unknown_status_ids:
        disposition = "HOLD_USAGE_SNAPSHOT_INCOMPLETE"
        consistency_status = "INCOMPLETE"
    else:
        disposition = "PASS_SNAPSHOT_RECONCILIATION; HOLD_FULL_USAGE_INTERPRETATION"
        consistency_status = "PASS"

    return {
        "disposition": disposition,
        "scope": ("turn-identified thread/tokenUsage/updated snapshots only; no claim that "
                  "`last` is a per-turn delta or complete response-level usage"),
        "report_snapshot_consistency": consistency_status,
        "thread_ids": sorted(thread_ids),
        "usage_notification_count": sum(len(values) for values in notifications.values()),
        "foreign_thread_notification_count": foreign_count,
        "malformed_usage_notification_count": malformed_notification_count,
        "unmatched_notification_turn_ids": unmatched_notifications,
        "orphan_notification_turn_ids": orphan_notification_turn_ids,
        "duplicate_report_turn_ids": duplicate_ids,
        "snapshot_mismatch_turn_ids": mismatch_ids,
        "missing_snapshot_turn_ids": missing_ids,
        "unknown_status_turn_ids": unknown_status_ids,
        "turns": turns,
        "completed_turn_last_snapshot_sum": completed_sum,
        "completed_turn_last_snapshot_sum_scope": "observed last snapshots, not total token consumption",
        "completed_turn_ids_in_snapshot_sum": completed_included,
        "completed_turn_ids_missing_last_snapshot": completed_missing,
        "interrupted_turn_ids": interrupted_ids,
        "interrupted_incremental_usage": "UNKNOWN" if interrupted_ids else "NO_INTERRUPTED_TURNS",
        "response_level_usage_record_count": response_level_usage_record_count,
        "full_attempt_usage": "NOT_ESTABLISHED",
        "limits": [
            "turn IDs route notifications but do not define the semantics of `last`",
            "repeated interrupted snapshots do not prove zero incremental cost",
            "thread total/last snapshots are not response-level usage records",
            "this audit makes no claim about billing",
        ],
    }


def _count_response_level_usage_records(value) -> int:
    if isinstance(value, dict):
        normalized_keys = {key.replace("_", "").lower()
                           for key in value if isinstance(key, str)}
        if any(key.replace("_", "").lower() in normalized_keys
               for key in RESPONSE_USAGE_KEYS):
            return 1
        if any(isinstance(item, str) and
               item.replace("_", "").lower() == "tokenusagerecord"
               for key, item in value.items()
               if key in {"type", "schema", "kind", "event"}):
            return 1
        return sum(_count_response_level_usage_records(child)
                   for child in value.values())
    if isinstance(value, list):
        return sum(_count_response_level_usage_records(child) for child in value)
    return 0


def count_response_level_usage_records(run_root: Path) -> int:
    """Count explicit response-level usage records in retained JSON artifacts."""
    count = 0
    paths = sorted([*run_root.rglob("*.json"), *run_root.rglob("*.jsonl")])
    for path in paths:
        if path.name == "SAVED_READMISSION_AUDIT.json":
            continue
        try:
            if path.suffix == ".jsonl":
                values = read_jsonl(path)
            else:
                values = [json.loads(path.read_text(encoding="utf-8"))]
        except (UnicodeDecodeError, json.JSONDecodeError, ValueError):
            continue
        count += sum(_count_response_level_usage_records(value) for value in values)
    return count


def audit_archive(run_root: Path = RUN) -> dict:
    freeze = json.loads((PACKAGE / "FREEZE.json").read_text(encoding="utf-8"))
    frozen_files = []
    for relative, expected in freeze["input_sha256"].items():
        path = REPO / relative
        actual = hashlib.sha256(path.read_bytes()).hexdigest()
        frozen_files.append({"path": relative, "sha256": actual,
                             "matches_freeze": actual == expected})
    if any(not item["matches_freeze"] for item in frozen_files):
        raise ValueError("one or more frozen archive inputs differ from FREEZE.json")

    report = json.loads((run_root / "episode/report.json").read_text(encoding="utf-8"))
    host_rows = read_jsonl(run_root / "host.stdout.jsonl")
    response_record_count = count_response_level_usage_records(run_root)
    result = qualify_usage(
        report, host_rows,
        response_level_usage_record_count=response_record_count)
    result["frozen_input_verification"] = {
        "status": "PASS",
        "source_commit": freeze["source_commit"],
        "files": frozen_files,
    }

    first_audit_path = run_root / "SAVED_READMISSION_AUDIT.json"
    if first_audit_path.is_file():
        first = json.loads(first_audit_path.read_text(encoding="utf-8"))
        result["preserved_first_audit"] = {
            "path": str(first_audit_path),
            "original_claimed_sum": {
                "input": first.get("known_completed_input"),
                "output": first.get("known_completed_output"),
            },
            "note": "preserved historical output; not reused as qualified usage",
        }
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-root", type=Path, default=RUN)
    parser.add_argument("--out", type=Path, default=PACKAGE / "QUALIFIED_USAGE.json")
    args = parser.parse_args()
    result = audit_archive(args.run_root)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "disposition": result["disposition"],
        "completed_turn_last_snapshot_sum": result["completed_turn_last_snapshot_sum"],
        "interrupted_turn_ids": result["interrupted_turn_ids"],
        "interrupted_incremental_usage": result["interrupted_incremental_usage"],
        "response_level_usage_record_count": result["response_level_usage_record_count"],
        "full_attempt_usage": result["full_attempt_usage"],
        "out": str(args.out),
    }, sort_keys=True))


if __name__ == "__main__":
    main()
