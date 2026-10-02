"""Set-propagation candidate for the finite reachable-tube T0 fixture."""


def _safe_steps(case, steps):
    states = set(case["initial_states"])
    worst = max(states)
    if worst >= case["boundary_by_step"][0]:
        return {"safe": False, "first_unsafe_step": 0, "worst_position": worst}
    for step in range(1, steps + 1):
        states = {
            position + case["action"] + disturbance
            for position in states
            for disturbance in case["disturbances"]
        }
        worst = max(states)
        if worst >= case["boundary_by_step"][step]:
            return {"safe": False, "first_unsafe_step": step, "worst_position": worst}
    return {"safe": True, "first_unsafe_step": None, "worst_position": worst}


def evaluate(case):
    max_horizon = case["max_horizon"]
    release_lag = case["release_lag"]
    table = []
    for horizon in range(max_horizon + 1):
        steps = 0 if horizon == 0 else horizon + release_lag
        row = _safe_steps(case, steps)
        table.append({"horizon": horizon, **row})

    safe_horizons = [row["horizon"] for row in table if row["safe"]]
    robust_max = max(safe_horizons)
    if case["invalidated"]:
        selected = 0
        outcome = "YIELD_INVALIDATED_SOURCE"
    else:
        selected = robust_max
        outcome = "ROBUST_HORIZON"

    nominal = case["initial_states"][len(case["initial_states"]) // 2]
    nominal_max = 0
    if not case["invalidated"]:
        for horizon in range(1, max_horizon + 1):
            steps = horizon + release_lag
            position = nominal
            nominal_safe = position < case["boundary_by_step"][0]
            for step in range(1, steps + 1):
                position += case["action"]
                nominal_safe = nominal_safe and position < case["boundary_by_step"][step]
            if nominal_safe:
                nominal_max = horizon

    fixed_short = next(row["safe"] for row in table if row["horizon"] == 1)
    stress = None
    if case["stress_disturbances"] is not None:
        steps = selected + release_lag if selected else 0
        stress_path = [case["initial_states"][-1]]
        for step, disturbance in enumerate(case["stress_disturbances"][:steps], start=1):
            stress_path.append(stress_path[-1] + case["action"] + disturbance)
        within = all(
            case["stress_disturbances"][step - 1] in case["disturbances"]
            for step in range(1, steps + 1)
        )
        safe = all(
            position < case["boundary_by_step"][step]
            for step, position in enumerate(stress_path)
        )
        stress = {
            "within_declared_bound": within,
            "safe": safe,
            "disposition": "IN_ENVELOPE_CHECK" if within else "OUT_OF_ENVELOPE_NOT_CERTIFIED",
            "path": stress_path,
        }

    return {
        "case_id": case["id"],
        "outcome": outcome,
        "selected_horizon": selected,
        "robust_max_horizon": robust_max,
        "nominal_max_horizon": nominal_max,
        "fixed_one_safe": fixed_short,
        "horizon_table": table,
        "stress": stress,
    }


def run(cases):
    return [evaluate(case) for case in cases]
