"""Independent raw-only oracle for the four frozen T6 simulation rows."""
import json
from pathlib import Path


EXPECTED = [
    ("transitive", "no_inheritance", "deadline_missed", None, 0, 0, None),
    ("transitive", "inheritance_only", "completed", 6, 2, 2, None),
    ("transitive", "inheritance_plus_aging", "completed", 6, 2, 2, 6),
    ("cancelled", "inheritance_only", "cancelled", 2, 1, 0, None),
]


def audit_rows(rows):
    errors = []
    if not isinstance(rows, list) or len(rows) != len(EXPECTED):
        return ["row_count_mismatch"]
    observed_ids = [(r.get("case"), r.get("policy")) for r in rows if isinstance(r, dict)]
    if observed_ids != [(e[0], e[1]) for e in EXPECTED]:
        errors.append("row_identity_or_order_mismatch")

    for row, exp in zip(rows, EXPECTED):
        case, policy, status, at, a_done, b_done, first_u = exp
        if not isinstance(row, dict):
            errors.append("row_not_object")
            continue
        if row.get("horizon") != 20:
            errors.append(f"horizon_mismatch:{policy}")
        schedule = row.get("schedule")
        if not isinstance(schedule, list) or len(schedule) != 20:
            errors.append(f"schedule_length:{policy}")
            continue
        if [s.get("tick") for s in schedule] != list(range(20)):
            errors.append(f"tick_gap_or_duplicate:{policy}")
        if any(s.get("job") not in {"A", "B", "H", "M", "U"} for s in schedule):
            errors.append(f"unknown_job:{policy}")
        if row.get("case") != case or row.get("policy") != policy:
            errors.append(f"identity_mismatch:{policy}")
        if row.get("owners") != {"A": a_done, "B": b_done}:
            errors.append(f"owner_work_mismatch:{policy}")
        if row.get("verifier") != {"status": status, "at": at}:
            errors.append(f"verifier_outcome_mismatch:{policy}")
        if row.get("first_background_service") != first_u:
            errors.append(f"background_service_mismatch:{policy}")

        jobs = [s.get("job") for s in schedule]
        if policy == "no_inheritance" and jobs != ["M"] * 20:
            errors.append("deadline_only_schedule_mismatch")
        elif policy == "inheritance_only":
            if case == "transitive" and jobs[:6] != ["M", "A", "A", "B", "B", "H"]:
                errors.append("transitive_chain_order_mismatch")
            if case == "transitive" and "U" in jobs:
                errors.append("inheritance_only_background_expected_starvation")
            if case == "cancelled" and jobs[:3] != ["M", "A", "M"]:
                errors.append("cancel_revocation_order_mismatch")
            if case == "cancelled" and any(j in {"A", "B", "H"} for j in jobs[2:]):
                errors.append("cancelled_work_resumed_without_waiter")
        elif policy == "inheritance_plus_aging":
            if jobs[:7] != ["M", "A", "A", "B", "B", "H", "U"]:
                errors.append("aging_policy_critical_prefix_mismatch")
            u_ticks = [s["tick"] for s in schedule if s["job"] == "U"]
            m_ticks_after_first_u = [s["tick"] for s in schedule
                                     if s["job"] == "M" and first_u is not None and s["tick"] > first_u]
            if not u_ticks or any(b - a > 3 for a, b in zip(u_ticks, u_ticks[1:])):
                errors.append("background_wait_bound_exceeded")
            if not m_ticks_after_first_u:
                errors.append("medium_starvation_after_aging")
            if row.get("max_background_wait") != 6:
                errors.append("aging_max_wait_mismatch")
    return errors


def main():
    raw_path = Path(__file__).with_name("raw.json")
    rows = json.loads(raw_path.read_text(encoding="utf-8"))
    errors = audit_rows(rows)
    print(json.dumps({"rows": len(rows), "errors": errors,
                      "result": "PASS_AUDIT_V1_SCOPED" if not errors else "STOP_AUDIT"},
                     sort_keys=True))
    raise SystemExit(0 if not errors else 1)


if __name__ == "__main__":
    main()
