#!/usr/bin/env python3
"""Recompute frozen predecessor current-only and velocity decisions."""
import argparse
import hashlib
import json
from pathlib import Path

EXPECTED_SHA = "49f9204bde9fa72349da82a93a4bb0ffccd93cc213319070c94587ca5e1e8184"


def expected(case, policy):
    state = case["state"]
    if not case["current_valid"]:
        return "YIELD"
    if state == "SELF_CORRECTING":
        return "NO_OP"
    if state == "UNCERTAIN":
        return "YIELD"
    p2 = case["scores"][2]
    if policy == "CURRENT_ONLY" or case["history_status"] != "VALID":
        return "ACTION" if p2 >= 0.75 else "YIELD"
    t1, t2 = case["times_ms"][1:]
    dt = (t2 - t1) / 100.0
    if dt <= 0:
        raise ValueError("non-positive sampling interval")
    velocity = (case["scores"][2] - case["scores"][1]) / dt
    return "ACTION" if (p2 >= 0.75 or (p2 >= 0.55 and velocity >= 0.20)) else "YIELD"


def run(raw_path, out_path):
    raw_bytes = raw_path.read_bytes()
    digest = hashlib.sha256(raw_bytes).hexdigest()
    if digest != EXPECTED_SHA:
        raise ValueError(f"predecessor raw hash mismatch: {digest}")
    rows = [json.loads(line) for line in raw_bytes.decode().splitlines()]
    if len(rows) != 84:
        raise ValueError(f"expected 84 rows, got {len(rows)}")
    changed, metrics = [], {}
    for policy in ("CURRENT_ONLY", "LEVEL_PLUS_VELOCITY"):
        correct = false_action = 0
        for row in rows:
            case = row["input"]
            actual = row["predictions"][policy]["decision"]
            fixed = expected(case, policy)
            if policy == "LEVEL_PLUS_VELOCITY" and fixed != actual:
                changed.append({"case_id": case["case_id"], "family": case["family"], "predecessor": actual, "frozen_spec": fixed})
            correct += fixed == case["truth"]
            false_action += fixed == "ACTION" and case["truth"] != "ACTION"
        metrics[policy] = {"typed_accuracy": correct, "false_action": false_action}
    out_path.mkdir(parents=True, exist_ok=False)
    result = {
        "allocation": "confidence-trajectory-4597-rule-reconciliation-20260927-01",
        "classification": "FROZEN_RULE_REANALYSIS_NOT_NEW_OBSERVATIONS",
        "input_sha256": digest,
        "rows": len(rows),
        "changed_velocity_rows": changed,
        "metrics": metrics,
    }
    (out_path / "reanalysis.json").write_text(json.dumps(result, sort_keys=True, indent=2) + "\n")
    print(json.dumps({"rows": len(rows), "changed": len(changed), "metrics": metrics}, sort_keys=True))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("raw", type=Path)
    parser.add_argument("out", type=Path)
    args = parser.parse_args()
    run(args.raw, args.out)
