#!/usr/bin/env python3
"""Frozen finite event-DAG enumerator for Issue #5734 T0."""

from fractions import Fraction
from itertools import product
import json
from pathlib import Path


HERE = Path(__file__).resolve().parent


def run():
    fixture = json.loads((HERE / "fixtures.json").read_text())
    funcs = fixture["functions"]
    choices = [range(f["min"], f["max"] + 1) for f in funcs]
    rows = []
    for case in fixture["cases"]:
        if case["oracle"] != "available" or case["deadline_tick"] is None:
            rows.append({"case": case["name"], "status": "HOLD_NO_ORACLE",
                         "enumerated": 0, "deadline_tick": None})
            continue
        schedules = []
        for durations in product(*choices):
            tick = Fraction(fixture["cue_tick"])
            events = []
            for f, duration in zip(funcs, durations):
                start = tick
                tick += Fraction(duration)
                events.append({"function": f["name"], "duration": duration,
                               "start": str(start), "end": str(tick),
                               "local_ok": f["min"] <= duration <= f["max"]})
            schedules.append({"completion_tick": str(tick),
                              "deadline_miss": tick > case["deadline_tick"],
                              "all_local_ok": all(e["local_ok"] for e in events),
                              "events": events})
        misses = [s for s in schedules if s["deadline_miss"]]
        rows.append({"case": case["name"], "status": "ENUMERATED",
                     "enumerated": len(schedules), "deadline_tick": case["deadline_tick"],
                     "deadline_misses": len(misses),
                     "all_misses_local_ok": all(s["all_local_ok"] for s in misses),
                     "max_completion_tick": str(max(Fraction(s["completion_tick"]) for s in schedules)),
                     "witness": misses[-1] if misses else None})
    print(json.dumps({"schema": "functional-coupling-t0-result-v1", "cases": rows},
                     sort_keys=True, separators=(",", ":")))


if __name__ == "__main__":
    run()
