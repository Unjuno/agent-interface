"""Independent raw-only auditor; deliberately does not import candidate.py."""
import json
import sys


def reconstruct(row, contract, gate_enabled):
    if gate_enabled:
        if contract.get("contract_complete_for_fixture") is not True:
            return "UNKNOWN"
        if row.get("surface_family") not in contract.get("supported_surface_families", []):
            return "UNKNOWN"
        if not set(contract.get("required_predicates", [])).issubset(
            set(row.get("covered_predicates", []))
        ):
            return "UNKNOWN"
    observations = row.get("observations", {})
    for predicate in row.get("covered_predicates", []):
        if predicate not in observations:
            return "UNKNOWN"
        if observations[predicate] != contract.get("safe_values", {}).get(predicate):
            return "REFUSE"
    return "ADMIT"


def main():
    fixture = json.load(open(sys.argv[1], encoding="utf-8"))
    contract = json.load(open(sys.argv[2], encoding="utf-8"))
    oracle = json.load(open(sys.argv[3], encoding="utf-8"))
    raw = json.load(open(sys.argv[4], encoding="utf-8"))
    errors = []
    expected_ids = [row["id"] for row in fixture["rows"]]
    raw_rows = raw.get("rows", [])
    if raw.get("fixture_id") != fixture.get("fixture_id"):
        errors.append("fixture_identity_mismatch")
    if raw.get("contract_id") != contract.get("contract_id"):
        errors.append("contract_identity_mismatch")
    if [row.get("id") for row in raw_rows] != expected_ids:
        errors.append("row_identity_or_order_mismatch")
    by_id = {row.get("id"): row for row in raw_rows}
    labels = {row["id"]: row["effect"] for row in oracle["labels"]}
    if set(labels) != set(expected_ids):
        errors.append("oracle_identity_set_mismatch")
    for row in fixture["rows"]:
        observed = by_id.get(row["id"], {})
        for field, enabled in (("gate_disabled", False), ("gate_enabled", True)):
            if observed.get(field) != reconstruct(row, contract, enabled):
                errors.append("decision_mismatch:" + row["id"] + ":" + field)
    decisions = by_id
    hidden_harm = decisions.get("hidden_modal_harmful_incomplete_coverage", {})
    hidden_safe = decisions.get("hidden_modal_safe_incomplete_coverage", {})
    if hidden_harm.get("gate_disabled") != "ADMIT" or labels.get("hidden_modal_harmful_incomplete_coverage") != "harmful":
        errors.append("no_gate_harmful_admission_not_reproduced")
    if hidden_harm.get("gate_enabled") != "UNKNOWN":
        errors.append("gate_did_not_hold_hidden_harm")
    if hidden_safe.get("gate_enabled") != "UNKNOWN":
        errors.append("indistinguishable_safe_control_not_unknown")
    for field in ("gate_disabled", "gate_enabled"):
        if hidden_harm.get(field) != hidden_safe.get(field):
            errors.append("indistinguishable_pair_decisions_diverged:" + field)
    if decisions.get("valid_complete_coverage", {}).get("gate_enabled") != "ADMIT":
        errors.append("complete_valid_control_not_admitted")
    if decisions.get("known_stale_complete_coverage", {}).get("gate_enabled") != "REFUSE":
        errors.append("known_harm_not_refused")
    if decisions.get("unregistered_surface_family", {}).get("gate_enabled") != "UNKNOWN":
        errors.append("unsupported_family_not_unknown")
    result = "PASS_COVERAGE_GATE_ISOLATED_SCOPED" if not errors else "FAIL_AUDIT"
    print(json.dumps({"result": result, "row_count": len(expected_ids), "errors": errors},
                     sort_keys=True, separators=(",", ":")))
    raise SystemExit(0 if not errors else 1)


if __name__ == "__main__":
    main()
