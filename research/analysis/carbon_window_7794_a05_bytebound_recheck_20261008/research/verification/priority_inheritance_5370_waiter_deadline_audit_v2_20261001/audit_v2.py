"""Independent raw-only audit v2 for the frozen #5370 waiter-order trace.

This module deliberately does not import the candidate simulator.  Stale
abstentions occupy one logical service tick even though audit-v1's raw schema
does not emit them as entries in ``schedule``.
"""
import json
import sys


ALLOCATION = "G5370-PRIORITY-INHERITANCE-T5-20261001-01"
BASE_MAIN = "1b561c2978f020ff784480880ac8e7c908ddadfe"

# completed rows: (id, finish, deadline); stale rows: (id, observed_at, deadline)
EXPECTED = {
    ("deadline_order_conflict", False, "fifo"): {
        "completed": [], "stale": [("H1", 7, 5), ("H2", 8, 3)],
        "release": 7, "owner_ticks": 0, "max_priority": 1,
    },
    ("deadline_order_conflict", True, "fifo"): {
        "completed": [("H1", 3, 5)], "stale": [("H2", 3, 3)],
        "release": 2, "owner_ticks": 2, "max_priority": 4,
    },
    ("deadline_order_conflict", True, "edf"): {
        "completed": [("H2", 3, 3), ("H1", 4, 5)], "stale": [],
        "release": 2, "owner_ticks": 2, "max_priority": 4,
    },
    ("equal_deadline_control", False, "fifo"): {
        "completed": [], "stale": [("H1", 7, 4), ("H2", 8, 4)],
        "release": 7, "owner_ticks": 0, "max_priority": 1,
    },
    ("equal_deadline_control", True, "fifo"): {
        "completed": [("H1", 3, 4), ("H2", 4, 4)], "stale": [],
        "release": 2, "owner_ticks": 2, "max_priority": 4,
    },
    ("equal_deadline_control", True, "edf"): {
        "completed": [("H1", 3, 4), ("H2", 4, 4)], "stale": [],
        "release": 2, "owner_ticks": 2, "max_priority": 4,
    },
    ("forged_urgency_control", True, "edf"): {
        "completed": [("H1", 3, 5)], "stale": [],
        "release": 2, "owner_ticks": 2, "max_priority": 3,
    },
}


def _ids(rows):
    return [item.get("id") for item in rows]


def audit(raw):
    errors = []
    if not isinstance(raw, dict):
        return {"status": "FAIL", "errors": ["raw_not_object"]}
    if raw.get("allocation") != ALLOCATION:
        errors.append("allocation_mismatch")
    if raw.get("base_main") != BASE_MAIN:
        errors.append("base_main_mismatch")
    rows = raw.get("rows")
    if not isinstance(rows, list) or len(rows) != len(EXPECTED):
        return {"status": "FAIL", "errors": errors + ["row_count_mismatch"]}

    observed = set()
    for row in rows:
        if not isinstance(row, dict):
            errors.append("row_not_object")
            continue
        policy = row.get("policy")
        if not isinstance(policy, dict) or type(policy.get("inheritance")) is not bool:
            errors.append("policy_malformed")
            continue
        key = (row.get("case"), policy["inheritance"], policy.get("waiter_order"))
        if key not in EXPECTED or key in observed:
            errors.append("unexpected_or_duplicate_policy_row")
            continue
        observed.add(key)
        exp = EXPECTED[key]
        completed = row.get("completed_before_deadline")
        stale = row.get("stale_abstentions")
        schedule = row.get("schedule")
        rejected = row.get("rejected_unauthenticated")
        if not all(isinstance(x, list) for x in (completed, stale, schedule, rejected)):
            errors.append(f"row_lists_malformed:{key}")
            continue

        try:
            got_completed = [(x["id"], x["finish"], x["deadline"]) for x in completed]
            got_stale = [(x["id"], x["observed_at"], x["deadline"]) for x in stale]
        except (KeyError, TypeError):
            errors.append(f"outcome_fields_malformed:{key}")
            continue
        if got_completed != exp["completed"] or got_stale != exp["stale"]:
            errors.append(f"outcome_mismatch:{key}")
        if any(type(x[1]) is not int or type(x[2]) is not int or x[1] > x[2]
               for x in got_completed):
            errors.append(f"late_or_malformed_completion:{key}")
        if any(x.get("reason") != "STALE_ABSTAIN" for x in stale):
            errors.append(f"stale_not_abstained:{key}")

        expected_rejected = ([{"id": "H2", "reason": "UNAUTHENTICATED_URGENCY"}]
                             if key[0] == "forged_urgency_control" else [])
        if rejected != expected_rejected:
            errors.append(f"unauthenticated_request_not_rejected:{key}")
        admitted_ids = _ids(completed) + _ids(stale) + _ids(rejected)
        expected_ids = (["H1", "H2"] if key[0] != "forged_urgency_control" else ["H1", "H2"])
        if sorted(admitted_ids) != sorted(expected_ids) or len(admitted_ids) != len(set(admitted_ids)):
            errors.append(f"request_accounting_mismatch:{key}")

        # Completed work is represented by a schedule event at finish-1.
        # A stale abstention consumes that same one-tick slot but is represented
        # only by observed_at in v1 raw; include it while reconstructing time.
        slots = {}
        for event in schedule:
            if not isinstance(event, dict) or type(event.get("tick")) is not int:
                errors.append(f"schedule_event_malformed:{key}")
                continue
            tick, run = event["tick"], event.get("run")
            if tick < 0 or run not in {"L", "M", "H1", "H2"} or tick in slots:
                errors.append(f"schedule_event_invalid_or_duplicate:{key}")
                continue
            slots[tick] = run
        for item in completed:
            tick = item.get("finish", -1) - 1
            if slots.get(tick) != item.get("id"):
                errors.append(f"completion_missing_schedule_slot:{key}")
        for item in stale:
            tick = item.get("observed_at")
            if type(tick) is not int or tick in slots:
                errors.append(f"stale_slot_missing_or_overlaps_schedule:{key}")
            else:
                slots[tick] = "STALE_ABSTAIN"
        if slots and sorted(slots) != list(range(max(slots) + 1)):
            errors.append(f"logical_timeline_gap_or_duplicate:{key}")
        if sum(run == "L" for run in slots.values()) != 2:
            errors.append(f"holder_work_mismatch:{key}")
        if sum(run == "M" for run in slots.values()) != 5:
            errors.append(f"medium_service_mismatch:{key}")
        holder_ticks = [tick for tick, run in slots.items() if run == "L"]
        if type(row.get("holder_release")) is not int or row["holder_release"] != exp["release"]:
            errors.append(f"holder_release_mismatch:{key}")
        if holder_ticks and max(holder_ticks) + 1 != row.get("holder_release"):
            errors.append(f"holder_release_not_reconciled:{key}")
        if row.get("inherited_owner_ticks") != exp["owner_ticks"] or row.get("inherited_owner_ticks", 0) > 2:
            errors.append(f"inheritance_budget_or_count_mismatch:{key}")
        if row.get("max_inherited_priority") != exp["max_priority"]:
            errors.append(f"effective_priority_mismatch:{key}")

    if observed != set(EXPECTED):
        errors.append("policy_coverage_mismatch")

    # Paired-policy controls: only waiter order differs in the primary inherited
    # comparison; equal deadlines retain stable FIFO-compatible completion.
    by_key = {(r.get("case"), r.get("policy", {}).get("inheritance"),
               r.get("policy", {}).get("waiter_order")): r for r in rows
              if isinstance(r, dict) and isinstance(r.get("policy"), dict)}
    fifo = by_key.get(("deadline_order_conflict", True, "fifo"), {})
    edf = by_key.get(("deadline_order_conflict", True, "edf"), {})
    if fifo.get("holder_release") != edf.get("holder_release") or fifo.get("medium_service") != edf.get("medium_service"):
        errors.append("primary_pair_resource_trace_mismatch")
    if by_key.get(("equal_deadline_control", True, "fifo"), {}).get("completed_before_deadline") != by_key.get(("equal_deadline_control", True, "edf"), {}).get("completed_before_deadline"):
        errors.append("equal_deadline_order_not_stable")

    return {"status": "PASS" if not errors else "FAIL", "errors": errors,
            "audited_rows": len(rows)}


if __name__ == "__main__":
    try:
        result = audit(json.load(sys.stdin))
    except Exception as exc:  # raw evidence is untrusted
        result = {"status": "FAIL", "errors": [f"raw_parse_error:{type(exc).__name__}"]}
    print(json.dumps(result, sort_keys=True, separators=(",", ":")))
    raise SystemExit(0 if result["status"] == "PASS" else 1)

