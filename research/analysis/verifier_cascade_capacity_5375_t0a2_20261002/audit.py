"""Independent raw-only conservation and policy audit; imports no candidate code."""
import json
import sys


def audit(fixture, raw_rows):
    errors = []
    cases = {case["id"]: case for case in fixture["cases"]}
    expected_keys = {(case["id"], policy) for case in fixture["cases"] for policy in fixture["policies"]}
    grouped = {}
    for row in raw_rows:
        key = (row.get("case"), row.get("policy"))
        grouped.setdefault(key, []).append(row)
        if key not in expected_keys:
            errors.append("unexpected_group:" + repr(key))
    if set(grouped) != expected_keys:
        errors.append("group_set")

    capacity = fixture["total_capacity_per_tick"]
    for key in sorted(expected_keys):
        rows = grouped.get(key, [])
        if len(rows) != fixture["ticks"]:
            errors.append("row_count:" + repr(key))
        prior = {"primary": 0, "retry": 0, "safety": 0}
        case = cases[key[0]]
        policy = key[1]
        for tick, row in enumerate(rows):
            tag = f"{key[0]}/{policy}/{tick}"
            fault = tick < case["fault_ticks"]
            if row.get("tick") != tick or row.get("fault_active") != fault:
                errors.append("chronology:" + tag)
            if row.get("total_capacity") != capacity:
                errors.append("capacity_id:" + tag)
            if row.get("authority_admissions") != 0:
                errors.append("authority:" + tag)

            fields = ("primary_before", "retry_before", "safety_before")
            for queue, field in zip(("primary", "retry", "safety"), fields):
                if row.get(field) != prior[queue]:
                    errors.append("queue_continuity:" + tag + ":" + queue)
            if row.get("external_primary_arrival") != case["external_primary_per_tick"]:
                errors.append("primary_schedule:" + tag)
            if row.get("safety_arrival") != fixture["safety_arrival_per_tick"]:
                errors.append("safety_schedule:" + tag)
            expected_trigger = fixture["trigger_retry_arrival_per_fault_tick"] if fault else 0
            if row.get("trigger_retry_arrival") != expected_trigger:
                errors.append("trigger_schedule:" + tag)

            expected_feedback = 0
            if (not fault and policy == "legacy_shared_retry" and case["feedback_after_trigger"]
                    and prior["retry"] > 0):
                expected_feedback = fixture["feedback_retry_arrival_per_tick"]
            if row.get("feedback_retry_arrival") != expected_feedback:
                errors.append("feedback_schedule:" + tag)

            expected_drop = prior["retry"] if policy == "debt_shed_reserved" and tick == case["fault_ticks"] else 0
            if row.get("retry_dropped") != expected_drop:
                errors.append("retry_shedding:" + tag)
            p_available = prior["primary"] + case["external_primary_per_tick"]
            r_available = (prior["retry"] + expected_trigger + expected_feedback - expected_drop)
            s_available = prior["safety"] + fixture["safety_arrival_per_tick"]
            ps = row.get("primary_service", -1)
            rs = row.get("retry_service", -1)
            ss = row.get("safety_service", -1)
            failed = row.get("failed_attempt_resource", -1)
            if min(ps, rs, ss, failed) < 0 or ps > p_available or rs > r_available or ss > s_available:
                errors.append("service_bounds:" + tag)
            if row.get("primary_after") != p_available - ps:
                errors.append("primary_conservation:" + tag)
            if row.get("retry_after") != r_available - rs:
                errors.append("retry_conservation:" + tag)
            if row.get("safety_after") != s_available - ss:
                errors.append("safety_conservation:" + tag)
            if any(row.get(name, -1) > fixture["queue_limit"] for name in ("primary_after", "retry_after", "safety_after")):
                errors.append("queue_limit:" + tag)

            expected_failed = fixture["outage_failed_attempt_resource_per_tick"] if fault else 0
            if failed != expected_failed:
                errors.append("failed_attempt_resource:" + tag)
            used = ps + rs + ss + failed
            if used != row.get("total_resource_used") or used > capacity:
                errors.append("JOINT_CAPACITY:" + tag)

            if fault:
                if ps != 0 or rs != 0:
                    errors.append("service_during_dependency_outage:" + tag)
                expected_safety = min(s_available, 1) if policy == "debt_shed_reserved" else min(s_available, capacity - failed)
            elif policy == "debt_shed_reserved":
                expected_safety = min(s_available, 1)
                budget = capacity - expected_safety
                if ps != min(p_available, budget) or rs != min(r_available, budget - ps):
                    errors.append("reserved_scheduling:" + tag)
            else:
                expected_p = min(p_available, capacity)
                expected_r = min(r_available, capacity - expected_p)
                expected_safety = min(s_available, capacity - expected_p - expected_r)
                if ps != expected_p or rs != expected_r:
                    errors.append("shared_scheduling:" + tag)
            if ss != expected_safety:
                errors.append("safety_scheduling:" + tag)

            prior = {"primary": row.get("primary_after"), "retry": row.get("retry_after"),
                     "safety": row.get("safety_after")}

    def final_eight(case_id, policy):
        rows = grouped.get((case_id, policy), [])[-8:]
        return len(rows) == 8 and all(row["safety_service"] >= 1 for row in rows)

    # Negative/control arms must regain safety service. The feedback-on legacy
    # arm must retain both retry debt and safety backlog through the frozen tail.
    for policy in fixture["policies"]:
        if not final_eight("underload_no_trigger", policy):
            errors.append("underload_control:" + policy)
        if not final_eight("finite_fault_debt_no_feedback", policy):
            errors.append("fault_only_control:" + policy)
    legacy_tail = grouped.get(("finite_fault_debt_feedback_on", "legacy_shared_retry"), [])[-8:]
    if len(legacy_tail) != 8 or not all(r["safety_service"] == 0 and r["retry_after"] > 0 and r["safety_after"] > 0 for r in legacy_tail):
        errors.append("feedback_on_legacy_not_sustained")
    for policy in ("debt_shed_reserved", "no_retry_shared"):
        if not final_eight("finite_fault_debt_feedback_on", policy):
            errors.append("feedback_recovery_control:" + policy)
    return {"status": "PASS_METHOD_AND_HYPOTHESIS_SCOPED" if not errors else "FAIL_METHOD",
            "rows_reconstructed": len(raw_rows), "groups_reconstructed": len(grouped),
            "joint_capacity_checks": len(raw_rows), "errors": errors}


if __name__ == "__main__":
    with open(sys.argv[1], encoding="utf-8") as stream:
        fixture = json.load(stream)
    with open(sys.argv[2], encoding="utf-8") as stream:
        rows = [json.loads(line) for line in stream if line.strip()]
    result = audit(fixture, rows)
    with open(sys.argv[3], "w", encoding="utf-8") as stream:
        json.dump(result, stream, indent=2, sort_keys=True)
        stream.write("\n")
    print(json.dumps(result, sort_keys=True))
    raise SystemExit(0 if result["status"] == "PASS_METHOD_AND_HYPOTHESIS_SCOPED" else 1)
