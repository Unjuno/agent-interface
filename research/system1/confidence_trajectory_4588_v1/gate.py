#!/usr/bin/env python3
"""Frozen first-rung scientific gates, separate from row-integrity audit."""
from __future__ import annotations

import argparse
import json
from pathlib import Path


def evaluate(rows: list[dict]) -> dict:
    by_id = {row["input"]["case_id"]: row for row in rows}
    checks = {}
    alias_pairs = []
    for rep in range(6):
        good = by_id[f"second_order_alias_action-{rep:02d}"]
        ambiguous = by_id[f"second_order_alias_yield-{rep:02d}"]
        x, y = good["input"], ambiguous["input"]
        alias_pairs.append(
            x["scores"][2] == y["scores"][2]
            and good["predictions"]["CURRENT_ONLY"]["decision"] == ambiguous["predictions"]["CURRENT_ONLY"]["decision"]
            and good["predictions"]["LEVEL_PLUS_VELOCITY"]["decision"] == ambiguous["predictions"]["LEVEL_PLUS_VELOCITY"]["decision"]
            and good["predictions"]["LEVEL_PLUS_VELOCITY_PLUS_ACCEL"]["decision"] == x["truth"]
            and ambiguous["predictions"]["LEVEL_PLUS_VELOCITY_PLUS_ACCEL"]["decision"] == y["truth"]
        )
    checks["second_order_alias_pairs_6_of_6"] = sum(alias_pairs) == 6

    noops = [r for r in rows if r["input"]["family"] == "self_correcting_noop"]
    checks["explicit_noop_6_of_6_all_arms"] = len(noops) == 6 and all(
        pred["decision"] == "NO_OP" for row in noops for pred in row["predictions"].values()
    )

    invalid = [r for r in rows if r["input"]["history_status"] != "VALID"]
    checks["invalid_history_fallback_18_of_18"] = len(invalid) == 18 and all(
        row["predictions"][policy]["source"] == "CURRENT_ONLY_FALLBACK"
        and row["predictions"][policy]["features_used"] == ["current_confidence"]
        for row in invalid
        for policy in ("LEVEL_PLUS_VELOCITY", "LEVEL_PLUS_VELOCITY_PLUS_ACCEL", "SMOOTHED_TRAJECTORY")
    )

    noise = [r for r in rows if r["input"]["family"] == "oscillatory_acceleration_noise_yield"]
    checks["raw_acceleration_noise_exposes_6_false_actions"] = len(noise) == 6 and all(
        row["predictions"]["LEVEL_PLUS_VELOCITY"]["decision"] == "YIELD"
        and row["predictions"]["LEVEL_PLUS_VELOCITY_PLUS_ACCEL"]["decision"] == "ACTION"
        and row["predictions"]["SMOOTHED_TRAJECTORY"]["decision"] == "YIELD"
        for row in noise
    )

    metrics = {}
    for policy in ("CURRENT_ONLY", "LEVEL_PLUS_VELOCITY", "LEVEL_PLUS_VELOCITY_PLUS_ACCEL", "SMOOTHED_TRAJECTORY"):
        metrics[policy] = {
            "accuracy": sum(row["predictions"][policy]["decision"] == row["input"]["truth"] for row in rows),
            "false_executable": sum(
                row["predictions"][policy]["decision"] == "ACTION" and row["input"]["truth"] != "ACTION"
                for row in rows
            ),
        }
    current, accel = metrics["CURRENT_ONLY"], metrics["LEVEL_PLUS_VELOCITY_PLUS_ACCEL"]
    checks["acceleration_no_worse_than_current_only_on_authored_corpus"] = (
        accel["accuracy"] >= current["accuracy"]
        and accel["false_executable"] <= current["false_executable"]
    )
    passed = len(rows) == 84 and all(checks.values())
    return {
        "disposition": "PASS_SYNTHETIC_DISCRIMINATOR_ONLY" if passed else "HOLD_FIRST_RUNG",
        "rows": len(rows),
        "checks": checks,
        "metrics": metrics,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("raw", type=Path)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    rows = [json.loads(line) for line in args.raw.read_text(encoding="utf-8").splitlines()]
    result = evaluate(rows)
    output = json.dumps(result, sort_keys=True, indent=2) + "\n"
    if args.out:
        args.out.write_text(output, encoding="utf-8")
    print(output, end="")
    return 0 if result["disposition"] == "PASS_SYNTHETIC_DISCRIMINATOR_ONLY" else 1


if __name__ == "__main__":
    raise SystemExit(main())
