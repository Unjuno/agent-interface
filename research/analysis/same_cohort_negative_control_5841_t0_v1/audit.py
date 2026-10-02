"""Independent literal-table audit; imports neither candidate nor its helpers."""

import json


def _expected_pairs(fixture):
    return {
        (route, episode["id"])
        for route in fixture["routes"]
        for episode in fixture["episodes"]
    }


def audit_result(result, fixture, expected):
    errors = []
    expected_cases = expected["cases"]
    actual_cases = result.get("cases", [])
    if result.get("schema") != "issue-5841-negative-control-t0-result-v1":
        errors.append("RESULT_SCHEMA_MISMATCH")
    if [row.get("id") for row in actual_cases] != [row["id"] for row in expected_cases]:
        errors.append("CASE_INVENTORY_MISMATCH")

    assigned_seals = {episode["id"]: episode["seal"] for episode in fixture["episodes"]}
    episode_index = {episode["id"]: index for index, episode in enumerate(fixture["episodes"])}
    expected_pairs = _expected_pairs(fixture)
    for case_index, expected_case in enumerate(expected_cases):
        if case_index >= len(actual_cases):
            break
        actual = actual_cases[case_index]
        case_id = expected_case["id"]
        ledger = actual.get("ledger", [])
        observed_pairs = [(row.get("route"), row.get("episode")) for row in ledger]
        if len(ledger) != len(expected_pairs) or set(observed_pairs) != expected_pairs or len(set(observed_pairs)) != len(observed_pairs):
            errors.append(f"CONTROL_DENOMINATOR_MISMATCH:{case_id}")
        for row in ledger:
            route, episode = row.get("route"), row.get("episode")
            if route not in fixture["routes"] or episode not in episode_index:
                continue
            index = episode_index[episode]
            scenario = fixture["scenarios"][case_index]
            override = scenario["join_overrides"].get(f"{route}:{episode}", {})
            expected_missing = (route, episode) in {
                (item["route"], item["episode"]) for item in scenario["missing"]
            }
            expected_value = None if expected_missing else scenario["primary"][route][index]
            expected_fields = {
                "joined_id": override.get("joined_id", episode),
                "joined_seal": override.get("joined_seal", assigned_seals[episode]),
                "primary_value": expected_value,
                "primary_present": not expected_missing,
                "sentinel_before": 0,
                "sentinel_after_snapshot": scenario["sentinel_after"][route][index],
                "sentinel_after_export": scenario["sentinel_export"][route][index],
            }
            for field, expected_value in expected_fields.items():
                if row.get(field) != expected_value:
                    errors.append(f"LEDGER_FIELD_MISMATCH:{case_id}:{route}:{episode}:{field}")
            if episode in assigned_seals and row.get("assigned_seal") != assigned_seals[episode]:
                errors.append(f"ASSIGNMENT_SEAL_MISMATCH:{case_id}:{route}:{episode}")

        if actual.get("id") != case_id:
            continue
        if actual.get("primary_only_guarded_minus_direct") != expected_case["delta"]:
            errors.append(f"PRIMARY_DELTA_MISMATCH:{case_id}")
        if actual.get("reference_deck") != expected_case["deck"]:
            errors.append(f"REFERENCE_DECK_MISMATCH:{case_id}")
        flags = actual.get("control_flags", {})
        ordered_flags = [
            flags.get("any_primary_outcome_missing"),
            flags.get("route_specific_missingness"),
            flags.get("foreign_join_or_seal_mismatch"),
            flags.get("actual_sentinel_change"),
            flags.get("sentinel_export_snapshot_mismatch"),
        ]
        if ordered_flags != expected_case["flags"]:
            errors.append(f"CONTROL_FLAG_MISMATCH:{case_id}")
        if actual.get("disposition") != expected_case["disposition"]:
            errors.append(f"DISPOSITION_MISMATCH:{case_id}")

        for route in fixture["routes"]:
            if actual.get("assigned_rows_by_route", {}).get(route) != len(fixture["episodes"]):
                errors.append(f"ASSIGNED_DENOMINATOR_MISMATCH:{case_id}:{route}")
            expected_known = sum(
                (route, episode["id"]) not in {
                    (item["route"], item["episode"]) for item in fixture["scenarios"][case_index]["missing"]
                }
                for episode in fixture["episodes"]
            )
            if actual.get("known_rows_by_route", {}).get(route) != expected_known:
                errors.append(f"OBSERVED_DENOMINATOR_MISMATCH:{case_id}:{route}")
    truth_table = [
        {
            "id": row["id"],
            "true_primary_delta": row["true_primary_delta"],
            "truth_class": row["truth_class"],
        }
        for row in expected_cases
    ]
    return {
        "status": "PASS_METHOD_SCOPED" if not errors else "FAIL_METHOD",
        "errors": errors,
        "independent_truth_table": truth_table,
    }


def audit_bytes(raw_bytes, fixture, expected):
    try:
        result = json.loads(raw_bytes.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return {"status": "FAIL_METHOD", "errors": ["RAW_JSON_INVALID"]}
    return audit_result(result, fixture, expected)
