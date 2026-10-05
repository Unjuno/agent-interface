"""Conservative status-aware summary of retained thread usage snapshots."""


def audit_usage(report, notifications):
    """Join usage notifications to planner turn status without inventing deltas."""
    decisions = report.get("decisions", [])
    ordered = []
    errors = []
    seen_turns = set()
    for decision in decisions:
        terminal = decision.get("final_action_admission", {}).get("planner_terminal", {})
        turn_id = terminal.get("turn_id")
        status = terminal.get("status")
        if not turn_id or turn_id in seen_turns:
            errors.append("missing_or_duplicate_report_turn_id")
            continue
        if status not in {"completed", "interrupted"}:
            errors.append("unsupported_turn_status:" + str(status))
        seen_turns.add(turn_id)
        ordered.append({"turn_id": turn_id, "status": status})

    usage_by_turn = {}
    for row in notifications:
        if row.get("method") != "thread/tokenUsage/updated":
            continue
        params = row.get("params", {})
        turn_id = params.get("turnId")
        if not turn_id or turn_id in usage_by_turn:
            errors.append("missing_or_duplicate_usage_turn_id")
            continue
        usage_by_turn[turn_id] = params.get("tokenUsage")

    if set(usage_by_turn) != seen_turns:
        errors.append("report_notification_turn_id_set_mismatch")

    totals = {"inputTokens": 0, "outputTokens": 0}
    summaries = []
    unknown_interrupted = []
    missing_completed = []
    previous_completed_usage = None
    for turn in ordered:
        turn_id = turn["turn_id"]
        status = turn["status"]
        usage = usage_by_turn.get(turn_id)
        last = usage.get("last") if isinstance(usage, dict) else None
        total = usage.get("total") if isinstance(usage, dict) else None
        valid_last = isinstance(last, dict) and all(
            type(last.get(field)) is int and last[field] >= 0
            for field in ("inputTokens", "outputTokens")
        )
        summary = {"turn_id": turn_id, "status": status, "last_snapshot": last, "total_snapshot": total}
        if status == "completed":
            if valid_last:
                for field in totals:
                    totals[field] += last[field]
                previous_completed_usage = usage
                summary["usage_treatment"] = "COMPLETED_TURN_LAST_SNAPSHOT_REPORTED"
            else:
                missing_completed.append(turn_id)
                summary["usage_treatment"] = "MISSING_OR_MALFORMED"
        elif status == "interrupted":
            unknown_interrupted.append(turn_id)
            repeated = bool(
                isinstance(previous_completed_usage, dict)
                and usage
                and usage.get("last") == previous_completed_usage.get("last")
                and usage.get("total") == previous_completed_usage.get("total")
            )
            summary["usage_treatment"] = "INTERRUPTED_INCREMENT_UNKNOWN"
            summary["snapshot_relation_to_prior_completed"] = (
                "EXACT_REPEAT" if repeated else "NOT_AN_EXACT_REPEAT_OR_NO_PRIOR_COMPLETED"
            )
        summaries.append(summary)

    if missing_completed:
        errors.append("completed_turn_usage_missing_or_malformed")
    return {
        "disposition": "PASS_STATUS_AWARE_RECORD_JOIN" if not errors else "HOLD_STATUS_AWARE_RECORD_JOIN",
        "errors": errors,
        "turn_usage": summaries,
        "completed_turn_last_snapshot_sum": totals,
        "unknown_interrupted_turns": unknown_interrupted,
        "interrupted_usage_interpretation": "UNKNOWN; repeated or changed snapshots do not establish an incremental amount",
        "usage_semantics": "Last and total snapshots are reported as retained fields, not asserted to be per-turn or per-response deltas.",
        "scope": "Raw notification/report identity and status join only; no billing, exact all-attempt cost, controller defect, causal benefit, or live control claim.",
    }
