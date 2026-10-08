"""Independent raw-only auditor; does not import candidate.py."""
import copy
import json
from pathlib import Path

ROOT = Path(__file__).parent
ORACLE = {
    "equiv_browser_sheet": ("slack_equivalent", {"verified_direct", "verified_two_step"}, "verified_direct"),
    "equiv_document_lookup": ("slack_equivalent", {"verified_index", "verified_search"}, "verified_index"),
    "equiv_cross_app_cleanup": ("slack_equivalent", {"verified_return", "verified_summary"}, "verified_return"),
    "sensitive_deadline_switch": ("slack_sensitive", {"full_audit", "bounded_check"}, "full_audit", "bounded_check"),
    "impossible_verification": ("impossible_short", {"verified_submit"}, "verified_submit", "YIELD"),
}
MUTATION_ORACLE = {
    "verification_crosses_short_deadline": "FEASIBLE_SET_DIFFERS",
    "lease_expires_in_short_variant": "LEASE_BUDGET_DIFFERS",
    "user_intent_changes": "INTENT_DIFFERS",
}


def independently_compute(case, variant):
    lease = variant.get("lease_seconds", case["lease_seconds"])
    feasible = []
    for route in case["routes"]:
        elapsed = route["action_seconds"] + route["verification_seconds"]
        if (route["safe"] is True and route["effect"] == case["effect"]
                and elapsed <= variant["deadline_seconds"] and elapsed <= lease):
            feasible.append((elapsed, route["id"]))
    route_by_id = {route["id"]: route for route in case["routes"]}
    feasible.sort(key=lambda item: (route_by_id[item[1]].get("quality_cost", 0), item[0], item[1]))
    return {"variant": variant["id"], "intent": variant.get("intent", case["intent"]),
            "lease_seconds": lease, "feasible": [route for _, route in feasible],
            "choice": feasible[0][1] if feasible else "YIELD"}


def classify(case, long, short):
    reasons = []
    if long["intent"] != short["intent"]:
        reasons.append("INTENT_DIFFERS")
    if long["lease_seconds"] != short["lease_seconds"]:
        reasons.append("LEASE_BUDGET_DIFFERS")
    if long["feasible"] != short["feasible"]:
        reasons.append("FEASIBLE_SET_DIFFERS")
    if long["choice"] != short["choice"]:
        reasons.append("ORACLE_CHOICE_DIFFERS")
    return reasons


def apply_mutation(case, mutation):
    changed = copy.deepcopy(case)
    short = changed["variants"][1]
    if mutation == "set_short_deadline_seconds_to_6":
        short["deadline_seconds"] = 6
    elif mutation == "set_short_lease_seconds_to_9":
        short["lease_seconds"] = 9
    elif mutation == "set_short_intent_to_delete_download":
        short["intent"] = "delete_required_download"
    changed["kind"] = "slack_equivalent"
    return changed


def main():
    cases = json.loads((ROOT / "cases.json").read_text(encoding="utf-8"))
    observed = json.loads((ROOT / "candidate.raw.json").read_text(encoding="utf-8"))
    errors = []
    actual_pairs = {row["case_id"]: row for row in observed["pairs"]}
    if set(actual_pairs) != set(ORACLE):
        errors.append("CASE_SET_MISMATCH")
    for case in cases["cases"]:
        kind, expected_long, expected_choice = ORACLE[case["id"]][:3]
        expected_short_choice = ORACLE[case["id"]][3] if len(ORACLE[case["id"]]) == 4 else expected_choice
        actual = actual_pairs.get(case["id"], {})
        long = independently_compute(case, case["variants"][0])
        short = independently_compute(case, case["variants"][1])
        if actual.get("kind") != kind or actual.get("long") != long or actual.get("short") != short:
            errors.append(f"{case['id']}:RAW_RECONSTRUCTION")
        if set(long["feasible"]) != expected_long:
            errors.append(f"{case['id']}:FEASIBLE_ORACLE")
        if long["choice"] != expected_choice or short["choice"] != expected_short_choice:
            errors.append(f"{case['id']}:CHOICE_ORACLE")
        reasons = classify(case, long, short)
        expect_equivalent = kind == "slack_equivalent"
        if (not reasons) != expect_equivalent:
            errors.append(f"{case['id']}:PAIR_CLASSIFICATION")
    by_id = {case["id"]: case for case in cases["cases"]}
    actual_mutations = {row["id"]: row for row in observed["invalid_claimed_equivalent"]}
    if set(actual_mutations) != set(MUTATION_ORACLE):
        errors.append("MUTATION_SET_MISMATCH")
    for mutation in cases["invalid_claimed_equivalent"]:
        altered = apply_mutation(by_id[mutation["base_case"]], mutation["mutation"])
        long = independently_compute(altered, altered["variants"][0])
        short = independently_compute(altered, altered["variants"][1])
        rejection = set(classify(altered, long, short))
        required = MUTATION_ORACLE[mutation["id"]]
        result = actual_mutations.get(mutation["id"], {}).get("result", {})
        if required not in rejection or result.get("equivalent") is not False or required not in result.get("reasons", []):
            errors.append(f"{mutation['id']}:MUTATION_NOT_REJECTED")
    report = {"status": "PASS_METHOD_SCOPED" if not errors else "FAIL_METHOD", "cases": len(ORACLE),
              "mutations": len(MUTATION_ORACLE), "errors": errors,
              "scope": "finite duration/effect/lease enumeration only; no model, human, GUI, behavior, or actual deadline claim"}
    (ROOT / "audit.raw.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report, sort_keys=True))
    raise SystemExit(0 if not errors else 1)


if __name__ == "__main__":
    main()
