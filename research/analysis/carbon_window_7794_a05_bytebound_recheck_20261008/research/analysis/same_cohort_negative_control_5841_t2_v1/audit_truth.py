"""Independent fixture-derived audit of retained Issue #5841 T1 raw rows."""


def _truth(case, cohort, assignment_id):
    route = assignment_id[0]
    success_a = set(cohort["primary_success_route_a"])
    success_b = set(
        cohort[
            "primary_success_route_b_benefit"
            if case["benefit"]
            else "primary_success_route_b_null"
        ]
    )
    primary = assignment_id in (success_a if route == "A" else success_b)
    sentinel = assignment_id in set(cohort["sentinel_true_at_baseline"])
    collateral = case["collateral"] is True and assignment_id == "B3"
    if collateral:
        sentinel = True
    return {"primary": primary, "sentinel": sentinel, "collateral": collateral}


def _expected_rows(case, cohort):
    rows = []
    for route in ("A", "B"):
        for index in range(cohort["episodes_per_route"]):
            assignment_id = f"{route}{index}"
            truth = _truth(case, cohort, assignment_id)
            observed = {
                "assignment_id": assignment_id,
                "route": route,
                "primary": truth["primary"],
                "sentinel": truth["sentinel"],
                "terminal": True,
            }
            if route == "B" and assignment_id == "B2":
                if case["fault"] == "shared_export":
                    observed["primary"] = True
                    observed["sentinel"] = True
                elif case["fault"] == "primary_only_export":
                    observed["primary"] = True
                elif case["fault"] == "missing_terminal":
                    observed["terminal"] = False
            if case["fault"] == "foreign_join" and assignment_id == "B3":
                observed["assignment_id"] = "A3"
            rows.append({
                "assignment_id": assignment_id,
                "route": route,
                "ground_truth": truth,
                "observed": observed,
            })
    return rows


def _summary(case, rows):
    complete = [row["observed"] for row in rows if row["observed"].get("terminal") is True]
    assigned_routes = {row["assignment_id"]: row["route"] for row in rows}
    observed_ids = [row.get("assignment_id") for row in complete]
    identity_bad = len(observed_ids) != len(set(observed_ids)) or any(
        item_id not in assigned_routes or assigned_routes[item_id] != record.get("route")
        for item_id, record in ((record.get("assignment_id"), record) for record in complete)
    )
    if identity_bad:
        all_attempt = "HOLD_IDENTITY"
    elif set(observed_ids) != set(assigned_routes):
        all_attempt = "HOLD_MISSING"
    else:
        all_attempt = "PASS_COMPLETE"

    primary_rates = {}
    sentinel_rates = {}
    for route in ("A", "B"):
        group = [record for record in complete if record.get("route") == route]
        primary_rates[route] = (
            sum(record.get("primary") is True for record in group) / len(group)
            if group else None
        )
        sentinel_rates[route] = (
            sum(record.get("sentinel") is True for record in group) / len(group)
            if group else None
        )

    sentinel_shift = sentinel_rates["A"] != sentinel_rates["B"]
    expected_truth = {row["assignment_id"]: row["ground_truth"] for row in rows}
    oracle_mismatch = any(
        expected_truth[row["assignment_id"]]["sentinel"] != row["observed"].get("sentinel")
        for row in rows if row["observed"].get("terminal") is True
    )
    real_collateral = any(row["ground_truth"]["collateral"] is True for row in rows)
    if all_attempt == "HOLD_IDENTITY":
        disposition = "IDENTITY_HOLD"
    elif all_attempt == "HOLD_MISSING":
        disposition = "MISSING_HOLD"
    elif real_collateral:
        disposition = "COLLATERAL_FAIL"
    elif sentinel_shift and oracle_mismatch:
        disposition = "SHARED_PATH_HOLD"
    elif case["fault"] == "primary_only_export" and primary_rates["A"] != primary_rates["B"]:
        disposition = "OUT_OF_SCOPE_UNDETECTED"
    else:
        disposition = "NO_SIGNAL"
    return {
        "all_attempt": all_attempt,
        "negative_control_shift": sentinel_shift,
        "observed_sentinel_rates": sentinel_rates,
        "observed_primary_rates": primary_rates,
        "disposition": disposition,
    }


def audit(fixture, output):
    errors = []
    if output.get("allocation_id") != fixture.get("allocation_id"):
        errors.append("allocation_id_mismatch")
    fixture_cases = fixture.get("cases", [])
    raw_cases = output.get("cases", [])
    wanted_ids = [case.get("case_id") for case in fixture_cases]
    actual_ids = [case.get("case_id") for case in raw_cases]
    if actual_ids != wanted_ids:
        errors.append("case_inventory_or_order_mismatch")

    expected_case_results = []
    for index, case in enumerate(fixture_cases):
        if index >= len(raw_cases):
            continue
        raw_case = raw_cases[index]
        expected_rows = _expected_rows(case, fixture["cohort"])
        raw_rows = raw_case.get("rows", [])
        if len(raw_rows) != len(expected_rows):
            errors.append(f"{case['case_id']}:row_count_mismatch")
        for row_index, expected in enumerate(expected_rows):
            if row_index >= len(raw_rows):
                continue
            actual = raw_rows[row_index]
            assignment_id = expected["assignment_id"]
            if actual.get("assignment_id") != assignment_id or actual.get("route") != expected["route"]:
                errors.append(f"{case['case_id']}:{assignment_id}:assignment_mismatch")
            if actual.get("ground_truth") != expected["ground_truth"]:
                errors.append(f"{case['case_id']}:{assignment_id}:ground_truth_mismatch")
            if actual.get("observed") != expected["observed"]:
                errors.append(f"{case['case_id']}:{assignment_id}:observed_mismatch")

        summary = _summary(case, expected_rows)
        expected_case_results.append((case["case_id"], summary))
        for key, value in summary.items():
            if raw_case.get(key) != value:
                errors.append(f"{case['case_id']}:{key}_mismatch")

    shared = sum(
        case_id == "shared_export_fault" and summary["all_attempt"] == "PASS_COMPLETE"
        and summary["negative_control_shift"]
        for case_id, summary in expected_case_results
    )
    primary_escape = sum(
        case_id == "primary_only_fault" and summary["all_attempt"] == "PASS_COMPLETE"
        and not summary["negative_control_shift"]
        and summary["disposition"] == "OUT_OF_SCOPE_UNDETECTED"
        for case_id, summary in expected_case_results
    )
    if output.get("incremental_shared_faults_detected") != shared:
        errors.append("incremental_shared_fault_count_mismatch")
    if output.get("primary_only_false_all_clear") != primary_escape:
        errors.append("primary_only_false_all_clear_count_mismatch")

    return {
        "status": "PASS_FIXTURE_DERIVED_RAW" if not errors else "FAIL_T1_RAW_LABEL_MISMATCH",
        "errors": errors,
        "case_count": len(raw_cases),
        "row_count": sum(len(case.get("rows", [])) for case in raw_cases),
        "reconstructed_truth_labels": sum(len(_expected_rows(case, fixture["cohort"])) for case in fixture_cases),
        "mutation_controls": None,
    }
