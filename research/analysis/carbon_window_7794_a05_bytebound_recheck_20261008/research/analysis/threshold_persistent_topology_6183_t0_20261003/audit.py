#!/usr/bin/env python3
"""Independent replay auditor; does not import candidate.py."""
import json
import os
from collections import deque
from pathlib import Path

ROOT = Path(__file__).parent
OUT_DIR = Path(os.environ.get("OUT_DIR", ROOT))


def flood(image, cutoff):
    rows, cols = len(image), len(image[0])
    active = {(col, row) for row in range(rows) for col in range(cols) if image[row][col] > cutoff}
    origin, target = (0, 4), (8, 4)
    pending = [origin] if origin in active else []
    reached = set(pending)
    while pending:
        x, y = pending.pop()
        neighbors = {(x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)} & active - reached
        reached |= neighbors
        pending.extend(neighbors)
    return target in reached


def expected(image, reference):
    delta = sum(abs(int(p) - int(q)) for r, s in zip(image, reference) for p, q in zip(r, s)) / (255.0 * 81)
    return "PRESENT" if delta <= .02 else "ABSENT" if delta >= .10 else "UNKNOWN"


def main():
    cases = json.loads((ROOT / "fixtures.json").read_text())["fixtures"]
    labels = {x["id"]: x for x in json.loads((ROOT / "labels.json").read_text())["labels"]}
    observed = json.loads((OUT_DIR / "candidate.raw.json").read_text())["rows"]
    reference = next(c["pixels"] for c in cases if c["id"] == "clear_connected")
    lookup = {r["case_id"]: r for r in observed}
    errors, scored = [], {name: {"wrong": 0, "confident": 0, "correct": 0} for name in ("pixel", "single", "persistent")}
    for case in cases:
        row = lookup.get(case["id"])
        if row is None:
            errors.append(f"missing:{case['id']}")
            continue
        direct = expected(case["pixels"], reference)
        one = "PRESENT" if flood(case["pixels"], 128) else "ABSENT"
        band = sum(flood(case["pixels"], t) for t in (64, 128, 192, 240))
        persistent = "PRESENT" if band >= 3 else "ABSENT" if band <= 1 else "UNKNOWN"
        replay = {"pixel": direct, "single": one, "persistent": persistent}
        for method, value in replay.items():
            if row.get(method) != value:
                errors.append(f"replay:{case['id']}:{method}")
            truth = labels[case["id"]]["visual_truth"]
            if truth != "UNKNOWN":
                scored[method]["confident"] += value != "UNKNOWN"
                scored[method]["correct"] += value == truth
                scored[method]["wrong"] += value not in ("UNKNOWN", truth)
            elif value != "UNKNOWN":
                scored[method]["wrong"] += 1
        if row.get("application_effect") != "UNKNOWN" or row.get("semantic_oracle_used") is not False:
            errors.append(f"semantic-promotion:{case['id']}")
        if row.get("pixel_visits") != 486:
            errors.append(f"cost:{case['id']}")
    twins = [lookup.get("identical_twin_a"), lookup.get("identical_twin_b")]
    if len(twins) != 2 or any(x is None for x in twins) or any(
        twins[0].get(k) != twins[1].get(k) for k in ("pixel", "single", "persistent", "application_effect")
    ):
        errors.append("identical-image-output-mismatch")
    result = {
        "schema": "topology-6183-independent-audit-v1",
        "rows": len(cases),
        "errors": errors,
        "metrics": scored,
        "thresholds": [64, 128, 192, 240],
        "visual_coverage_on_determinate": {k: v["confident"] / 6 for k, v in scored.items()},
        "persistent_strictly_fewer_false_confident_than_pixel_and_single": (
            scored["persistent"]["wrong"] < scored["pixel"]["wrong"]
            and scored["persistent"]["wrong"] < scored["single"]["wrong"]
        ),
    }
    (OUT_DIR / "audit.json").write_text(json.dumps(result, sort_keys=True, indent=2) + "\n")
    if errors:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
