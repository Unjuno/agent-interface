#!/usr/bin/env python3
"""Frozen finite input/output conformance matrix for Issue #5518 T7."""
import argparse
import json
from pathlib import Path

DEADLINE_TICK = 2
CASES = (
    ("receipt_before_deadline", [
        {"direction": "input", "label": "OBSERVE", "tick": 0},
        {"direction": "internal", "label": "TAU_RETRY", "tick": 0},
        {"direction": "output", "label": "RECEIPT", "tick": 1},
    ], True, None),
    ("quiescent_at_deadline", [
        {"direction": "input", "label": "OBSERVE", "tick": 0},
        {"direction": "output", "label": "QUIESCENT", "tick": 2},
    ], True, None),
    ("quiescent_after_deadline", [
        {"direction": "input", "label": "OBSERVE", "tick": 0},
        {"direction": "output", "label": "QUIESCENT", "tick": 3},
    ], False, 1),
    ("explicit_unknown_after_deadline", [
        {"direction": "input", "label": "OBSERVE", "tick": 0},
        {"direction": "output", "label": "UNKNOWN", "tick": 3},
    ], True, None),
    ("late_receipt", [
        {"direction": "input", "label": "OBSERVE", "tick": 0},
        {"direction": "output", "label": "RECEIPT", "tick": 3},
    ], False, 1),
    ("cancel_then_quiescent", [
        {"direction": "input", "label": "CANCEL", "tick": 0},
        {"direction": "output", "label": "CANCELLED", "tick": 0},
        {"direction": "output", "label": "QUIESCENT", "tick": 1},
    ], False, 2),
)


def check_trace(events):
    state, deadline, previous_tick = "start", None, -1
    for index, event in enumerate(events):
        tick = event["tick"]
        if not isinstance(tick, int) or tick < previous_tick:
            return False, index
        previous_tick = tick
        direction, label = event["direction"], event["label"]
        if direction == "internal":
            if label != "TAU_RETRY":
                return False, index
            continue
        if state == "start":
            if direction == "input" and label == "OBSERVE":
                state, deadline = "pending", tick + DEADLINE_TICK
                continue
            if direction == "input" and label == "CANCEL":
                state = "cancel_wait"
                continue
            return False, index
        if state == "pending":
            if direction != "output":
                return False, index
            if label == "UNKNOWN":
                state = "done"
                continue
            if label == "RECEIPT" and tick <= deadline:
                state = "done"
                continue
            if label == "QUIESCENT" and tick <= deadline:
                continue
            return False, index
        if state == "cancel_wait":
            if direction == "output" and label == "CANCELLED" and tick == 0:
                state = "cancelled"
                continue
            return False, index
        return False, index
    return True, None


def run_case(case_id, events, expected, expected_cex):
    conformant, cex = check_trace(events)
    return {"case_id": case_id, "events": events, "expected_conformant": expected,
            "expected_counterexample_index": expected_cex,
            "conformant": conformant, "counterexample_index": cex}


def main(outdir):
    root = Path(outdir)
    root.mkdir(parents=True, exist_ok=True)
    traces = [run_case(*case) for case in CASES]
    passed = all(row["conformant"] == row["expected_conformant"]
                 and row["counterexample_index"] == row["expected_counterexample_index"]
                 for row in traces)
    print(json.dumps({"kind": "manifest", "schema": "issue-5518-ioco-t7-v1",
                      "deadline_tick": DEADLINE_TICK, "scenario_count": len(traces),
                      "decision": "PASS" if passed else "FAIL"}, sort_keys=True, separators=(",", ":")))
    for trace in traces:
        print(json.dumps({"kind": "trace", **trace}, sort_keys=True, separators=(",", ":")))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--outdir", required=True)
    main(parser.parse_args().outdir)
