"""Independent reconstruction of the hidden 2-D plant and frozen decision gate."""
from __future__ import annotations

import hashlib
import json
import math
import random
from pathlib import Path

ROOT = Path(__file__).parent
P = json.loads((ROOT / "protocol.json").read_text())


def independent_plant(seed, condition):
    """Reconstruct hidden fixture independently; intentionally duplicates frozen rule."""
    rng = random.Random(seed * 117 + len(condition) * 7919)
    if condition == "constant":
        return [[1.0, 0.0], [0.0, 1.0]]
    if condition == "gain_drift":
        return [[rng.uniform(0.58, 1.52), 0.0], [0.0, rng.uniform(0.58, 1.52)]]
    a, b = rng.uniform(0.72, 1.28), rng.uniform(0.72, 1.28)
    c, d = rng.uniform(-0.30, 0.30), rng.uniform(-0.30, 0.30)
    if condition == "cross_coupling":
        c, d = rng.uniform(-0.38, 0.38), rng.uniform(-0.38, 0.38)
    return [[a, c], [d, b]]


def audit_rows(rows):
    errors = []
    expected = {(c, s, a) for c in P["conditions"] for s in range(30) for a in P["arms"]}
    got = [(r.get("condition"), r.get("seed"), r.get("arm")) for r in rows]
    if set(got) != expected or len(got) != len(expected):
        errors.append("PAIR_GRID_INCOMPLETE_OR_DUPLICATE")
    for row in rows:
        condition, seed, arm = row["condition"], row["seed"], row["arm"]
        matrix = independent_plant(seed, condition)
        state = [0.0, 0.0]
        err = list(row["start_error"])
        for i, action in enumerate(row["actions"]):
            if math.hypot(*action) > P["max_action_norm"] + 1e-9:
                errors.append(f"ACTION_BOUND:{condition}:{seed}:{arm}:{i}")
            before = err
            for k in range(2):
                delta = sum(matrix[k][j] * action[j] for j in range(2))
                if condition == "saturation":
                    delta = max(-5.0, min(5.0, delta))
                state[k] += delta
            err = [row["start_error"][k] - state[k] for k in range(2)]
            try:
                cand_row = row["candidate"]["rows"][i]
                if cand_row["before"] != before or cand_row["after"] != err or cand_row["action"] != action:
                    errors.append(f"TRACE_MISMATCH:{condition}:{seed}:{arm}:{i}")
            except (IndexError, KeyError):
                errors.append(f"MISSING_EVENT:{condition}:{seed}:{arm}:{i}")
        terminal = math.hypot(*err)
        if abs(terminal - row["terminal_error"]) > 1e-9:
            errors.append(f"TERMINAL_MISMATCH:{condition}:{seed}:{arm}")
        if (terminal <= P["target_tolerance_pixels"]) != row["goal_reached"]:
            errors.append(f"ORACLE_MISMATCH:{condition}:{seed}:{arm}")
        if row["safety_violation"]:
            errors.append(f"SAFETY_VIOLATION:{condition}:{seed}:{arm}")
        if len(row["actions"]) != row["candidate"]["corrections"]:
            errors.append(f"CORRECTION_COUNT_MISMATCH:{condition}:{seed}:{arm}")
    by = {(r["condition"], r["seed"], r["arm"]): r for r in rows}
    paired = {}
    for condition in P["conditions"]:
        pairs = []
        for seed in range(30):
            f = by[(condition, seed, "fixed_gain")]
            j = by[(condition, seed, "online_jacobian")]
            if f["goal_reached"] != j["goal_reached"]:
                errors.append(f"GOAL_NONMATCH:{condition}:{seed}")
            pairs.append((f["candidate"]["corrections"], j["candidate"]["corrections"]))
        paired[condition] = pairs
    subset = [pair for c in P["adaptation_subset"] for pair in paired[c]]
    # Aggregate paired total corrections; every pair has a valid independent terminal outcome.
    fixed_total = sum(x for x, _ in subset)
    adaptive_total = sum(y for _, y in subset)
    improvement = 1.0 - adaptive_total / fixed_total if fixed_total else 0.0
    same_outcomes = all(by[(c, s, "fixed_gain")]["goal_reached"] ==
                        by[(c, s, "online_jacobian")]["goal_reached"]
                        for c in P["conditions"] for s in range(30))
    reached = all(r["goal_reached"] for r in rows)
    status = ("PASS_METHOD_SCOPED" if not errors and same_outcomes and reached
              and improvement >= P["required_improvement_fraction"] else
              "FAIL_NO_GAIN" if not errors and same_outcomes and not any(r["safety_violation"] for r in rows)
              else "HOLD_AUDIT_OR_OUTCOME")
    return {"status": status, "errors": errors, "rows": len(rows),
            "paired_conditions": {c: 30 for c in P["conditions"]},
            "all_goals_reached": reached, "same_goal_outcomes": same_outcomes,
            "adaptation_subset": P["adaptation_subset"], "fixed_corrections": fixed_total,
            "online_jacobian_corrections": adaptive_total,
            "correction_reduction_fraction": improvement,
            "per_condition_totals": {c: {"fixed": sum(x for x, _ in paired[c]),
                "online_jacobian": sum(y for _, y in paired[c])} for c in P["conditions"]},
            "safety_violations": sum(bool(r["safety_violation"]) for r in rows)}


def main():
    path = ROOT / "formal_01/RAW.jsonl"
    rows = [json.loads(line) for line in path.read_text().splitlines()]
    result = audit_rows(rows)
    result["raw_sha256"] = hashlib.sha256(path.read_bytes()).hexdigest()
    (ROOT / "formal_01/AUDIT.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))
    if result["status"] != "PASS_METHOD_SCOPED":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
