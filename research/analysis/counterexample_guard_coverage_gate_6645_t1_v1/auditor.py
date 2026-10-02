"""Independent raw-only oracle for the finite coverage-gate allocation."""
import json
import sys


def expected(row, contract):
    registered = row.get("family") in contract.get("required_families", [])
    complete = contract.get("contract_complete_for_fixture") is True
    covered = set(row.get("candidate_covered_families", []))
    required = set(contract.get("required_families", []))
    if not registered or not complete or not required.issubset(covered):
        return "UNKNOWN"
    if row.get("target_freshness") != "current":
        return "REFUSE"
    if row.get("app_mode") != "document":
        return "REFUSE"
    if row.get("modal_occlusion") != "none":
        return "REFUSE"
    return "ADMIT"


def expected_legacy(row):
    if row.get("target_freshness") == "current" and row.get("app_mode") == "document":
        return "ADMIT"
    return "REFUSE"


def main():
    fixture = json.load(open(sys.argv[1], encoding="utf-8"))
    contract = json.load(open(sys.argv[2], encoding="utf-8"))
    raw = json.load(open(sys.argv[3], encoding="utf-8"))
    errors = []
    expected_ids = [row["id"] for row in fixture["rows"]]
    raw_ids = [row.get("id") for row in raw.get("rows", [])]
    if raw.get("fixture_id") != fixture.get("fixture_id"):
        errors.append("fixture_id_mismatch")
    if raw.get("contract_id") != contract.get("contract_id"):
        errors.append("contract_id_mismatch")
    if raw_ids != expected_ids:
        errors.append("row_identity_or_order_mismatch")
    by_id = {row["id"]: row for row in raw.get("rows", []) if "id" in row}
    for row in fixture["rows"]:
        observed = by_id.get(row["id"], {})
        if observed.get("candidate_decision") != expected(row, contract):
            errors.append("candidate_decision_mismatch:" + row["id"])
        if observed.get("legacy_decision") != expected_legacy(row):
            errors.append("legacy_decision_mismatch:" + row["id"])
    decisions = {item.get("id"): item for item in raw.get("rows", [])}
    if decisions.get("valid_complete_coverage", {}).get("candidate_decision") != "ADMIT":
        errors.append("complete_coverage_valid_control_not_admitted")
    if decisions.get("known_stale_target", {}).get("candidate_decision") != "REFUSE":
        errors.append("known_harm_not_refused")
    hidden = decisions.get("hidden_modal_family_harmful", {})
    if hidden.get("legacy_decision") != "ADMIT":
        errors.append("legacy_counterexample_not_exposed")
    if hidden.get("candidate_decision") != "UNKNOWN":
        errors.append("coverage_gate_did_not_fail_closed_on_hidden_family")
    if decisions.get("unregistered_family", {}).get("candidate_decision") != "UNKNOWN":
        errors.append("unregistered_family_not_unknown")
    result = "PASS_COVERAGE_GATE_SCOPED" if not errors else "FAIL_AUDIT"
    print(json.dumps({"result": result, "row_count": len(expected_ids), "errors": errors},
                     sort_keys=True, separators=(",", ":")))
    raise SystemExit(0 if not errors else 1)


if __name__ == "__main__":
    main()
