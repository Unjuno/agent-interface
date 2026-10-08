"""Exact finite decision-contract enumeration for Issue #5428; stdlib only."""
from __future__ import annotations

import itertools
import json
import sys
from pathlib import Path


def decide(case: dict) -> dict:
    if not (case["authorized"] and case["fresh"] and case["hard_safety_pass"] and case["commit_window_open"]):
        decision, reason = "HOLD", "HARD_GATE"
    elif not case["priceable"]:
        decision, reason = "HOLD", "UNPRICEABLE"
    elif case["wait_deadline_remaining"] <= 0 or not case["wait_route"]:
        decision, reason = "COMMIT", "WAIT_UNAVAILABLE"
    else:
        now = case["commit_value"] - case["lost_flexibility_cost"]
        wait = case["future_gross_value"] - case["wait_cost"]
        decision = "COMMIT" if now >= wait else "WAIT"
        reason = "PAIRWISE_NET_VALUE"
    return {"id": case["id"], "decision": decision, "reason": reason}


def enumerate_cases(design: dict) -> list[dict]:
    grid = design["numeric_grid"]
    rows = []
    products = itertools.product(
        grid["commit_value"], grid["future_gross_value"],
        grid["wait_cost"], grid["lost_flexibility_cost"],
    )
    for index, (now, future, wait_cost, lost_flex) in enumerate(products):
        rows.append({
            "id": f"grid-{index:03d}", "authorized": True, "fresh": True,
            "hard_safety_pass": True, "commit_window_open": True, "priceable": True,
            "commit_value": now, "future_gross_value": future,
            "wait_cost": wait_cost, "lost_flexibility_cost": lost_flex,
            "wait_route": True, "wait_deadline_remaining": 1,
            "information_available": True,
        })
    return rows + design["corner_cases"]


def run(design: dict) -> dict:
    cases = enumerate_cases(design)
    return {
        "schema": "real-option-wait-cost-result-v1",
        "allocation": "REAL-OPTION-WAIT-COST-MONOTONICITY-5428-T0-20261003-01",
        "rows": [{**case, **decide(case)} for case in cases],
    }


if __name__ == "__main__":
    design = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    Path(sys.argv[2]).write_text(
        json.dumps(run(design), sort_keys=True, separators=(",", ":")) + "\n",
        encoding="utf-8", newline="\n",
    )
