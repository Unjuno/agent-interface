#!/usr/bin/env python3
"""Independent exhaustive oracle: direct Cartesian sum, no analyzer imports."""

from fractions import Fraction
from itertools import product
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent
fixture = json.loads((ROOT / "fixtures.json").read_text())
names = tuple(item["name"] for item in fixture["functions"])
domains = tuple(tuple(range(item["min"], item["max"] + 1))
                for item in fixture["functions"])
expected = {"uncoupled_control": (32, 0), "coupled_near_boundary": (32, 6)}
observed = {}
for case in fixture["cases"]:
    if case["oracle"] == "missing":
        assert case["deadline_tick"] is None
        observed[case["name"]] = "HOLD_NO_ORACLE"
        continue
    count = 0
    misses = []
    for vector in product(*domains):
        assert len(vector) == len(names)
        assert all(low <= value <= high
                   for value, (low, high) in zip(vector,
                       ((f["min"], f["max"]) for f in fixture["functions"])))
        end_tick = Fraction(fixture["cue_tick"]) + sum(map(Fraction, vector))
        count += 1
        if end_tick > case["deadline_tick"]:
            misses.append((vector, end_tick))
    observed[case["name"]] = (count, len(misses))
    assert observed[case["name"]] == expected[case["name"]], (case, observed[case["name"]])
    if misses:
        witness, end_tick = misses[-1]
        assert all(1 <= value <= 2 for value in witness)
        assert end_tick == 10 and case["deadline_tick"] == 8

assert observed["missing_effect_oracle"] == "HOLD_NO_ORACLE"
print(json.dumps({"audit": "PASS", "independent_counts": observed,
                  "clock_order": "single synthetic monotonic tick domain",
                  "scope": "finite synthetic T0 only"},
                 sort_keys=True, separators=(",", ":")))
