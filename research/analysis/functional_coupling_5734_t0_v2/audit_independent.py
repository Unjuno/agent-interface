#!/usr/bin/env python3
"""Independent direct graph-time audit; deliberately does not import analyze.py."""

from fractions import Fraction
from itertools import product
import json
from pathlib import Path

fixture = json.loads((Path(__file__).resolve().parent / "fixtures.json").read_text())
functions = fixture["functions"]
names = [item["name"] for item in functions]
domains = [range(item["min"], item["max"] + 1) for item in functions]
expected = {"parallel_control": 0, "coupled_chain": 6}
audit = {}
for case in fixture["cases"]:
    if case["oracle"] == "missing":
        assert case["deadline_tick"] is None
        audit[case["name"]] = "HOLD_NO_ORACLE"
        continue
    predecessor = {name: [] for name in names}
    for source, target in case["edges"]:
        assert source in predecessor and target in predecessor and source != target
        predecessor[target].append(source)
    samples = 0
    violations = 0
    maximum = Fraction(fixture["cue_tick"])
    for assignment in product(*domains):
        duration = dict(zip(names, assignment))
        finish = {}
        todo = set(names)
        while todo:
            available = [n for n in names if n in todo and all(p in finish for p in predecessor[n])]
            assert available, "cycle or unresolved predecessor"
            for n in available:
                begin = max([Fraction(fixture["cue_tick"]), *(finish[p] for p in predecessor[n])])
                finish[n] = begin + Fraction(duration[n])
                todo.remove(n)
        terminal = max(finish.values())
        maximum = max(maximum, terminal)
        samples += 1
        assert all(f["min"] <= duration[f["name"]] <= f["max"] for f in functions)
        violations += terminal > case["deadline_tick"]
    assert samples == 32
    assert violations == expected[case["name"]], (case["name"], violations)
    if case["name"] == "coupled_chain":
        assert maximum == 10 and violations > 0
    else:
        assert maximum == 2
    audit[case["name"]] = {"schedules": samples, "deadline_misses": violations,
                           "max_completion_tick": str(maximum)}

assert audit["missing_effect_oracle"] == "HOLD_NO_ORACLE"
print(json.dumps({"audit": "PASS", "independent_graph_counts": audit,
                  "scope": "synthetic finite T0-v2 only"},
                 sort_keys=True, separators=(",", ":")))
