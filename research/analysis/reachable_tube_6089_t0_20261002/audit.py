"""Raw-only recursive path enumerator; intentionally independent of candidate."""


def _paths(case, steps):
    paths = [[position] for position in case["initial_states"]]
    for _ in range(steps):
        paths = [
            path + [path[-1] + case["action"] + disturbance]
            for path in paths
            for disturbance in case["disturbances"]
        ]
    return paths


def _oracle(case, horizon):
    steps = 0 if horizon == 0 else horizon + case["release_lag"]
    all_paths = _paths(case, steps)
    worst = max(path[-1] for path in all_paths)
    for step in range(steps + 1):
        positions = [path[step] for path in all_paths]
        if any(position >= case["boundary_by_step"][step] for position in positions):
            return {
                "safe": False,
                "first_unsafe_step": step,
                "worst_position": max(positions),
            }
    return {"safe": True, "first_unsafe_step": None, "worst_position": worst}


def reconstruct(case):
    table = []
    for horizon in range(case["max_horizon"] + 1):
        table.append({"horizon": horizon, **_oracle(case, horizon)})
    robust_max = max(row["horizon"] for row in table if row["safe"])
    nominal = case["initial_states"][len(case["initial_states"]) // 2]
    nominal_max = 0
    if not case["invalidated"]:
        for horizon in range(1, case["max_horizon"] + 1):
            steps = horizon + case["release_lag"]
            position = nominal
            safe = position < case["boundary_by_step"][0]
            for step in range(1, steps + 1):
                position += case["action"]
                safe = safe and position < case["boundary_by_step"][step]
            if safe:
                nominal_max = horizon
    selected = 0 if case["invalidated"] else robust_max
    stress = None
    if case["stress_disturbances"] is not None:
        steps = selected + case["release_lag"] if selected else 0
        path = [case["initial_states"][-1]]
        for disturbance in case["stress_disturbances"][:steps]:
            path.append(path[-1] + case["action"] + disturbance)
        within = all(
            case["stress_disturbances"][i] in case["disturbances"]
            for i in range(steps)
        )
        safe = True
        for i, position in enumerate(path):
            if position >= case["boundary_by_step"][i]:
                safe = False
                break
        stress = {
            "within_declared_bound": within,
            "safe": safe,
            "disposition": "IN_ENVELOPE_CHECK" if within else "OUT_OF_ENVELOPE_NOT_CERTIFIED",
            "path": path,
        }
    return {
        "case_id": case["id"],
        "outcome": "YIELD_INVALIDATED_SOURCE" if case["invalidated"] else "ROBUST_HORIZON",
        "selected_horizon": selected,
        "robust_max_horizon": robust_max,
        "nominal_max_horizon": nominal_max,
        "fixed_one_safe": next(row["safe"] for row in table if row["horizon"] == 1),
        "horizon_table": table,
        "stress": stress,
    }


def audit(cases, records):
    errors = []
    expected_ids = [case["id"] for case in cases]
    actual_ids = [record.get("case_id") for record in records]
    if actual_ids != expected_ids:
        errors.append("CASE_ORDER_OR_COVERAGE_MISMATCH")
    by_id = {record.get("case_id"): record for record in records}
    for case in cases:
        actual = by_id.get(case["id"])
        if actual != reconstruct(case):
            errors.append(f"RESULT_MISMATCH:{case['id']}")
    return {"status": "PASS_METHOD_SCOPED" if not errors else "FAIL_AUDIT", "errors": errors}
