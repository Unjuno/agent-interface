"""Deterministic synthetic raw-row constructor; imports no auditor."""
import json


def build_raw(expected_inventory):
    records = []
    for index, item in enumerate(expected_inventory):
        started = 100 + index * 100
        records.append({
            "event": "owner_key_release_bracket",
            "schema": "owner-key-release-bracket-v2",
            **item,
            "request_started_ns": started,
            "request_returned_ns": started + 10,
            "shared_sync_returned_ns": started + 20,
            "timing_valid": True,
            "grants_input_authority": False,
            "physical_key_up_claimed": False,
        })
    return {"schema": "owner-keyup-audit-t0-raw-v2", "records": records}


if __name__ == "__main__":
    with open("expected_inventory.json", encoding="utf-8") as source:
        expected = json.load(source)
    print(json.dumps(build_raw(expected), sort_keys=True, separators=(",", ":")))
