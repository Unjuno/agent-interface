"""Predeclared coarse ordinal response screen; not a CFA/IRT estimator."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


MIN_N = 100
THRESHOLD_MARGIN = 0.15
ASSOCIATION_MARGIN = 0.22


def cumulative_differences(a: list[list[int]], b: list[list[int]], items: int) -> list[float]:
    out = []
    for j in range(items):
        worst = 0.0
        for cut in range(4):
            pa = sum(row[j] <= cut for row in a) / len(a)
            pb = sum(row[j] <= cut for row in b) / len(b)
            worst = max(worst, abs(pa - pb))
        out.append(worst)
    return out


def correlations(rows: list[list[int]], items: int) -> dict[str, float]:
    means = [sum(row[j] for row in rows) / len(rows) for j in range(items)]
    out: dict[str, float] = {}
    for i in range(items):
        for j in range(i + 1, items):
            cov = sum((row[i] - means[i]) * (row[j] - means[j]) for row in rows) / len(rows)
            vi = sum((row[i] - means[i]) ** 2 for row in rows) / len(rows)
            vj = sum((row[j] - means[j]) ** 2 for row in rows) / len(rows)
            out[f"{i}-{j}"] = 0.0 if vi == 0.0 or vj == 0.0 else cov / (vi * vj) ** 0.5
    return out


def classify(fixture: dict[str, Any], item_count: int) -> dict[str, Any]:
    a, b = fixture["groups"]["A"], fixture["groups"]["B"]
    if len(a) < MIN_N or len(b) < MIN_N:
        return {"fixture_id": fixture["fixture_id"], "classification": "UNCERTAIN", "reason": "UNDERPOWERED_N", "threshold_items": [], "association_edges": []}
    td = cumulative_differences(a, b, item_count)
    threshold_items = [i for i, difference in enumerate(td) if difference > THRESHOLD_MARGIN]
    if threshold_items:
        return {"fixture_id": fixture["fixture_id"], "classification": "THRESHOLD_NONINVARIANCE", "reason": "CUMULATIVE_CATEGORY_DIFFERENCE", "threshold_items": threshold_items, "association_edges": []}
    ca, cb = correlations(a, item_count), correlations(b, item_count)
    edges = sorted(key for key in ca if abs(ca[key] - cb[key]) > ASSOCIATION_MARGIN)
    if not edges:
        label, reason, localization = "COMPATIBLE_SCREEN", "NO_GROSS_MOMENT_DIFFERENCE", []
    else:
        endpoints = [set(map(int, key.split("-"))) for key in edges]
        common = set.intersection(*endpoints)
        if len(edges) >= 3 and len(common) == 1:
            label, reason, localization = "LOADING_PATTERN_NONINVARIANCE", "SINGLE_ITEM_STAR", sorted(common)
        else:
            label, reason, localization = "STRUCTURE_NONINVARIANCE", "NON_STAR_ASSOCIATION_PATTERN", []
    return {"fixture_id": fixture["fixture_id"], "classification": label, "reason": reason, "threshold_items": [], "loading_items": localization, "association_edges": edges, "threshold_differences": [round(x, 12) for x in td], "association_differences": {k: round(abs(ca[k] - cb[k]), 12) for k in sorted(ca)}}


def analyze(fixtures: dict, fixture_bytes: bytes) -> dict:
    rows = [classify(fixture, fixtures["item_count"]) for fixture in fixtures["fixtures"]]
    return {"schema": "issue8502-t0-a01-candidate-v1", "fixture_sha256": hashlib.sha256(fixture_bytes).hexdigest(), "parameters": {"min_n_per_group": MIN_N, "threshold_margin": THRESHOLD_MARGIN, "association_margin": ASSOCIATION_MARGIN}, "results": rows}


def main() -> None:
    root = Path(__file__).resolve().parent
    fixture_bytes = (root / "fixtures.json").read_bytes()
    result = analyze(json.loads(fixture_bytes), fixture_bytes)
    payload = (json.dumps(result, sort_keys=True, separators=(",", ":"), ensure_ascii=True) + "\n").encode("utf-8")
    with (root / "candidate.json").open("xb") as stream:
        stream.write(payload)
    print(json.dumps({"output": "candidate.json", "fixtures": len(result["results"]), "sha256": hashlib.sha256(payload).hexdigest()}, sort_keys=True))


if __name__ == "__main__":
    main()
