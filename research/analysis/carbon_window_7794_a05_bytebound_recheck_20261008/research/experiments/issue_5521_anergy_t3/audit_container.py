#!/usr/bin/env python3
"""Run the independent raw-only audit and its frozen corruption controls."""
import copy
import hashlib
import json
import sys

import audit


def read_records(stream):
    return [json.loads(line) for line in stream if line.strip()]


def rejected(records):
    try:
        audit.validate(records)
    except (KeyError, TypeError, ValueError):
        return True
    return False


def main():
    records = read_records(sys.stdin)
    snapshots = [row for row in records if row.get("type") == "state_snapshot"]
    core = [row for row in records if row.get("type") != "state_snapshot"]
    policies = audit.validate(core)

    if len(snapshots) != 6:
        raise SystemExit("expected one state snapshot for each of six worker segments")
    expected_snapshot_keys = {(policy, segment) for policy in ("clear", "tombstone") for segment in range(3)}
    if {(row["policy"], row["segment"]) for row in snapshots} != expected_snapshot_keys:
        raise SystemExit("state snapshot inventory does not match the two-arm worker schedule")
    exits = {(row["policy"], row["segment"]): row for row in core if row.get("type") == "process_exit"}
    if set(exits) != {(policy, segment) for policy in ("clear", "tombstone") for segment in range(3)}:
        raise SystemExit("worker exit inventory does not match the frozen two-arm restart schedule")
    for snapshot in snapshots:
        key = (snapshot["policy"], snapshot["segment"])
        digest = hashlib.sha256(json.dumps(snapshot["state"], sort_keys=True, separators=(",", ":")).encode()).hexdigest()
        if digest != snapshot["state_sha256"] or exits[key]["state_sha256"] != digest:
            raise SystemExit("state snapshot does not reconcile with its worker exit")
    for row in core:
        if row.get("type") == "restart":
            prior = exits[(row["policy"], {3: 0, 7: 1}[row["tick"]])]
            if prior["state_sha256"] != row["restored_state_sha256"]:
                raise SystemExit("restart state does not reconcile with the preceding worker snapshot")

    disposition_swap = copy.deepcopy(records)
    clear = next(r for r in disposition_swap if r.get("policy") == "clear" and
                 r.get("type") == "transition" and r.get("tick") == 9)
    tombstone = next(r for r in disposition_swap if r.get("policy") == "tombstone" and
                     r.get("type") == "transition" and r.get("tick") == 9)
    clear["disposition"], tombstone["disposition"] = tombstone["disposition"], clear["disposition"]

    expiry_generation = copy.deepcopy(records)
    freeze = expiry_generation[0]
    freeze["events"][7]["gen"] = 1
    schedule = json.dumps(freeze["events"], sort_keys=True, separators=(",", ":")).encode()
    freeze["schedule_sha256"] = hashlib.sha256(schedule).hexdigest()
    for row in expiry_generation:
        if row.get("type") == "transition" and row.get("tick") == 9 and row.get("proposal") == "Q" and row.get("target") == "A":
            row["gen"] = 1

    controls = {
        "expiry_disposition_swap": rejected(disposition_swap),
        "expiry_generation_mutation": rejected(expiry_generation),
    }
    if not all(controls.values()):
        raise SystemExit("independent auditor accepted a preregistered corruption control")
    print(json.dumps({"audit": "PASS_T3_CONTAINER_RAW_ONLY", "rows": len(records),
                      "state_snapshots": len(snapshots),
                      "policies": policies, "corruption_controls_rejected": controls}, sort_keys=True))


if __name__ == "__main__":
    main()
