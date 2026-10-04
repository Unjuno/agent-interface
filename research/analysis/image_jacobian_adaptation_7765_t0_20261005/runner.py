"""Deterministic hidden 2-D plant and paired trial runner."""
from __future__ import annotations

import hashlib
import json
import math
import random
from pathlib import Path

from candidate import run_trial

ROOT = Path(__file__).parent
PROTOCOL = json.loads((ROOT / "protocol.json").read_text())


def plant(seed, condition):
    r = random.Random(seed * 117 + len(condition) * 7919)
    if condition == "constant":
        a, b = 1.0, 1.0
        c, d = 0.0, 0.0
    elif condition == "gain_drift":
        a, b = r.uniform(0.58, 1.52), r.uniform(0.58, 1.52)
        c, d = 0.0, 0.0
    else:
        a, b = r.uniform(0.72, 1.28), r.uniform(0.72, 1.28)
        c, d = r.uniform(-0.30, 0.30), r.uniform(-0.30, 0.30)
    if condition == "cross_coupling":
        c, d = r.uniform(-0.38, 0.38), r.uniform(-0.38, 0.38)
    return [[a, c], [d, b]]


def trial(seed, condition, arm):
    rng = random.Random(1000003 + seed * 31 + len(condition))
    target_error = [rng.uniform(-34, 34), rng.uniform(-28, 28)]
    start = list(target_error)
    matrix = plant(seed, condition)
    state = [0.0, 0.0]
    generation = f"viewport-{seed}-{condition}"
    target_id = f"target-{seed}"
    actions = []
    def observe():
        return {"error": [target_error[i] - state[i] for i in range(2)],
                "generation": generation, "target_id": target_id, "fresh": True}
    def act(u):
        actions.append(list(u))
        for i in range(2):
            delta = sum(matrix[i][j] * u[j] for j in range(2))
            if condition == "saturation":
                delta = max(-5.0, min(5.0, delta))
            state[i] += delta
        return {"acknowledged": True}
    result = run_trial(arm, observe, act,
                       max_corrections=PROTOCOL["max_corrections"],
                       tolerance=PROTOCOL["target_tolerance_pixels"],
                       max_action=PROTOCOL["max_action_norm"],
                       gain=PROTOCOL["online_gain"] if arm == "online_jacobian" else PROTOCOL["fixed_gain"])
    actual_error = math.hypot(target_error[0] - state[0], target_error[1] - state[1])
    safety = any(math.hypot(*u) > PROTOCOL["max_action_norm"] + 1e-9 for u in actions)
    return {"seed": seed, "condition": condition, "arm": arm, "start_error": start,
            "plant": matrix, "actions": actions, "candidate": result,
            "terminal_error": actual_error, "goal_reached": actual_error <= PROTOCOL["target_tolerance_pixels"],
            "safety_violation": safety, "generation": generation, "target_id": target_id}


def main():
    rows = [trial(seed, condition, arm)
            for condition in PROTOCOL["conditions"] for seed in range(30)
            for arm in PROTOCOL["arms"]]
    raw = "\n".join(json.dumps(row, sort_keys=True, separators=(",", ":")) for row in rows) + "\n"
    out = ROOT / "formal_01"
    out.mkdir(exist_ok=True)
    (out / "RAW.jsonl").write_text(raw)
    (out / "CANDIDATE_RECEIPT.json").write_text(json.dumps({"exit_code": 0, "rows": len(rows),
        "sha256": hashlib.sha256(raw.encode()).hexdigest(), "stderr": ""}, indent=2) + "\n")
    print(f"rows={len(rows)} sha256={hashlib.sha256(raw.encode()).hexdigest()}")


if __name__ == "__main__":
    main()
