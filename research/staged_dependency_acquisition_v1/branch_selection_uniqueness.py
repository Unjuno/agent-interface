#!/usr/bin/env python3
"""Finite counterexample for branch revalidation semantics.

Ground truth permits execution only when the originally selected branch remains
the *unique* matching branch at final admission.
"""
from itertools import product
import json


def score(rows):
    out = {}
    for name in ("selected_truth", "exact_raw", "unique_selection"):
        stale = false_reject = 0
        for row in rows:
            truth = row["ground_truth"]
            pred = row[name]
            if pred and not truth:
                stale += 1
            elif not pred and truth:
                false_reject += 1
        out[name] = {
            "correct": len(rows) - stale - false_reject,
            "stale_accept": stale,
            "false_reject": false_reject,
        }
    return out


def independent_two_branch():
    rows = []
    for x0, y0 in product(range(-3, 4), repeat=2):
        init = [x0 >= 0, y0 >= 0]
        if sum(init) != 1:
            continue
        selected = 0 if init[0] else 1
        for x1, y1 in product(range(-5, 6), repeat=2):
            current = [x1 >= 0, y1 >= 0]
            rows.append({
                "ground_truth": sum(current) == 1 and current[selected],
                "selected_truth": current[selected],
                "exact_raw": x1 == x0 and y1 == y0,
                "unique_selection": sum(current) == 1 and current[selected],
            })
    return rows


def mutually_exclusive_two_branch():
    rows = []
    for x0 in range(-3, 4):
        init = [x0 < 0, x0 >= 0]
        selected = 0 if init[0] else 1
        for x1 in range(-5, 6):
            current = [x1 < 0, x1 >= 0]
            rows.append({
                "ground_truth": sum(current) == 1 and current[selected],
                "selected_truth": current[selected],
                "exact_raw": x1 == x0,
                "unique_selection": sum(current) == 1 and current[selected],
            })
    return rows


def overlapping_same_variable():
    rows = []
    for x0 in range(-3, 6):
        init = [x0 >= 0, x0 <= 2]
        if sum(init) != 1:
            continue
        selected = 0 if init[0] else 1
        for x1 in range(-5, 6):
            current = [x1 >= 0, x1 <= 2]
            rows.append({
                "ground_truth": sum(current) == 1 and current[selected],
                "selected_truth": current[selected],
                "exact_raw": x1 == x0,
                "unique_selection": sum(current) == 1 and current[selected],
            })
    return rows


def main():
    blocks = {
        "independent": independent_two_branch(),
        "mutually_exclusive": mutually_exclusive_two_branch(),
        "overlapping": overlapping_same_variable(),
    }
    summary = {name: {"rows": len(rows), "scores": score(rows)}
               for name, rows in blocks.items()}
    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
