"""Literal independent expected outcomes for the frozen case IDs."""
EXPECTED = {
    "warm_cpu_feasible": ("COMPATIBLE", ()),
    "unsupported_primitive": ("REJECTED", ("unsupported_primitive", "wrong_evidence_role")),
    "wrong_role": ("REJECTED", ("wrong_evidence_role",)),
    "stale_version": ("REJECTED", ("stale_version",)),
    "resource_unavailable": ("UNAVAILABLE", ("resource_unavailable", "latency_unqualified")),
    "cold_budget_violation": ("REJECTED", ("budget_exceeded",)),
    "side_effect_prohibited": ("UNAVAILABLE", ("resource_unavailable", "latency_unqualified", "side_effect_prohibited")),
    "deadline_infeasible": ("REJECTED", ("deadline_infeasible",)),
}


def audit(cases: dict, raw: dict) -> dict:
    observed = {row["check_id"]: row for row in raw["decisions"]}
    case_rows = cases["cases"]
    ids = {row["case_id"] for row in case_rows}
    ok = ids == set(EXPECTED) and len(case_rows) == len(ids) and len(observed) == len(ids)
    errors = []
    for item in case_rows:
        expected_status, expected_reasons = EXPECTED[item["case_id"]]
        result = observed.get(item["check"]["check_id"], {})
        expected = (expected_status, expected_reasons)
        got = (result.get("status"), tuple(result.get("reasons", [])))
        if item["expected"] != expected_status or tuple(item["reasons"]) != expected_reasons or got != expected:
            ok = False
            errors.append({"case_id": item["case_id"], "expected": expected, "observed": got})
        if result.get("dispatch_count") != 0 or result.get("authority") != "none" or result.get("cost_basis") != "declared_estimate_not_measurement":
            ok = False
            errors.append({"case_id": item["case_id"], "invariant": "dispatch_authority_cost"})
    return {"disposition": "PASS_HOST_CONSTRUCTION_ONLY" if ok else "FAIL", "case_count": len(case_rows),
            "matched": ok and not errors, "errors": errors, "dispatches": 0}
