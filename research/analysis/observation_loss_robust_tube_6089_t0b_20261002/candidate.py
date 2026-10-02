"""Set-propagation candidate for the scheduled-observation-erasure extension."""


def _reachable(case, steps):
    states = set(case["initial_states"])
    for step in range(1, steps + 1):
        states = {
            state + case["action"] + disturbance
            for state in states
            for disturbance in case["disturbances"]
        }
        if any(state >= case["boundary_by_step"][step] for state in states):
            return {"safe": False, "first_unsafe_step": step, "worst_position": max(states)}
    return {"safe": max(states) < case["boundary_by_step"][0], "first_unsafe_step": None, "worst_position": max(states)}


def _usable(event, case):
    return (
        event.get("kind") == "FRESH"
        and event.get("generation") == case["source_generation"]
        and event.get("age") <= case["max_receipt_age"]
    )


def _misses_before_usable(case):
    misses = 0
    for event in case["checkpoint_events"]:
        if _usable(event, case):
            break
        if event.get("kind") == "TARGET_INVALIDATED":
            return misses, True
        misses += 1
    return misses, False


def _base_horizon(case):
    safe = []
    for horizon in range(case["max_horizon"] + 1):
        steps = 0 if horizon == 0 else horizon + case["release_lag"]
        if _reachable(case, steps)["safe"]:
            safe.append(horizon)
    return max(safe)


def evaluate(case):
    base = _base_horizon(case)
    events = case["checkpoint_events"]
    first = events[0] if events else {"kind": "FRESH", "generation": case["source_generation"], "age": 0}
    first_fresh = _usable(first, case)
    actual_misses, invalidation_event = _misses_before_usable(case)
    invalidated = case["target_invalidated"] or invalidation_event

    optimistic_steps = 0 if base == 0 or invalidated else base + case["release_lag"] + (0 if first_fresh else case["observation_interval"])
    optimistic = _reachable(case, optimistic_steps)
    policy_a = {
        "assumes_checkpoint_success": True,
        "receipt_was_usable": first_fresh,
        "held_steps_before_release": optimistic_steps,
        "safe": optimistic["safe"] and not invalidated,
        "disposition": "INVALIDATED" if invalidated else ("UNSAFE_OPTIMISTIC_EXTENSION" if not optimistic["safe"] else "SAFE_IN_THIS_FIXTURE"),
    }

    b_steps = 0 if base == 0 or invalidated else base + case["release_lag"]
    b_result = _reachable(case, b_steps)
    policy_b = {
        "release_on_missing_or_stale": not first_fresh,
        "receipt_was_usable": first_fresh,
        "held_steps_before_release": b_steps,
        "safe": b_result["safe"] and not invalidated,
        "disposition": "YIELD_INVALIDATED_TARGET" if invalidated else ("RELEASED_ON_ABSENT_OR_STALE" if not first_fresh else "FRESH_CHECKPOINT"),
    }

    if invalidated:
        robust_horizon, c_disposition = 0, "YIELD_INVALIDATED_TARGET"
    elif not case["loss_bound_supported"] or case["max_consecutive_misses"] is None:
        robust_horizon, c_disposition = 0, "HOLD_LOSS_BOUND_UNSUPPORTED"
    else:
        bound = case["max_consecutive_misses"]
        feasible = []
        for horizon in range(case["max_horizon"] + 1):
            worst_case_misses = 0 if horizon == 0 else bound
            steps = 0 if horizon == 0 else horizon + worst_case_misses * case["observation_interval"] + case["release_lag"]
            if all(_reachable(case, horizon + m * case["observation_interval"] + case["release_lag"])["safe"] for m in range(bound + 1)) if horizon > 0 else _reachable(case, 0)["safe"]:
                feasible.append(horizon)
        robust_horizon = max(feasible)
        c_disposition = "ROBUST_LOSS_HORIZON"

    if case["max_consecutive_misses"] is None or invalidated:
        c_safe = robust_horizon == 0
        horizon_table = []
    else:
        bound = case["max_consecutive_misses"]
        horizon_table = []
        for horizon in range(case["max_horizon"] + 1):
            missed = 0 if horizon == 0 else bound
            steps = 0 if horizon == 0 else horizon + missed * case["observation_interval"] + case["release_lag"]
            checks = [
                {"misses": m, **_reachable(case, 0 if horizon == 0 else horizon + m * case["observation_interval"] + case["release_lag"])}
                for m in range(bound + 1)
            ]
            horizon_table.append({"horizon": horizon, "checks": checks, "safe_for_all_loss_patterns": all(x["safe"] for x in checks)})
        c_safe = all(x["safe_for_all_loss_patterns"] for x in horizon_table if x["horizon"] <= robust_horizon)

    actual_beyond = case["max_consecutive_misses"] is not None and actual_misses > case["max_consecutive_misses"]
    stress = None
    if actual_beyond and robust_horizon:
        beyond_steps = robust_horizon + (case["max_consecutive_misses"] + 1) * case["observation_interval"] + case["release_lag"]
        beyond = _reachable(case, beyond_steps)
        stress = {"misses": case["max_consecutive_misses"] + 1, "safe": beyond["safe"], "disposition": "OUT_OF_BOUND_NOT_CERTIFIED", "held_steps_if_illegally_continued": beyond_steps}

    if invalidated:
        actual_status = "YIELD_INVALIDATED_TARGET"
    elif case["max_consecutive_misses"] is None:
        actual_status = "HOLD_LOSS_BOUND_UNSUPPORTED"
    elif actual_beyond:
        actual_status = "BOUND_EXCEEDED_STOP_AT_FROZEN_DEADLINE"
    elif actual_misses == 0:
        actual_status = "NO_LOSS_CONTROL"
    else:
        actual_status = "IN_BOUND_ERASURE_PATTERN"

    return {
        "case_id": case["id"],
        "base_no_loss_horizon": base,
        "policy_a_optimistic": policy_a,
        "policy_b_release_on_absence": policy_b,
        "policy_c_loss_robust": {
            "selected_horizon": robust_horizon,
            "disposition": c_disposition,
            "safe_for_all_declared_patterns": c_safe,
            "horizon_table": horizon_table,
            "actual_consecutive_misses": actual_misses,
            "actual_status": actual_status,
        },
        "stress": stress,
    }


def run(cases):
    return [evaluate(case) for case in cases]
