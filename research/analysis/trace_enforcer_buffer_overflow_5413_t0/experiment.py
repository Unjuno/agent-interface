"""Finite buffer-overflow experiment for Issue #5413 (construction only)."""

import json
import sys


CASES = {
    "exact_control": [
        {"kind": "OBSERVE", "target": "t", "epoch": 7},
        {"kind": "AUTHORITY", "target": "t", "epoch": 7},
    ],
    "dropped_mutation": [
        {"kind": "OBSERVE", "target": "t", "epoch": 7},
        {"kind": "AUTHORITY", "target": "t", "epoch": 7},
        {"kind": "EXTERNAL_MUTATION", "target": "t", "epoch": 8},
    ],
    "irrelevant_overflow": [
        {"kind": "OBSERVE", "target": "t", "epoch": 7},
        {"kind": "AUTHORITY", "target": "t", "epoch": 7},
        {"kind": "TELEMETRY", "target": "other", "epoch": 1},
    ],
}
COMMIT = {"kind": "COMMIT", "target": "t", "epoch": 7}
CAPACITY = 2


def enforce(events, commit, capacity=CAPACITY, policy="FAIL_CLOSED"):
    overflow = len(events) > capacity
    retained = events[:capacity] if policy == "DROP_NEWEST" else events
    if overflow and policy == "FAIL_CLOSED":
        decision = "UNKNOWN_BUFFER_OVERFLOW"
    else:
        observations = [e for e in retained if e["kind"] == "OBSERVE"]
        authorities = [e for e in retained if e["kind"] == "AUTHORITY"]
        mutation = any(e["kind"] == "EXTERNAL_MUTATION" for e in retained)
        matched = any(
            o["target"] == commit["target"] == a["target"]
            and o["epoch"] == commit["epoch"] == a["epoch"]
            for o in observations
            for a in authorities
        )
        decision = "PASS" if matched and not mutation else "BLOCK"
    return {
        "decision": decision,
        "effect_emitted": decision == "PASS",
        "overflow": overflow,
        "retained_event_kinds": [e["kind"] for e in retained],
    }


def run():
    for case_id, events in CASES.items():
        for policy in ("FAIL_CLOSED", "DROP_NEWEST"):
            result = enforce(events, COMMIT, policy=policy)
            yield {
                "case_id": case_id,
                "policy": policy,
                "capacity": CAPACITY,
                "events": events,
                "commit": COMMIT,
                **result,
            }


if __name__ == "__main__":
    for row in run():
        print(json.dumps(row, sort_keys=True, separators=(",", ":")))
