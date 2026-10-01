"""Finite path-specific ascertainment probe; no repository scorer is loaded."""


def _build_rows(case, cohort):
    rows = []
    success_a = set(cohort["primary_success_route_a"])
    success_b = set(
        cohort[
            "primary_success_route_b_benefit"
            if case["benefit"]
            else "primary_success_route_b_null"
        ]
    )
    baseline_sentinel = set(cohort["sentinel_true_at_baseline"])
    for route in ("A", "B"):
        for index in range(cohort["episodes_per_route"]):
            assignment_id = f"{route}{index}"
            primary_true = assignment_id in (success_a if route == "A" else success_b)
            sentinel_true = assignment_id in baseline_sentinel
            if case["collateral"] and assignment_id == "B3":
                sentinel_true = True
            row = {
                "assignment_id": assignment_id,
                "route": route,
                "ground_truth": {
                    "primary": primary_true,
                    "sentinel": sentinel_true,
                    "collateral": case["collateral"] and assignment_id == "B3",
                },
                "observed": {
                    "assignment_id": assignment_id,
                    "route": route,
                    "primary": primary_true,
                    "sentinel": sentinel_true,
                    "terminal": True,
                },
            }
            if route == "B" and assignment_id == "B2":
                if case["fault"] == "shared_export":
                    row["observed"]["primary"] = True
                    row["observed"]["sentinel"] = True
                elif case["fault"] == "primary_only_export":
                    row["observed"]["primary"] = True
                elif case["fault"] == "missing_terminal":
                    row["observed"]["terminal"] = False
            if case["fault"] == "foreign_join" and assignment_id == "B3":
                row["observed"]["assignment_id"] = "A3"
            rows.append(row)
    return rows


def _all_attempt_status(rows):
    expected = {row["assignment_id"]: row["route"] for row in rows}
    observed = [row["observed"] for row in rows if row["observed"]["terminal"]]
    ids = [row["assignment_id"] for row in observed]
    if len(ids) != len(set(ids)) or any(
        item_id not in expected or expected[item_id] != record["route"]
        for item_id, record in ((record["assignment_id"], record) for record in observed)
    ):
        return "HOLD_IDENTITY"
    if set(ids) != set(expected):
        return "HOLD_MISSING"
    return "PASS_COMPLETE"


def evaluate(fixture):
    output = {"allocation_id": fixture["allocation_id"], "cases": []}
    for case in fixture["cases"]:
        rows = _build_rows(case, fixture["cohort"])
        complete = [row for row in rows if row["observed"]["terminal"]]
        attempt = _all_attempt_status(rows)
        primary_rates = {}
        sentinel_rates = {}
        for route in ("A", "B"):
            group = [row for row in complete if row["route"] == route]
            primary_rates[route] = sum(row["observed"]["primary"] for row in group) / len(group)
            sentinel_rates[route] = sum(row["observed"]["sentinel"] for row in group) / len(group)
        sentinel_shift = sentinel_rates["A"] != sentinel_rates["B"]
        oracle_mismatch = any(
            row["ground_truth"]["sentinel"] != row["observed"]["sentinel"]
            for row in complete
        )
        true_collateral = any(row["ground_truth"]["collateral"] for row in rows)
        primary_shift = primary_rates["B"] != primary_rates["A"]
        if attempt == "HOLD_IDENTITY":
            disposition = "IDENTITY_HOLD"
        elif attempt == "HOLD_MISSING":
            disposition = "MISSING_HOLD"
        elif true_collateral:
            disposition = "COLLATERAL_FAIL"
        elif sentinel_shift and oracle_mismatch:
            disposition = "SHARED_PATH_HOLD"
        elif case["fault"] == "primary_only_export" and primary_shift:
            disposition = "OUT_OF_SCOPE_UNDETECTED"
        else:
            disposition = "NO_SIGNAL"
        output["cases"].append({
            "case_id": case["case_id"],
            "rows": rows,
            "all_attempt": attempt,
            "negative_control_shift": sentinel_shift,
            "observed_sentinel_rates": sentinel_rates,
            "observed_primary_rates": primary_rates,
            "disposition": disposition,
        })
    output["incremental_shared_faults_detected"] = sum(
        row["case_id"] == "shared_export_fault"
        and row["all_attempt"] == "PASS_COMPLETE"
        and row["negative_control_shift"]
        for row in output["cases"]
    )
    output["primary_only_false_all_clear"] = sum(
        row["case_id"] == "primary_only_fault"
        and row["all_attempt"] == "PASS_COMPLETE"
        and not row["negative_control_shift"]
        and row["disposition"] == "OUT_OF_SCOPE_UNDETECTED"
        for row in output["cases"]
    )
    return output
