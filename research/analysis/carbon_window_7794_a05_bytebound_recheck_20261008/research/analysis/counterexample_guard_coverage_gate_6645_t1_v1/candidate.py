"""Coverage-gated admission candidate for the frozen synthetic fixture."""
import json
import sys


def decide(row, contract):
    if row["family"] not in contract["required_families"]:
        return "UNKNOWN"
    if not contract["contract_complete_for_fixture"]:
        return "UNKNOWN"
    if not set(contract["required_families"]).issubset(
        set(row["candidate_covered_families"])
    ):
        return "UNKNOWN"
    if row["target_freshness"] != "current":
        return "REFUSE"
    if row["app_mode"] != "document":
        return "REFUSE"
    if row["modal_occlusion"] != "none":
        return "REFUSE"
    return "ADMIT"


def legacy_decide(row):
    if row["target_freshness"] == "current" and row["app_mode"] == "document":
        return "ADMIT"
    return "REFUSE"


def main():
    fixture_path, contract_path = sys.argv[1:3]
    fixture = json.load(open(fixture_path, encoding="utf-8"))
    contract = json.load(open(contract_path, encoding="utf-8"))
    output = {
        "fixture_id": fixture["fixture_id"],
        "contract_id": contract["contract_id"],
        "rows": [
            {
                "id": row["id"],
                "legacy_decision": legacy_decide(row),
                "candidate_decision": decide(row, contract),
            }
            for row in fixture["rows"]
        ],
    }
    print(json.dumps(output, sort_keys=True, separators=(",", ":")))


if __name__ == "__main__":
    main()
