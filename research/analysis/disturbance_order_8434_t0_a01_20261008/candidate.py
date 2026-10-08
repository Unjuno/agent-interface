#!/usr/bin/env python3
"""Generate the frozen finite schedule-order fixture and raw route outcomes."""

import hashlib
import json
import random
import sys
from pathlib import Path


def canonical_bytes(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def make_schedule(structure, seed, count_each=16):
    if structure == "iid":
        sequence = ["A"] * count_each + ["B"] * count_each
        random.Random(seed).shuffle(sequence)
        return sequence
    first, second = (("A", "B") if seed % 2 == 0 else ("B", "A"))
    if structure == "clustered":
        return [label for label in (first, second, first, second) for _ in range(count_each // 2)]
    if structure == "alternating":
        return [label for _ in range(count_each) for label in (first, second)]
    if structure == "heldout_block":
        return [first] * count_each + [second] * count_each
    raise ValueError(f"unknown schedule structure: {structure}")


def _runs(schedule):
    lengths = []
    for label in schedule:
        if not lengths or label != lengths[-1][0]:
            lengths.append([label, 1])
        else:
            lengths[-1][1] += 1
    return [{"label": label, "length": length} for label, length in lengths]


def evaluate_schedule(schedule):
    runs = _runs(schedule)
    counts = {"A": schedule.count("A"), "B": schedule.count("B")}
    transitions = sum(a != b for a, b in zip(schedule, schedule[1:]))
    lag1_product_sum = sum((1 if a == b else -1) for a, b in zip(schedule, schedule[1:]))
    events = []
    offset = 0
    for run in runs:
        for within_run in range(run["length"]):
            i = offset + within_run
            switch_ok = within_run > 0
            cache_ok = i != 0 and within_run < 2
            events.append({
                "index": i,
                "label": schedule[i],
                "intensity": 1,
                "duration": 1,
                "routes": {
                    "switch_reconfigure": switch_ok,
                    "two_step_cache": cache_ok,
                    "null_a": True,
                    "null_b": True,
                },
                "forbidden_effects": 0,
                "release_empty": True,
            })
        offset += run["length"]
    route_rows = {}
    for name in ("switch_reconfigure", "two_step_cache", "null_a", "null_b"):
        correct = sum(event["routes"][name] for event in events)
        route_rows[name] = {
            "safe_effects": correct,
            "missed_opportunities": len(events) - correct,
            "forbidden_effects": sum(event["forbidden_effects"] for event in events),
            "release_empty_failures": sum(not event["release_empty"] for event in events),
        }
    return {
        "opportunity_count": len(schedule),
        "label_counts": counts,
        "transitions": transitions,
        "runs": runs,
        "run_count": len(runs),
        "lag1_product_sum": lag1_product_sum,
        "routes": route_rows,
        "events": events,
    }


def build_raw(source, source_bytes):
    cases = []
    for split, seed_key in (("calibration", "calibration_seeds"), ("heldout", "heldout_seeds")):
        for structure in source["structures"]:
            for seed in source[seed_key]:
                schedule = make_schedule(structure, seed, source["count_per_label"])
                evaluated = evaluate_schedule(schedule)
                cases.append({
                    "case_id": f"{split}:{structure}:{seed}",
                    "split": split,
                    "structure": structure,
                    "seed": seed,
                    "schedule": schedule,
                    "schedule_sha256": hashlib.sha256(canonical_bytes(schedule)).hexdigest(),
                    **evaluated,
                })
    return {
        "format": "disturbance-order-8434-t0-a01-raw-v1",
        "source_sha256": hashlib.sha256(source_bytes).hexdigest(),
        "cases": cases,
    }


def main(argv):
    if len(argv) != 3:
        raise SystemExit("usage: candidate.py SOURCE.json RAW.json")
    source_path, raw_path = map(Path, argv[1:])
    source_bytes = source_path.read_bytes()
    source = json.loads(source_bytes)
    raw = build_raw(source, source_bytes)
    raw_path.parent.mkdir(parents=True, exist_ok=True)
    raw_path.write_bytes(json.dumps(raw, indent=2, sort_keys=True).encode() + b"\n")
    print(json.dumps({"status": "CANDIDATE_COMPLETE", "cases": len(raw["cases"]), "output": str(raw_path)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
