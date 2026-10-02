"""Four-case candidate simulator for the frozen Issue #5442 T8 allocation."""
import copy
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
ALLOCATION = "SEMANTIC-RECEIPT-5442-T8-ORBSTACK-20261002-01"


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")


def digest(value):
    return hashlib.sha256(value).hexdigest()


def run(source_bytes):
    fixture = json.loads(source_bytes)
    out_rows = []
    for scenario in fixture["scenarios"]:
        intent = scenario["intent"]
        dispatch = scenario["dispatch"]
        objects = copy.deepcopy(scenario["initial_objects"])
        dispatch_object = objects[dispatch["target_id"]]
        dispatch_pre = dispatch_object["version"]
        if dispatch["accepted"] and dispatch["effect_mode"] == "apply_goal":
            dispatch_object["state"] = copy.deepcopy(intent["goal"])
            dispatch_object["version"] += 1

        observed = objects[scenario["observer"]["target_id"]]
        receipt = {
            "intent": {
                "target_id": intent["target_id"],
                "pre_version": intent["pre_version"],
                "goal_sha256": digest(canonical(intent["goal"])),
            },
            "dispatch": {
                "accepted": dispatch["accepted"],
                "target_id": dispatch["target_id"],
                "observed_pre_version": dispatch_pre,
            },
            "endpoint": {
                "observer_id": scenario["observer"]["id"],
                "fresh": scenario["observer"]["fresh"],
                "target_id": scenario["observer"]["target_id"],
                "post_version": observed["version"],
                "state": observed["state"],
            },
        }
        semantically_confirmed = (
            receipt["dispatch"]["accepted"] is True
            and receipt["dispatch"]["target_id"] == receipt["intent"]["target_id"]
            and receipt["dispatch"]["observed_pre_version"] == receipt["intent"]["pre_version"]
            and receipt["endpoint"]["target_id"] == receipt["intent"]["target_id"]
            and receipt["endpoint"]["fresh"] is True
            and receipt["endpoint"]["post_version"] > receipt["intent"]["pre_version"]
            and receipt["endpoint"]["state"] == intent["goal"]
        )
        semantic_status = "SEMANTICALLY_CONFIRMED" if semantically_confirmed else "UNKNOWN"
        out_rows.append({
            "scenario_id": scenario["id"],
            "intermediate_status": "SUCCESS" if dispatch["accepted"] is True else "UNKNOWN",
            "semantic_status": semantic_status,
            "commit_admitted": scenario["action_class"] != "irreversible" or semantically_confirmed,
            "receipt": receipt,
        })
    return {
        "schema": "agent-interface.semantic-receipt-target-binding-raw.v1",
        "allocation": ALLOCATION,
        "scenario_source_sha256": digest(source_bytes),
        "candidate_source_sha256": digest(Path(__file__).read_bytes()),
        "rows": out_rows,
    }


def main():
    source = (ROOT / "scenarios.json").read_bytes()
    print(json.dumps(run(source), sort_keys=True, separators=(",", ":")))


if __name__ == "__main__":
    main()
