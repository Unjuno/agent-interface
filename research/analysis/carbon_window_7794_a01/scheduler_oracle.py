#!/usr/bin/env python3
"""Tiny exhaustive oracle for deadline/window constrained carbon scheduling."""
from __future__ import annotations

import hashlib
import itertools
import json
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Job:
    name: str
    duration: int
    earliest: int
    latest_finish: int
    energy: int
    predecessors: tuple[str, ...] = ()


def enumerate_schedules(jobs: tuple[Job, ...], intensity: tuple[int, ...]):
    starts = [range(j.earliest, j.latest_finish - j.duration + 1) for j in jobs]
    feasible = []
    for values in itertools.product(*starts):
        schedule = dict(zip((j.name for j in jobs), values))
        occupied = set()
        valid = True
        for j in jobs:
            slots = set(range(schedule[j.name], schedule[j.name] + j.duration))
            if occupied & slots:
                valid = False
                break
            occupied |= slots
            if any(schedule[p] + next(x.duration for x in jobs if x.name == p) > schedule[j.name]
                   for p in j.predecessors):
                valid = False
                break
        if valid:
            cost = sum(j.energy * sum(intensity[t] for t in range(schedule[j.name], schedule[j.name] + j.duration)) for j in jobs)
            feasible.append((cost, tuple(schedule[j.name] for j in jobs)))
    return sorted(feasible)


def heuristic(jobs, intensity, mode):
    # Deterministic serial dispatcher in the declared job order.
    placed = {}
    occupied = set()
    for j in jobs:
        candidates = []
        for start in range(j.earliest, j.latest_finish - j.duration + 1):
            slots = set(range(start, start + j.duration))
            if slots & occupied:
                continue
            if any(placed[p] + next(x.duration for x in jobs if x.name == p) > start for p in j.predecessors):
                continue
            c = j.energy * sum(intensity[t] for t in slots)
            rank = (start if mode == "asap" else -start if mode == "latest" else c, start)
            candidates.append((rank, start, slots))
        if not candidates:
            return None
        _, start, slots = min(candidates)
        placed[j.name] = start
        occupied |= slots
    return tuple(placed[j.name] for j in jobs)


def cost(jobs, starts, intensity):
    return sum(j.energy * sum(intensity[t] for t in range(s, s + j.duration)) for j, s in zip(jobs, starts))


def main():
    jobs = (Job("a", 2, 0, 5, 1), Job("b", 1, 0, 5, 2, ("a",)), Job("c", 1, 0, 5, 1))
    cases = {
        "declining": (9, 7, 5, 3, 1, 1),
        "flat": (4, 4, 4, 4, 4, 4),
        "inverted": (1, 2, 4, 6, 8, 9),
        "tied": (1, 2, 2, 1, 2, 1),
    }
    rows = []
    all_ok = True
    for label, intensity in cases.items():
        oracle = enumerate_schedules(jobs, intensity)
        if not oracle:
            raise AssertionError("control schedule unexpectedly infeasible")
        methods = {m: heuristic(jobs, intensity, m) for m in ("asap", "latest", "carbon_greedy")}
        # Heuristics are subjects under test: a dead end or feasible but
        # non-optimal schedule is a counterexample, not an oracle failure.
        for sched in methods.values():
            if sched is not None and sched not in {s for _, s in oracle}:
                all_ok = False
        row = {
            "case": label,
            "oracle_min_cost": oracle[0][0],
            "oracle_starts": oracle[0][1],
            "heuristics": {m: {"starts": s, "cost": cost(jobs, s, intensity) if s is not None else None}
                           for m, s in methods.items()},
            "feasible_schedule_count": len(oracle),
        }
        rows.append(row)
    impossible = (Job("x", 3, 0, 2, 1),)
    infeasible_rejected = enumerate_schedules(impossible, (1, 1, 1)) == []
    flat_equal = rows[1]["oracle_min_cost"] == sum(j.energy * j.duration * cases["flat"][0] for j in jobs)
    # Single-job discriminator confirms carbon-aware placement follows intensity.
    probe = (Job("p", 1, 0, 5, 1),)
    low_late = enumerate_schedules(probe, cases["declining"])[0][1] == (4,)
    low_early = enumerate_schedules(probe, cases["inverted"])[0][1] == (0,)
    result = {
        "scope": "finite deterministic model; not operational emissions evidence",
        "cases": rows,
        "controls": {"infeasible_rejected": infeasible_rejected, "flat_cost_computed": flat_equal,
                     "declining_prefers_late": low_late, "inverted_prefers_early": low_early},
        "heuristic_counterexamples": [
            {"case": r["case"], "method": m, "starts": v["starts"], "cost": v["cost"]}
            for r in rows for m, v in r["heuristics"].items()
            if v["starts"] is None or v["cost"] > r["oracle_min_cost"]
        ],
        "pass": all_ok and infeasible_rejected and flat_equal and low_late and low_early,
    }
    source = Path(__file__).read_bytes()
    result["source_sha256"] = hashlib.sha256(source).hexdigest()
    print(json.dumps(result, indent=2, sort_keys=True))
    if not result["pass"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
