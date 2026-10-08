#!/usr/bin/env python3
"""Independent raw-only reconstruction of the frozen synthetic design."""

from __future__ import annotations

import json
import sys
from pathlib import Path


BASE_CONTRACT = "tool-contract-v1"


def reconstruct(fixture: dict) -> dict:
    expected_rows = []
    sequence = fixture["cell_order_by_task"]
    next_order = 0
    for scenario in fixture["scenarios"]:
        for task_pos, task_id in enumerate(fixture["task_ids"]):
            shift = task_pos % len(sequence)
            permutation = sequence[shift:] + sequence[:shift]
            for pair in permutation:
                model, route = pair.split("/", maxsplit=1)
                cell_outcomes = scenario["cells"][pair]
                marker = f"{pair}/{task_id}"
                expected_rows.append({
                    "scenario": scenario["id"],
                    "task_id": task_id,
                    "model": model,
                    "route": route,
                    "contract": scenario["contract_by_cell"].get(pair, BASE_CONTRACT),
                    "assigned": True,
                    "terminal": cell_outcomes[task_pos],
                    "forbidden_attempt": marker in scenario["forbidden_attempts"],
                    "start_order": next_order,
                })
                next_order += 1

    scenario_summaries = []
    for case in fixture["scenarios"]:
        entries = [entry for entry in expected_rows if entry["scenario"] == case["id"]]
        cells = []
        for model in fixture["models"]:
            for route in fixture["routes"]:
                sample = [entry for entry in entries if entry["model"] == model and entry["route"] == route]
                state_counts = {}
                for state in fixture["terminal_states"]:
                    state_counts[state] = sum(entry["terminal"] == state for entry in sample)
                cell_contracts = sorted({entry["contract"] for entry in sample})
                cells.append({
                    "model": model,
                    "route": route,
                    "assigned_denominator": len(sample),
                    "terminal_counts": state_counts,
                    "verified_success_fraction_all_assigned": state_counts["VERIFIED_SUCCESS_BY_DEADLINE"] / len(sample),
                    "forbidden_attempts": sum(entry["forbidden_attempt"] for entry in sample),
                    "contract_set": cell_contracts,
                })
        lookup = {(cell["model"], cell["route"]): cell["verified_success_fraction_all_assigned"] for cell in cells}
        model_1, model_2 = fixture["models"]
        route_1, route_2 = fixture["routes"]
        effect_1 = lookup[(model_1, route_2)] - lookup[(model_1, route_1)]
        effect_2 = lookup[(model_2, route_2)] - lookup[(model_2, route_1)]
        interaction = effect_2 - effect_1
        contract_values = {entry["contract"] for entry in entries}
        violations = sum(entry["forbidden_attempt"] for entry in entries)
        if len(contract_values) > 1:
            decision = "HOLD_NO_COMMON_CONTRACT"
        elif violations > 0:
            decision = "FAIL_HARD_SAFETY"
        elif abs(interaction) >= fixture["interaction_margin"]:
            decision = "INTERACTION_DETECTED"
        else:
            decision = "NO_MATERIAL_INTERACTION"
        scenario_summaries.append({
            "scenario": case["id"],
            "assigned_denominator_per_cell": len(fixture["task_ids"]),
            "cells": cells,
            "route_effect_profile_A": effect_1,
            "route_effect_profile_B": effect_2,
            "difference_in_differences": interaction,
            "interaction_margin": fixture["interaction_margin"],
            "disposition": decision,
        })
    return {"allocation_id": fixture["allocation_id"], "assigned_rows": len(expected_rows), "rows": expected_rows, "scenarios": scenario_summaries}


def audit(fixture: dict, raw: dict) -> list[str]:
    expected = reconstruct(fixture)
    errors = []
    if raw != expected:
        errors.append("raw output differs from independent all-assigned reconstruction")
    if len(raw.get("rows", [])) != len(fixture["scenarios"]) * len(fixture["task_ids"]) * len(fixture["cell_order_by_task"]):
        errors.append("one or more assigned rows are missing or duplicated")
    for summary in raw.get("scenarios", []):
        if summary.get("assigned_denominator_per_cell") != len(fixture["task_ids"]):
            errors.append("a cell denominator differs from the frozen assigned cohort")
            break
    return errors


def main() -> int:
    if len(sys.argv) != 3:
        print("usage: auditor.py FIXTURE.json RAW.json", file=sys.stderr)
        return 2
    fixture = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    raw = json.loads(Path(sys.argv[2]).read_text(encoding="utf-8"))
    errors = audit(fixture, raw)
    result = {"disposition": "PASS_METHOD_SCOPED" if not errors else "FAIL_AUDIT", "rows_reconstructed": len(raw.get("rows", [])), "errors": errors}
    print(json.dumps(result, sort_keys=True))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
