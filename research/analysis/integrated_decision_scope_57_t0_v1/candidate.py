"""Prospective two-axis decision evaluator; never rewrites historical results."""


def _finite_disposition(case):
    if case["integration_discovery"] or case["accounting"] != "COMPLETE" or case["comparability"] != "PASS":
        return "HOLD"
    if case["correctness"] == "UNKNOWN":
        return "HOLD"
    if case["correctness"] == "FAIL" or case["frozen_thresholds"] == "FAIL":
        return "REJECT"
    if case["correctness"] != "PASS" or case["frozen_thresholds"] != "PASS":
        return "HOLD"
    return "RETAIN"


def evaluate(fixture):
    mismatch = (
        fixture["scope_mismatch"]["plan_hold_clause_mentions_single_allocation_insufficient"]
        and not fixture["scope_mismatch"]["frozen_hold_clause_mentions_insufficient"]
    )
    cases = {}
    for case in fixture["cases"]:
        disposition = _finite_disposition(case)
        cases[case["id"]] = {
            "finite_allocation_disposition": disposition,
            "claim_scope": "FINITE_SCHEDULE_ONLY" if disposition == "RETAIN" else "NO_POSITIVE_CLAIM",
            "sequences_per_arm": case["sequences_per_arm"],
        }
    return {
        "schema": "57-integrated-decision-scope-result-v1",
        "source_commit": fixture["source_commit"],
        "source_sha256": fixture["source_sha256"],
        "source_mismatch": "PLAN_VS_FROZEN_HOLD_SCOPE" if mismatch else "NONE",
        "historical_allocation": {
            "disposition": fixture["scope_mismatch"]["historical_report_disposition"],
            "unchanged": True,
        },
        "prospective_cases": cases,
        "generalization_scope": "HOLD_NOT_ESTABLISHED" if not fixture["generalization_protocol_frozen"] else "NOT_ASSESSED",
    }
