"""Independent raw-output audit; intentionally does not import candidate.py."""


def audit(fixture, output):
    errors = []
    wanted = {case["case_id"] for case in fixture["cases"]}
    observed_cases = output.get("cases", [])
    actual = [case.get("case_id") for case in observed_cases]
    if set(actual) != wanted or len(actual) != len(wanted):
        errors.append("case_inventory_mismatch")

    shared_detected = 0
    primary_escape = 0
    for case in observed_cases:
        cid = case.get("case_id")
        rows = case.get("rows", [])
        expected_ids = {f"{route}{i}" for route in ("A", "B") for i in range(4)}
        truth_ids = [row.get("assignment_id") for row in rows]
        if set(truth_ids) != expected_ids or len(truth_ids) != 8:
            errors.append(f"{cid}:assignment_inventory")
            continue

        expected_route = {f"{route}{i}": route for route in ("A", "B") for i in range(4)}
        seen = []
        observed_rows = []
        for row in rows:
            record = row.get("observed", {})
            if record.get("terminal"):
                seen.append(record.get("assignment_id"))
                observed_rows.append(record)
        unique = len(seen) == len(set(seen))
        route_consistent = all(
            item_id in expected_route and expected_route[item_id] == rec.get("route")
            for item_id, rec in ((rec.get("assignment_id"), rec) for rec in observed_rows)
        )
        if not unique or not route_consistent:
            expected_attempt = "HOLD_IDENTITY"
        elif set(seen) != expected_ids:
            expected_attempt = "HOLD_MISSING"
        else:
            expected_attempt = "PASS_COMPLETE"
        if case.get("all_attempt") != expected_attempt:
            errors.append(f"{cid}:all_attempt_disagrees_with_rows")

        oracle_mismatch = any(
            row.get("ground_truth", {}).get("sentinel")
            != row.get("observed", {}).get("sentinel")
            for row in rows if row.get("observed", {}).get("terminal")
        )
        sentinel_rates = {}
        for route in ("A", "B"):
            group = [r for r in observed_rows if r.get("route") == route]
            sentinel_rates[route] = sum(r.get("sentinel") is True for r in group) / len(group) if group else None
        sentinel_shift = sentinel_rates["A"] != sentinel_rates["B"]
        if case.get("negative_control_shift") is not sentinel_shift:
            errors.append(f"{cid}:negative_control_disagrees_with_route_rates")
        if case.get("observed_sentinel_rates") != sentinel_rates:
            errors.append(f"{cid}:sentinel_rate_disagrees_with_rows")

        rates = {}
        for route in ("A", "B"):
            group = [r for r in observed_rows if r.get("route") == route]
            rates[route] = sum(r.get("primary") is True for r in group) / len(group) if group else None
        if case.get("observed_primary_rates") != rates:
            errors.append(f"{cid}:primary_rate_disagrees_with_rows")

        real_collateral = any(
            row.get("ground_truth", {}).get("collateral") is True for row in rows
        )
        if expected_attempt == "HOLD_IDENTITY":
            expected_disposition = "IDENTITY_HOLD"
        elif expected_attempt == "HOLD_MISSING":
            expected_disposition = "MISSING_HOLD"
        elif real_collateral:
            expected_disposition = "COLLATERAL_FAIL"
        elif sentinel_shift and oracle_mismatch:
            expected_disposition = "SHARED_PATH_HOLD"
        elif cid == "primary_only_fault" and rates["A"] != rates["B"]:
            expected_disposition = "OUT_OF_SCOPE_UNDETECTED"
        else:
            expected_disposition = "NO_SIGNAL"
        if case.get("disposition") != expected_disposition:
            errors.append(f"{cid}:disposition_disagrees_with_rows")

        if cid == "shared_export_fault" and expected_attempt == "PASS_COMPLETE" and sentinel_shift:
            shared_detected += 1
        if (cid == "primary_only_fault" and expected_attempt == "PASS_COMPLETE"
                and not sentinel_shift and expected_disposition == "OUT_OF_SCOPE_UNDETECTED"):
            primary_escape += 1

    if output.get("incremental_shared_faults_detected") != shared_detected:
        errors.append("incremental_count_mismatch")
    if output.get("primary_only_false_all_clear") != primary_escape:
        errors.append("primary_only_escape_count_mismatch")
    if shared_detected != 1 or primary_escape != 1:
        errors.append("preregistered_path_contrast_not_observed")
    return {"status": "PASS_INDEPENDENT_AUDIT" if not errors else "FAIL_AUDIT",
            "errors": errors,
            "case_count": len(observed_cases),
            "rows": sum(len(case.get("rows", [])) for case in observed_cases),
            "mutation_controls": None}
