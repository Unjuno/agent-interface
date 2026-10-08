"""Candidate simulator for the frozen #5442 four-case container replay."""
import hashlib
import json
from pathlib import Path


HERE = Path(__file__).resolve().parent
SCENARIOS = HERE / "scenarios.json"


def intermediate_policy(scenario):
    return "SUCCESS" if scenario["dispatch"]["accepted"] else "UNKNOWN"


def endpoint_policy(scenario):
    intent = scenario["intent"]
    dispatch = scenario["dispatch"]
    endpoint = scenario["endpoint"]
    exact_effect = (
        dispatch["accepted"] is True
        and dispatch["target"] == intent["target"]
        and dispatch["observed_pre_version"] == intent["pre_version"]
        and endpoint["target"] == intent["target"]
        and endpoint["version"] > intent["pre_version"]
        and endpoint["state"] == intent["goal"]
    )
    return "SEMANTICALLY_CONFIRMED" if exact_effect else "UNKNOWN"


def main():
    source = SCENARIOS.read_bytes()
    fixture = json.loads(source)
    rows = []
    for scenario in fixture["scenarios"]:
        rows.append({
            "scenario_id": scenario["id"],
            "intermediate_status": intermediate_policy(scenario),
            "endpoint_status": endpoint_policy(scenario),
        })
    result = {
        "schema": "agent-interface.semantic-receipt-raw.v1",
        "allocation": "SEMANTIC-RECEIPT-5442-T7-WSLC-20261002-01",
        "candidate_source_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "scenario_source_sha256": hashlib.sha256(source).hexdigest(),
        "rows": rows,
    }
    print(json.dumps(result, sort_keys=True, separators=(",", ":")))


if __name__ == "__main__":
    main()
