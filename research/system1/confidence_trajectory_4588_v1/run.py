#!/usr/bin/env python3
"""Run the frozen, authority-neutral confidence-trajectory first rung."""
from __future__ import annotations

import argparse
import hashlib
import json
import platform
import sys
import time
from pathlib import Path


POLICIES = (
    "CURRENT_ONLY",
    "LEVEL_PLUS_VELOCITY",
    "LEVEL_PLUS_VELOCITY_PLUS_ACCEL",
    "SMOOTHED_TRAJECTORY",
)
DELTA = (-0.010, -0.006, -0.002, 0.002, 0.006, 0.010)


def make_cases() -> list[dict]:
    cases = []

    def add_family(name, state, truth, pattern, times=(0, 100, 200), history="VALID"):
        for rep, delta in enumerate(DELTA):
            scores = [round(v + delta, 6) for v in pattern]
            cases.append({
                "case_id": f"{name}-{rep:02d}",
                "family": name,
                "rep": rep,
                "intent_id": "intent-fixed-A",
                "candidate_id": "candidate-fixed-A",
                "state": state,
                "truth": truth,
                "scores": scores,
                "times_ms": list(times),
                "history_status": history,
                "current_valid": True,
            })

    # Matched curvature aliases: p1, p2, and v2 are equal within each rep.
    add_family("second_order_alias_action", "ACTION_REQUIRED", "ACTION", (0.95, 0.70, 0.80))
    add_family("second_order_alias_yield", "ACTION_REQUIRED", "YIELD", (0.45, 0.70, 0.80))
    add_family("low_confidence_rising_action", "ACTION_REQUIRED", "ACTION", (0.14, 0.32, 0.60))
    add_family("high_confidence_falling_yield", "ACTION_REQUIRED", "YIELD", (0.94, 0.87, 0.77))
    add_family("self_correcting_noop", "SELF_CORRECTING", "NO_OP", (0.65, 0.75, 0.90))
    add_family("uncertain_yield", "UNCERTAIN", "YIELD", (0.40, 0.80, 0.55))
    add_family("transient_spike_yield", "ACTION_REQUIRED", "YIELD", (0.40, 0.95, 0.55))
    add_family("irregular_interval_rise_yield", "ACTION_REQUIRED", "YIELD", (0.20, 0.40, 0.65), (0, 20, 180))
    add_family("plateau_action", "ACTION_REQUIRED", "ACTION", (0.80, 0.80, 0.80))
    add_family("overshoot_yield", "ACTION_REQUIRED", "YIELD", (0.70, 0.92, 0.70))
    # The bounce has low current level but a large positive raw second
    # difference. It is an authored stress control, not a sampled noise rate.
    add_family("oscillatory_acceleration_noise_yield", "ACTION_REQUIRED", "YIELD", (0.95, 0.05, 0.53))
    for status, pattern in (
        ("STALE_PREVIOUS", (0.55, 0.72, 0.95)),
        ("MISSING_PREVIOUS", (0.55, 0.72, 0.95)),
        ("EPOCH_MISMATCH", (0.55, 0.72, 0.95)),
    ):
        add_family(f"invalid_history_{status.lower()}", "ACTION_REQUIRED", "ACTION", pattern, history=status)
    return cases


def features(case: dict) -> tuple[float, float, float]:
    p0, p1, p2 = case["scores"]
    t0, t1, t2 = case["times_ms"]
    d0 = (t1 - t0) / 100.0
    d1 = (t2 - t1) / 100.0
    if d0 <= 0 or d1 <= 0:
        raise ValueError("non-positive sampling interval")
    v1 = (p1 - p0) / d0
    v2 = (p2 - p1) / d1
    return v1, v2, v2 - v1


def time_weighted_mean(case: dict) -> float:
    p0, p1, p2 = case["scores"]
    t0, t1, t2 = case["times_ms"]
    area = (p0 + p1) * 0.5 * (t1 - t0) + (p1 + p2) * 0.5 * (t2 - t1)
    return area / (t2 - t0)


def decide(case: dict, policy: str) -> dict:
    if not case["current_valid"]:
        return {"decision": "YIELD", "source": "CURRENT_INVALID", "features_used": []}
    if case["state"] == "SELF_CORRECTING":
        return {"decision": "NO_OP", "source": "CURRENT_STATE", "features_used": ["state"]}
    if case["state"] == "UNCERTAIN":
        return {"decision": "YIELD", "source": "CURRENT_STATE", "features_used": ["state"]}

    p2 = case["scores"][2]
    if policy == "CURRENT_ONLY" or case["history_status"] != "VALID":
        result = "ACTION" if p2 >= 0.75 else "YIELD"
        return {
            "decision": result,
            "source": "CURRENT_ONLY" if policy == "CURRENT_ONLY" else "CURRENT_ONLY_FALLBACK",
            "features_used": ["current_confidence"],
        }

    v1, v2, accel = features(case)
    lv_action = (p2 >= 0.75 and v2 >= 0.0) or (p2 >= 0.55 and v2 >= 0.20)
    if policy == "LEVEL_PLUS_VELOCITY":
        result = "ACTION" if lv_action else "YIELD"
        used = ["current_confidence", "velocity"]
    elif policy == "LEVEL_PLUS_VELOCITY_PLUS_ACCEL":
        accel_rescue = p2 >= 0.50 and v2 >= 0.20 and accel >= 0.50
        result = "ACTION" if (lv_action and accel >= 0.0) or accel_rescue else "YIELD"
        used = ["current_confidence", "velocity", "acceleration"]
    elif policy == "SMOOTHED_TRAJECTORY":
        result = "ACTION" if time_weighted_mean(case) >= 0.75 else "YIELD"
        used = ["causal_time_weighted_mean"]
    else:
        raise ValueError(f"unknown policy: {policy}")
    return {"decision": result, "source": policy, "features_used": used}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--freeze", required=True, type=Path)
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=False)

    started = time.monotonic_ns()
    raw = args.out / "raw.jsonl"
    cases = make_cases()
    with raw.open("w", encoding="utf-8", newline="\n") as stream:
        for case in cases:
            predictions = {p: decide(case, p) for p in POLICIES}
            row = {"input": case, "predictions": predictions}
            stream.write(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n")
    elapsed = time.monotonic_ns() - started

    rows = [json.loads(line) for line in raw.read_text(encoding="utf-8").splitlines()]
    summary = {}
    for policy in POLICIES:
        pred = [r["predictions"][policy]["decision"] for r in rows]
        truth = [r["input"]["truth"] for r in rows]
        executable_false = sum(p == "ACTION" and t != "ACTION" for p, t in zip(pred, truth))
        executable_tp = sum(p == "ACTION" and t == "ACTION" for p, t in zip(pred, truth))
        summary[policy] = {
            "typed_accuracy": sum(p == t for p, t in zip(pred, truth)),
            "rows": len(rows),
            "false_executable": executable_false,
            "false_executable_rate": round(executable_false / len(rows), 6),
            "action_true_positive": executable_tp,
            "action_precision": round(executable_tp / max(1, executable_tp + executable_false), 6),
            "action_recall": round(executable_tp / sum(t == "ACTION" for t in truth), 6),
            "correct_no_op": sum(p == t == "NO_OP" for p, t in zip(pred, truth)),
            "correct_yield": sum(p == t == "YIELD" for p, t in zip(pred, truth)),
        }
    freeze = json.loads(args.freeze.read_text(encoding="utf-8"))
    (args.out / "summary.json").write_text(json.dumps({
        "allocation": freeze["allocation"],
        "case_count": len(rows),
        "policy_order": list(POLICIES),
        "metrics": summary,
        "runner_exit": 0,
        "elapsed_monotonic_ns": elapsed,
    }, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    (args.out / "process.json").write_text(json.dumps({
        "python": sys.version,
        "platform": platform.platform(),
        "machine": platform.machine(),
        "pid": __import__("os").getpid(),
        "exit": 0,
        "elapsed_monotonic_ns": elapsed,
        "raw_sha256": hashlib.sha256(raw.read_bytes()).hexdigest(),
        "freeze_sha256": hashlib.sha256(args.freeze.read_bytes()).hexdigest(),
    }, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"case_count": len(rows), "metrics": summary, "exit": 0}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
