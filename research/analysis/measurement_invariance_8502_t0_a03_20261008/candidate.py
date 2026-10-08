"""A03 candidate: coarse ordinal-response screening, independent of the audit."""
from __future__ import annotations

import argparse
import hashlib
import json
from math import sqrt
from pathlib import Path
from typing import Any

from integrity import load_json, sha256, verify


def max_cutpoint_gap(counts_a: list[int], counts_b: list[int]) -> float:
    """Return max |F_A(k)-F_B(k)| over identical ordinal cutpoints."""
    n_a, n_b = sum(counts_a), sum(counts_b)
    if n_a == 0 or n_b == 0 or len(counts_a) != len(counts_b):
        raise ValueError("nonempty equal-width category counts required")
    run_a = run_b = 0
    gaps = []
    for count_a, count_b in zip(counts_a[:-1], counts_b[:-1]):
        run_a += count_a
        run_b += count_b
        gaps.append(abs(run_a / n_a - run_b / n_b))
    return max(gaps, default=0.0)


def _association_map(rows: list[list[int]], item_count: int) -> dict[str, float]:
    n = len(rows)
    sums = [sum(row[i] for row in rows) for i in range(item_count)]
    squares = [sum(row[i] * row[i] for row in rows) for i in range(item_count)]
    result: dict[str, float] = {}
    for left in range(item_count):
        for right in range(left + 1, item_count):
            cross = sum(row[left] * row[right] for row in rows)
            covariance = n * cross - sums[left] * sums[right]
            variance_left = n * squares[left] - sums[left] * sums[left]
            variance_right = n * squares[right] - sums[right] * sums[right]
            value = 0.0 if variance_left <= 0 or variance_right <= 0 else covariance / sqrt(variance_left * variance_right)
            result[f"{left}-{right}"] = value
    return result


def screen_rows(
    rows_a: list[list[int]], rows_b: list[list[int]], *, min_n: int,
    threshold_margin: float, association_margin: float,
) -> dict[str, Any]:
    if not rows_a or not rows_b or min(map(len, rows_a + rows_b)) == 0:
        raise ValueError("groups must contain nonempty response rows")
    item_count = len(rows_a[0])
    if any(len(row) != item_count for row in rows_a + rows_b):
        raise ValueError("inconsistent item counts")
    if min(len(rows_a), len(rows_b)) < min_n:
        return {"classification": "UNCERTAIN", "threshold_items": [], "loading_items": [], "association_edges": [],
                "diagnostics": {"max_cutpoint_gaps": [], "association_edges": []}}

    threshold_items = []
    cutpoint_gaps = []
    for item in range(item_count):
        counts_a = [sum(row[item] == category for row in rows_a) for category in range(5)]
        counts_b = [sum(row[item] == category for row in rows_b) for category in range(5)]
        gap = max_cutpoint_gap(counts_a, counts_b)
        cutpoint_gaps.append(round(gap, 12))
        if gap > threshold_margin:
            threshold_items.append(item)
    if threshold_items:
        return {"classification": "THRESHOLD_NONINVARIANCE", "threshold_items": threshold_items,
                "loading_items": [], "association_edges": [],
                "diagnostics": {"max_cutpoint_gaps": cutpoint_gaps, "association_edges": []}}

    corr_a = _association_map(rows_a, item_count)
    corr_b = _association_map(rows_b, item_count)
    changed = sorted(edge for edge in corr_a if abs(corr_a[edge] - corr_b[edge]) > association_margin)
    if not changed:
        return {"classification": "COMPATIBLE_SCREEN", "threshold_items": [], "loading_items": [],
                "association_edges": [],
                "diagnostics": {"max_cutpoint_gaps": cutpoint_gaps, "association_edges": []}}
    shared = None
    for edge in changed:
        endpoints = set(map(int, edge.split("-")))
        shared = endpoints if shared is None else shared & endpoints
    if len(changed) >= 3 and shared and len(shared) == 1:
        return {"classification": "LOADING_PATTERN_NONINVARIANCE", "threshold_items": [],
                "loading_items": sorted(shared), "association_edges": changed,
                "diagnostics": {"max_cutpoint_gaps": cutpoint_gaps, "association_edges": changed}}
    return {"classification": "STRUCTURE_NONINVARIANCE", "threshold_items": [],
            "loading_items": [], "association_edges": changed,
            "diagnostics": {"max_cutpoint_gaps": cutpoint_gaps, "association_edges": changed}}


def run(fixtures: dict[str, Any], config: dict[str, Any]) -> dict[str, Any]:
    results = []
    for fixture in fixtures["fixtures"]:
        result = screen_rows(
            fixture["groups"]["A"], fixture["groups"]["B"], min_n=config["min_n_per_group"],
            threshold_margin=config["threshold_margin"], association_margin=config["association_margin"],
        )
        results.append({"fixture_id": fixture["fixture_id"], **result})
    return {"schema": "issue8502-t0-a03-candidate-v1", "parameters": {
        key: config[key] for key in ("min_n_per_group", "threshold_margin", "association_margin")},
        "results": results}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dir", default=".")
    args = parser.parse_args()
    root = Path(args.dir).resolve()
    freeze_raw = (root / "FREEZE.json").read_bytes()
    freeze = json.loads(freeze_raw)
    errors = verify(root, freeze)
    if errors:
        raise SystemExit("SOURCE_OR_INPUT_INTEGRITY_STOP:" + ",".join(errors))
    fixtures = load_json(root, "fixtures.json")
    config = load_json(root, "config.json")
    output = run(fixtures, config)
    output["freeze_sha256"] = sha256(freeze_raw)
    output["fixture_sha256"] = sha256((root / "fixtures.json").read_bytes())
    output["truth_sha256"] = sha256((root / "truth.json").read_bytes())
    encoded = (json.dumps(output, sort_keys=True, separators=(",", ":"), ensure_ascii=True) + "\n").encode()
    with (root / "candidate.json").open("xb") as stream:
        stream.write(encoded)
    print(json.dumps({"decision_rows": len(output["results"]), "output_sha256": sha256(encoded)}, sort_keys=True))


if __name__ == "__main__":
    main()
