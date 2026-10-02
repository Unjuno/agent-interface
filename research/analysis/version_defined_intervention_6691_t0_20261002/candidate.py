#!/usr/bin/env python3
"""Emit the frozen synthetic version-mixture fixture and descriptive contrasts."""

import json
import sys
from collections import defaultdict
from pathlib import Path


def build_case(equal_effect=False):
    rows = []
    rid = 0
    for a_on in (0, 1):
        for b_on in (0, 1):
            # Fixed, matched B support.  The A-version mix intentionally differs
            # by A coalition; this is the treatment-version composition challenge.
            # Emit replicated raw observations with a deliberately different
            # version mixture between A=0 (version labels retained as controls)
            # and A=1. Off-state versions are randomized independently so that
            # task/effect truth is observable under both named versions.
            aversions = (("a1", 1), ("a2", 1)) if not a_on else (("a1", 8), ("a2", 2))
            bversions = (("b1", 1), ("b2", 1)) if b_on else (("b1", 1),)
            for av, an in aversions:
                for bv, bn in bversions:
                    if a_on and b_on and av == "a2" and bv == "b2":
                        continue  # declared structural zero: infeasible coalition
                    for rep in range(an * bn):
                        rid += 1
                        a_effect = ((5 if equal_effect else (2 if av == "a1" else 8)) * a_on)
                        b_effect = (3 if bv == "b1" else 5) * b_on
                        rows.append({
                            "row_id": f"r{rid:03d}", "a_on": a_on, "b_on": b_on,
                            "a_version": av, "b_version": bv,
                            "task_effect": 10 + a_effect + b_effect,
                            "safety_event": int(a_on and av == "a2"),
                            "attempt_status": "OBSERVED", "feasible": True,
                        })
    # Explicitly retained unresolved records: never imputed into estimates.
    rows.extend([
        {"row_id": "unknown-version", "a_on": 1, "b_on": 0,
         "a_version": "UNKNOWN", "b_version": "off", "task_effect": None,
         "safety_event": None, "attempt_status": "OBSERVED", "feasible": True},
        {"row_id": "missing-attempt", "a_on": 1, "b_on": 0,
         "a_version": "a2", "b_version": "off", "task_effect": None,
         "safety_event": None, "attempt_status": "FAILED_NO_OUTCOME", "feasible": True},
        {"row_id": "structural-zero", "a_on": 1, "b_on": 1,
         "a_version": "a2", "b_version": "b2", "task_effect": None,
         "safety_event": None, "attempt_status": "NOT_ASSIGNED", "feasible": False},
    ])
    return rows


def mean(values):
    return sum(values) / len(values) if values else None


def summarize(rows):
    valid = [r for r in rows if r["attempt_status"] == "OBSERVED"
             and r["feasible"] and r["a_version"] in ("a1", "a2")]
    estimates = {}
    for b_on in (0, 1):
        a0 = [r for r in valid if r["a_on"] == 0 and r["b_on"] == b_on]
        a1 = [r for r in valid if r["a_on"] == 1 and r["b_on"] == b_on]
        if not a0 or not a1:
            estimates[str(b_on)] = {"pooled": None, "standardized": "UNKNOWN"}
            continue
        pooled = mean([r["task_effect"] for r in a1]) - mean([r["task_effect"] for r in a0])
        # Equal weight over joint A/B-version cells observed in both coalitions.
        cells0 = {(r["a_version"], r["b_version"]): r["task_effect"] for r in a0}
        cells1 = {(r["a_version"], r["b_version"]): r["task_effect"] for r in a1}
        common_cells = sorted(set(cells0) & set(cells1))
        if not common_cells:
            standardized = "UNKNOWN"
        else:
            standardized = sum(cells1[cell] - cells0[cell] for cell in common_cells) / len(common_cells)
        estimates[str(b_on)] = {"pooled": pooled, "standardized": standardized,
                                "common_version_cells": [list(c) for c in common_cells]}
    return estimates


def main(outdir):
    cases = {"equal_effect": build_case(equal_effect=True),
             "version_interaction": build_case(equal_effect=False)}
    result = {"schema": "version-defined-intervention-t0-v1", "cases": {
        name: {"raw_rows": rows, "estimates": summarize(rows)} for name, rows in cases.items()
    }}
    Path(outdir).mkdir(parents=True, exist_ok=True)
    raw_only = {name: {"raw_rows": value["raw_rows"]} for name, value in result["cases"].items()}
    (Path(outdir) / "raw.json").write_text(json.dumps(raw_only, sort_keys=True, indent=2) + "\n")
    (Path(outdir) / "candidate.json").write_text(json.dumps(result, sort_keys=True, indent=2) + "\n")
    print(json.dumps({"cases": {k: v["estimates"] for k, v in result["cases"].items()},
                      "rows": {k: len(v) for k, v in cases.items()}}, sort_keys=True))


if __name__ == "__main__":
    main(sys.argv[1])
