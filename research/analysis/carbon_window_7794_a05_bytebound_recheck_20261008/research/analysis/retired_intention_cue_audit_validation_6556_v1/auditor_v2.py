"""Strict successor raw auditor for the retained Issue #6556 finite output."""


def audit(fixture, oracle, raw):
    errors, unsafe, missed, misattributed = [], [], [], []
    cases = {case["id"]: case for case in fixture["cases"]}
    truths = oracle["truth"]
    expected_keys = {(case["id"], policy) for case in fixture["cases"] for policy in fixture["policies"]}
    seen = set()
    rows = raw.get("rows", [])
    if not isinstance(rows, list):
        rows = []
        errors.append({"kind": "rows_not_list"})

    for row in rows:
        if not isinstance(row, dict):
            errors.append({"kind": "row_not_object"})
            continue
        key = (row.get("case_id"), row.get("policy"))
        if key in seen:
            errors.append({"kind": "duplicate_row", "key": key})
            continue
        seen.add(key)
        case, truth = cases.get(key[0]), truths.get(key[0])
        if case is None or truth is None or key not in expected_keys:
            errors.append({"kind": "unknown_row", "key": key})
            continue

        decision = row.get("decision")
        if decision not in {"ADMIT", "REFUSE", "UNKNOWN"}:
            errors.append({"kind": "invalid_decision", "key": key, "decision": decision})
            continue
        admitted = decision == "ADMIT"
        if admitted and not truth["eligible"]:
            unsafe.append({"case_id": key[0], "policy": key[1], "oracle_reason": truth["reason"]})
        if truth["eligible"] and not admitted:
            missed.append({"case_id": key[0], "policy": key[1], "decision": decision})

        if row.get("obligation_status") != case["obligation"] or row.get("effect_resolved") is not False or row.get("release_resolved") is not False:
            errors.append({"kind": "obligation_laundering", "key": key})
        expected_lineage = truth["origin"]["instance"] if admitted else None
        if admitted and row.get("response_lineage") != expected_lineage:
            misattributed.append({"case_id": key[0], "policy": key[1], "true_origin": expected_lineage, "claimed_lineage": row.get("response_lineage")})
            if key[1] == "ORIGIN_GENERATION_RETIREMENT_FENCE":
                errors.append({"kind": "origin_fence_misattributed_response", "key": key})
        elif not admitted and row.get("response_lineage") is not None:
            errors.append({"kind": "refused_row_has_response_lineage", "key": key})

        if key[1] == "ORIGIN_GENERATION_RETIREMENT_FENCE":
            if truth["origin"] != case["event"]["origin"]:
                expected_decision = "UNKNOWN"
            else:
                expected_decision = "ADMIT" if truth["eligible"] else "REFUSE"
            if decision != expected_decision:
                errors.append({"kind": "origin_fence_decision_mismatch", "case_id": key[0], "expected": expected_decision, "observed": decision})
        elif decision == "UNKNOWN":
            errors.append({"kind": "unexpected_unknown_for_comparator", "key": key})

    missing = sorted(expected_keys - seen)
    extra = sorted(seen - expected_keys)
    if missing or extra:
        errors.append({"kind": "denominator_mismatch", "expected": len(expected_keys), "observed": len(seen), "missing": missing, "extra": extra})
    fence_rows = [row for row in rows if isinstance(row, dict) and row.get("policy") == "ORIGIN_GENERATION_RETIREMENT_FENCE"]
    fence_unsafe = [item for item in unsafe if item["policy"] == "ORIGIN_GENERATION_RETIREMENT_FENCE"]
    fence_missed = [item for item in missed if item["policy"] == "ORIGIN_GENERATION_RETIREMENT_FENCE"]
    status = "METHOD_PASS_SCOPED" if not errors and not fence_unsafe and not fence_missed and len(fence_rows) == len(cases) else "FAIL_OR_HOLD"
    return {
        "schema": "issue-6556-t0-audit-v2",
        "status": status,
        "rows_expected": len(expected_keys),
        "rows_seen": len(seen),
        "errors": errors,
        "unsafe_admissions_by_policy": _counts(unsafe),
        "missed_eligible_by_policy": _counts(missed),
        "misattributed_admissions_by_policy": _counts(misattributed),
        "origin_fence_unknown_cases": sorted(row["case_id"] for row in fence_rows if row.get("decision") == "UNKNOWN"),
        "obligations_preserved_rows": len(rows) if not any(error["kind"] == "obligation_laundering" for error in errors) else None,
    }


def _counts(rows):
    counts = {}
    for row in rows:
        counts[row["policy"]] = counts.get(row["policy"], 0) + 1
    return counts
