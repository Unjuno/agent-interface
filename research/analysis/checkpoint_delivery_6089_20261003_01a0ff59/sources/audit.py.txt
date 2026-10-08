"""Raw-only recursive path and erasure-pattern auditor; imports no candidate code."""


def _all_paths(case, steps):
    paths = [[x] for x in case["initial_states"]]
    for _ in range(steps):
        paths = [p + [p[-1] + case["action"] + w] for p in paths for w in case["disturbances"]]
    return paths


def _oracle(case, steps):
    paths = _all_paths(case, steps)
    for t in range(steps + 1):
        positions = [p[t] for p in paths]
        if any(x >= case["boundary_by_step"][t] for x in positions):
            return {"safe": False, "first_unsafe_step": t, "worst_position": max(positions)}
    return {"safe": True, "first_unsafe_step": None, "worst_position": max(p[-1] for p in paths)}


def _fresh(event, case):
    return event.get("kind") == "FRESH" and event.get("generation") == case["source_generation"] and event.get("age") <= case["max_receipt_age"]


def _base(case):
    valid = []
    for h in range(case["max_horizon"] + 1):
        if _oracle(case, 0 if h == 0 else h + case["release_lag"])["safe"]:
            valid.append(h)
    return max(valid)


def reconstruct(case):
    base = _base(case)
    events = case["checkpoint_events"]
    first = events[0] if events else {"kind": "FRESH", "generation": case["source_generation"], "age": 0}
    first_fresh = _fresh(first, case)
    misses = 0
    invalidation_event = False
    for event in events:
        if _fresh(event, case):
            break
        if event.get("kind") == "TARGET_INVALIDATED":
            invalidation_event = True
            break
        misses += 1
    invalidated = case["target_invalidated"] or invalidation_event

    a_steps = 0 if base == 0 or invalidated else base + case["release_lag"] + (0 if first_fresh else case["observation_interval"])
    a_oracle = _oracle(case, a_steps)
    a = {"assumes_checkpoint_success": True, "receipt_was_usable": first_fresh, "held_steps_before_release": a_steps, "safe": a_oracle["safe"] and not invalidated, "disposition": "INVALIDATED" if invalidated else ("UNSAFE_OPTIMISTIC_EXTENSION" if not a_oracle["safe"] else "SAFE_IN_THIS_FIXTURE")}

    b_steps = 0 if base == 0 or invalidated else base + case["release_lag"]
    b_oracle = _oracle(case, b_steps)
    b = {"release_on_missing_or_stale": not first_fresh, "receipt_was_usable": first_fresh, "held_steps_before_release": b_steps, "safe": b_oracle["safe"] and not invalidated, "disposition": "YIELD_INVALIDATED_TARGET" if invalidated else ("RELEASED_ON_ABSENT_OR_STALE" if not first_fresh else "FRESH_CHECKPOINT")}

    horizon_table = []
    feasible = []
    if invalidated:
        robust_horizon, c_disposition = 0, "YIELD_INVALIDATED_TARGET"
    elif not case["loss_bound_supported"] or case["max_consecutive_misses"] is None:
        robust_horizon, c_disposition = 0, "HOLD_LOSS_BOUND_UNSUPPORTED"
    else:
        k = case["max_consecutive_misses"]
        for h in range(case["max_horizon"] + 1):
            # Independently enumerate every possible count of misses up to k.
            checks = []
            for m in range(k + 1):
                steps = 0 if h == 0 else h + m * case["observation_interval"] + case["release_lag"]
                checks.append({"misses": m, **_oracle(case, steps)})
            ok = all(item["safe"] for item in checks)
            horizon_table.append({"horizon": h, "checks": checks, "safe_for_all_loss_patterns": ok})
            if ok:
                feasible.append(h)
        robust_horizon, c_disposition = max(feasible), "ROBUST_LOSS_HORIZON"

    if invalidated:
        c_safe = robust_horizon == 0
        horizon_table = []
    elif not case["loss_bound_supported"] or case["max_consecutive_misses"] is None:
        c_safe = robust_horizon == 0
        horizon_table = []
    else:
        c_safe = all(row["safe_for_all_loss_patterns"] for row in horizon_table if row["horizon"] <= robust_horizon)

    beyond = case["max_consecutive_misses"] is not None and misses > case["max_consecutive_misses"]
    stress = None
    if beyond and robust_horizon:
        beyond_steps = robust_horizon + (case["max_consecutive_misses"] + 1) * case["observation_interval"] + case["release_lag"]
        stress_oracle = _oracle(case, beyond_steps)
        stress = {"misses": case["max_consecutive_misses"] + 1, "safe": stress_oracle["safe"], "disposition": "OUT_OF_BOUND_NOT_CERTIFIED", "held_steps_if_illegally_continued": beyond_steps}

    if invalidated:
        actual_status = "YIELD_INVALIDATED_TARGET"
    elif case["max_consecutive_misses"] is None:
        actual_status = "HOLD_LOSS_BOUND_UNSUPPORTED"
    elif beyond:
        actual_status = "BOUND_EXCEEDED_STOP_AT_FROZEN_DEADLINE"
    elif misses == 0:
        actual_status = "NO_LOSS_CONTROL"
    else:
        actual_status = "IN_BOUND_ERASURE_PATTERN"

    return {
        "case_id": case["id"],
        "base_no_loss_horizon": base,
        "policy_a_optimistic": a,
        "policy_b_release_on_absence": b,
        "policy_c_loss_robust": {"selected_horizon": robust_horizon, "disposition": c_disposition, "safe_for_all_declared_patterns": c_safe, "horizon_table": horizon_table, "actual_consecutive_misses": misses, "actual_status": actual_status},
        "stress": stress,
    }


def audit(cases, rows):
    errors = []
    expected_ids = [c["id"] for c in cases]
    actual_ids = [r.get("case_id") for r in rows]
    if actual_ids != expected_ids:
        errors.append("CASE_COVERAGE_OR_ORDER")
    by_id = {r.get("case_id"): r for r in rows}
    for case in cases:
        if by_id.get(case["id"]) != reconstruct(case):
            errors.append("RECONSTRUCTION_MISMATCH:" + case["id"])
    return {"status": "PASS_METHOD_SCOPED" if not errors else "FAIL_AUDIT", "rows": len(rows), "errors": errors}
