"""Matched coverage-gate intervention over candidate-visible observations."""
import json
import sys


def decide(row, contract, coverage_gate_enabled):
    if coverage_gate_enabled:
        if not contract["contract_complete_for_fixture"]:
            return "UNKNOWN"
        if row["surface_family"] not in contract["supported_surface_families"]:
            return "UNKNOWN"
        if not set(contract["required_predicates"]).issubset(
            set(row["covered_predicates"])
        ):
            return "UNKNOWN"
    for predicate in row["covered_predicates"]:
        if predicate not in row["observations"]:
            return "UNKNOWN"
        if row["observations"][predicate] != contract["safe_values"][predicate]:
            return "REFUSE"
    return "ADMIT"


def main():
    fixture = json.load(open(sys.argv[1], encoding="utf-8"))
    contract = json.load(open(sys.argv[2], encoding="utf-8"))
    rows = []
    for row in fixture["rows"]:
        rows.append({
            "id": row["id"],
            "gate_disabled": decide(row, contract, False),
            "gate_enabled": decide(row, contract, True),
        })
    print(json.dumps({"fixture_id": fixture["fixture_id"],
                      "contract_id": contract["contract_id"], "rows": rows},
                     sort_keys=True, separators=(",", ":")))


if __name__ == "__main__":
    main()
