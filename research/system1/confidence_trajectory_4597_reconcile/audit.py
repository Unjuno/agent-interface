#!/usr/bin/env python3
"""Independent raw-input reconstruction audit; does not import reanalyze.py."""
import hashlib
import json
import sys
from pathlib import Path

EXPECTED_SHA = "49f9204bde9fa72349da82a93a4bb0ffccd93cc213319070c94587ca5e1e8184"


def reconstruct(case, policy):
    if not case["current_valid"]:
        return "YIELD"
    if case["state"] == "SELF_CORRECTING":
        return "NO_OP"
    if case["state"] == "UNCERTAIN":
        return "YIELD"
    p2 = case["scores"][2]
    if policy == "CURRENT_ONLY" or case["history_status"] != "VALID":
        return "ACTION" if p2 >= 0.75 else "YIELD"
    dt = (case["times_ms"][2] - case["times_ms"][1]) / 100.0
    if dt <= 0:
        raise ValueError("non-positive sampling interval")
    velocity = (case["scores"][2] - case["scores"][1]) / dt
    return "ACTION" if p2 >= 0.75 or (p2 >= 0.55 and velocity >= 0.20) else "YIELD"


def audit_data(raw_bytes, result):
    errors = []
    digest = hashlib.sha256(raw_bytes).hexdigest()
    if digest != EXPECTED_SHA or result.get("input_sha256") != digest:
        errors.append("input_sha256")
    rows = [json.loads(line) for line in raw_bytes.decode().splitlines()]
    if len(rows) != 84 or result.get("rows") != len(rows):
        errors.append("row_count")
    if result.get("classification") != "FROZEN_RULE_REANALYSIS_NOT_NEW_OBSERVATIONS":
        errors.append("classification")
    expected_changed = []
    metrics = {}
    for policy in ("CURRENT_ONLY", "LEVEL_PLUS_VELOCITY"):
        correct = false_action = 0
        for row in rows:
            case = row["input"]
            expected = reconstruct(case, policy)
            actual = row["predictions"][policy]["decision"]
            truth = case["truth"]
            correct += expected == truth
            false_action += expected == "ACTION" and truth != "ACTION"
            if policy == "LEVEL_PLUS_VELOCITY" and expected != actual:
                expected_changed.append({"case_id": case["case_id"], "family": case["family"], "predecessor": actual, "frozen_spec": expected})
        metrics[policy] = {"typed_accuracy": correct, "false_action": false_action}
    if result.get("changed_velocity_rows") != expected_changed:
        errors.append("changed_rows_reconstruction")
    if result.get("metrics") != metrics:
        errors.append("metrics_reconstruction")
    return errors


def main(raw_path, result_path):
    errors = audit_data(Path(raw_path).read_bytes(), json.loads(Path(result_path).read_text()))
    print(json.dumps({"checks": 5, "errors": errors}, sort_keys=True))
    return bool(errors)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1], sys.argv[2]))
