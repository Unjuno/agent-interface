#!/usr/bin/env python3
"""Exact finite DAG scheduler for Issue #5734 T0-v2."""

from fractions import Fraction
from itertools import product
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent


def schedule(names, edges, durations, cue):
    predecessors = {name: [] for name in names}
    for before, after in edges:
        predecessors[after].append(before)
    ends = {}
    events = []
    pending = list(names)
    while pending:
        ready = [name for name in pending
                 if all(parent in ends for parent in predecessors[name])]
        if not ready:
            raise ValueError("cyclic or unknown dependency graph")
        for name in ready:
            start = max([Fraction(cue), *(ends[p] for p in predecessors[name])])
            end = start + Fraction(durations[name])
            ends[name] = end
            events.append({"function": name, "duration": durations[name],
                           "start": str(start), "end": str(end), "local_ok": True})
            pending.remove(name)
    return max(ends.values()), events


def run():
    fixture = json.loads((HERE / "fixtures.json").read_text())
    funcs = fixture["functions"]
    names = [f["name"] for f in funcs]
    choices = [range(f["min"], f["max"] + 1) for f in funcs]
    cases = []
    for case in fixture["cases"]:
        if case["oracle"] != "available" or case["deadline_tick"] is None:
            cases.append({"case": case["name"], "status": "HOLD_NO_ORACLE",
                          "enumerated": 0, "deadline_tick": None})
            continue
        rows = []
        for vector in product(*choices):
            durations = dict(zip(names, vector))
            end, events = schedule(names, case["edges"], durations, fixture["cue_tick"])
            rows.append({"completion_tick": str(end), "deadline_miss": end > case["deadline_tick"],
                         "all_local_ok": all(f["min"] <= durations[f["name"]] <= f["max"] for f in funcs),
                         "events": events})
        misses = [r for r in rows if r["deadline_miss"]]
        cases.append({"case": case["name"], "status": "ENUMERATED", "enumerated": len(rows),
                      "deadline_tick": case["deadline_tick"], "deadline_misses": len(misses),
                      "all_misses_local_ok": all(r["all_local_ok"] for r in misses),
                      "max_completion_tick": str(max(Fraction(r["completion_tick"]) for r in rows)),
                      "witness": misses[-1] if misses else None})
    print(json.dumps({"schema": "functional-coupling-t0-v2-result-v1", "cases": cases},
                     sort_keys=True, separators=(",", ":")))


if __name__ == "__main__":
    run()
