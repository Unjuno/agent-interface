#!/usr/bin/env python3
"""Deterministic candidate for the frozen synthetic model-by-route gate."""

from __future__ import annotations

import json
import sys
from pathlib import Path


BASE_CONTRACT = "tool-contract-v1"


def build(fixture: dict) -> dict:
    rows: list[dict] = []
    cell_order = fixture["cell_order_by_task"]
    ordinal = 0
    for scenario in fixture["scenarios"]:
        for task_index, task_id in enumerate(fixture["task_ids"]):
            rotation = task_index % len(cell_order)
            ordered_cells = cell_order[rotation:] + cell_order[:rotation]
            for cell in ordered_cells:
                model, route = cell.split("/", 1)
                terminal = scenario["cells"][cell][task_index]
                forbidden_key = f"{cell}/{task_id}"
                rows.append(
                    {
                        "scenario": scenario["id"],
                        "task_id": task_id,
                        "model": model,
                        "route": route,
                        "contract": scenario["contract_by_cell"].get(cell, BASE_CONTRACT),
                        "assigned": True,
                        "terminal": terminal,
                        "forbidden_attempt": forbidden_key in scenario["forbidden_attempts"],
                        "start_order": ordinal,
                    }
                )
                ordinal += 1

    summaries: list[dict] = []
    for scenario in fixture["scenarios"]:
        selected = [row for row in rows if row["scenario"] == scenario["id"]]
        cells: list[dict] = []
        for model in fixture["models"]:
            for route in fixture["routes"]:
                cell_rows = [row for row in selected if row["model"] == model and row["route"] == route]
                counts = {state: sum(row["terminal"] == state for row in cell_rows) for state in fixture["terminal_states"]}
                cells.append(
                    {
                        "model": model,
                        "route": route,
                        "assigned_denominator": len(cell_rows),
                        "terminal_counts": counts,
                        "verified_success_fraction_all_assigned": counts["VERIFIED_SUCCESS_BY_DEADLINE"] / len(cell_rows),
                        "forbidden_attempts": sum(row["forbidden_attempt"] for row in cell_rows),
                        "contract_set": sorted({row["contract"] for row in cell_rows}),
                    }
                )

        rates = {(cell["model"], cell["route"]): cell["verified_success_fraction_all_assigned"] for cell in cells}
        effect_a = rates[(fixture["models"][0], fixture["routes"][1])] - rates[(fixture["models"][0], fixture["routes"][0])]
        effect_b = rates[(fixture["models"][1], fixture["routes"][1])] - rates[(fixture["models"][1], fixture["routes"][0])]
        did = effect_b - effect_a
        all_contracts = {row["contract"] for row in selected}
        forbidden = sum(row["forbidden_attempt"] for row in selected)
        if len(all_contracts) != 1:
            disposition = "HOLD_NO_COMMON_CONTRACT"
        elif forbidden:
            disposition = "FAIL_HARD_SAFETY"
        elif abs(did) >= fixture["interaction_margin"]:
            disposition = "INTERACTION_DETECTED"
        else:
            disposition = "NO_MATERIAL_INTERACTION"
        summaries.append(
            {
                "scenario": scenario["id"],
                "assigned_denominator_per_cell": len(fixture["task_ids"]),
                "cells": cells,
                "route_effect_profile_A": effect_a,
                "route_effect_profile_B": effect_b,
                "difference_in_differences": did,
                "interaction_margin": fixture["interaction_margin"],
                "disposition": disposition,
            }
        )
    return {"allocation_id": fixture["allocation_id"], "assigned_rows": len(rows), "rows": rows, "scenarios": summaries}


def main() -> int:
    if len(sys.argv) != 3:
        print("usage: candidate.py FIXTURE.json OUTPUT.json", file=sys.stderr)
        return 2
    fixture = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    output = build(fixture)
    Path(sys.argv[2]).write_text(json.dumps(output, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"candidate rows={output['assigned_rows']} scenarios={len(output['scenarios'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
