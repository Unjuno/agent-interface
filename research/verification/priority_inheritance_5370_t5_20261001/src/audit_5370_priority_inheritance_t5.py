"""Independent raw-only oracle for Issue #5370 T5; candidate is not imported."""
import json
import sys


EXPECTED = {
    ("deadline_order_conflict", False, "fifo"): ({}, {"H1", "H2"}),
    ("deadline_order_conflict", True, "fifo"): ({"H1"}, {"H2"}),
    ("deadline_order_conflict", True, "edf"): ({"H1", "H2"}, set()),
    ("equal_deadline_control", False, "fifo"): ({}, {"H1", "H2"}),
    ("equal_deadline_control", True, "fifo"): ({"H1", "H2"}, set()),
    ("equal_deadline_control", True, "edf"): ({"H1", "H2"}, set()),
    ("forged_urgency_control", True, "edf"): ({"H1"}, set()),
}


def audit(raw):
    errors = []
    if raw.get("allocation") != "G5370-PRIORITY-INHERITANCE-T5-20261001-01":
        errors.append("allocation_mismatch")
    if raw.get("base_main") != "1b561c2978f020ff784480880ac8e7c908ddadfe":
        errors.append("base_main_mismatch")
    rows = raw.get("rows")
    if not isinstance(rows, list) or len(rows) != len(EXPECTED):
        return {"status": "FAIL", "errors": errors + ["row_count_mismatch"]}

    observed = set()
    for row in rows:
        policy = row.get("policy", {})
        key = (row.get("case"), policy.get("inheritance"), policy.get("waiter_order"))
        if key in observed or key not in EXPECTED:
            errors.append("unexpected_or_duplicate_policy_row")
            continue
        observed.add(key)
        expected_completed, expected_stale = EXPECTED[key]
        completed = row.get("completed_before_deadline", [])
        stale = row.get("stale_abstentions", [])
        completed_ids = {item.get("id") for item in completed}
        stale_ids = {item.get("id") for item in stale}
        if completed_ids != expected_completed or stale_ids != expected_stale:
            errors.append(f"outcome_mismatch:{key}")
        if any(type(item.get("finish")) is not int or item["finish"] > item.get("deadline", -1) for item in completed):
            errors.append(f"late_admission:{key}")
        if any(item.get("reason") != "STALE_ABSTAIN" for item in stale):
            errors.append(f"stale_not_abstained:{key}")
        if row.get("inherited_owner_ticks", 0) > 2:
            errors.append(f"inheritance_budget_exceeded:{key}")
        ticks = [event.get("tick") for event in row.get("schedule", [])]
        if ticks != list(range(len(ticks))):
            errors.append(f"schedule_gap_or_duplicate:{key}")
        if sum(event.get("run") == "L" for event in row.get("schedule", [])) != 2:
            errors.append(f"holder_work_mismatch:{key}")

    if observed != set(EXPECTED):
        errors.append("policy_coverage_mismatch")

    forged = next((r for r in rows if r.get("case") == "forged_urgency_control"), {})
    if forged.get("max_inherited_priority") != 3:
        errors.append("unauthenticated_priority_influenced_owner")
    if forged.get("rejected_unauthenticated") != [{"id": "H2", "reason": "UNAUTHENTICATED_URGENCY"}]:
        errors.append("unauthenticated_request_not_rejected")

    return {"status": "PASS" if not errors else "FAIL", "errors": errors, "audited_rows": len(rows)}


if __name__ == "__main__":
    try:
        result = audit(json.load(sys.stdin))
    except Exception as exc:  # diagnostic only; input is untrusted raw evidence
        result = {"status": "FAIL", "errors": [f"raw_parse_error:{type(exc).__name__}"]}
    print(json.dumps(result, sort_keys=True, separators=(",", ":")))
    raise SystemExit(0 if result["status"] == "PASS" else 1)
