#!/usr/bin/env python3
"""Frozen method fixture generator; does not model human responses."""
import argparse
import hashlib
import json
import random
from pathlib import Path


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def run(protocol, fixture):
    rng = random.Random(fixture["random_seed"])
    events = {item["event_id"]: item for item in fixture["truth"]}
    trials = []
    for block in range(protocol["primary_factorial"]["matched_blocks"]):
        cells = [(demand, gap) for demand in protocol["primary_factorial"]["first_event_demand"]
                 for gap in protocol["primary_factorial"]["gap_ms"]]
        rng.shuffle(cells)
        for position, (demand, gap) in enumerate(cells):
            cell_index = (protocol["primary_factorial"]["first_event_demand"].index(demand)
                          * len(protocol["primary_factorial"]["gap_ms"])
                          + protocol["primary_factorial"]["gap_ms"].index(gap))
            order = ["E1", "E2"] if block % 2 == 0 else ["E2", "E1"]
            first_id, second_id = order
            first_position = "upper" if (block + cell_index) % 2 == 0 else "lower"
            positions = [first_position, "lower" if first_position == "upper" else "upper"]
            trial_id = f"B{block + 1:02d}-D{demand}-G{gap:04d}"
            demand_instruction = ("identify_and_reconcile_first" if demand == "process"
                                  else "observe_first_but_do_not_reconcile")
            trials.append({
                "trial_id": trial_id,
                "block": block + 1,
                "position": position + 1,
                "demand": demand,
                "demand_instruction": demand_instruction,
                "gap_ms": gap,
                "event_onset_ms": [0, gap],
                "event_count": 2,
                "first_event_id": first_id,
                "second_event_id": second_id,
                "source_ids": [fixture["source_id"], fixture["source_id"]],
                "fact_ids": [events[first_id]["fact_id"], events[second_id]["fact_id"]],
                "messages": [events[first_id]["message"], events[second_id]["message"]],
                "salience": [protocol["primary_factorial"]["salience"]] * 2,
                "visual_duration_ms": [protocol["primary_factorial"]["visual_duration_ms"]] * 2,
                "t2_deadline_ms": protocol["primary_factorial"]["t2_deadline_after_arrival_ms"],
                "event_positions": positions,
                "schedule_sha256": digest([trial_id, first_id, second_id, gap, demand]),
            })
    scored = []
    trial_by_id = {row["trial_id"]: row for row in trials}
    for case in fixture["response_cases"]:
        latency = case["latency_after_t2_ms"]
        target = trial_by_id[case["trial_id"]]
        correct = (case["event_id"] == target["second_event_id"] and case["source_id"] == fixture["source_id"]
                   and case["fact_id"] == target["fact_ids"][1] and isinstance(latency, int)
                   and 0 <= latency <= protocol["primary_factorial"]["t2_deadline_after_arrival_ms"])
        reason = "correct" if correct else case["class"]
        scored.append({"case_id": case["case_id"], "target_trial_id": case["trial_id"],
                       "correct_t2": correct, "reason": reason})
    controls = [{"control": name, **protocol["control_definitions"][name],
                 "purpose": "detectability_or_review_control", "not_in_factorial": True}
                for name in protocol["controls"]]
    return {"fixture_id": fixture["fixture_id"], "scope": protocol["scope"],
            "factorial_trials": trials, "control_labels": controls, "response_scores": scored}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--protocol", type=Path, required=True)
    parser.add_argument("--fixture", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = run(json.loads(args.protocol.read_text()), json.loads(args.fixture.read_text()))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    encoded = json.dumps(result, sort_keys=True, indent=2) + "\n"
    args.output.write_text(encoded)
    print(json.dumps({"status": "CANDIDATE_COMPLETE", "factorial_trials": len(result["factorial_trials"]),
                      "response_cases": len(result["response_scores"]),
                      "sha256": hashlib.sha256(encoded.encode()).hexdigest()}, sort_keys=True))


if __name__ == "__main__":
    main()
