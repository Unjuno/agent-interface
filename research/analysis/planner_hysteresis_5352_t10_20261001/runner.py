"""T10: fail closed after an observed disturbance-bound breach.

This is a deterministic, synthetic gate study. It has no runtime or model calls.
"""
from __future__ import annotations

import itertools
import json
import sys

BOUND = 3
MAX_LENGTH = 4
DOMAIN = range(5)
DECLARED_GENERATION = 1


def _gate(observation: dict, expected_sequence: int) -> str | None:
    if observation["generation"] != DECLARED_GENERATION:
        return "generation_mismatch"
    if observation["sequence"] != expected_sequence:
        return "sequence_gap"
    if observation["critical"]:
        return "critical_override"
    if observation["magnitude"] > BOUND:
        return "out_of_bound"
    return None


def evaluate_observations(observations: list[dict], *, trace_id: str) -> dict:
    candidate_permits = 0
    stopped = False
    stop_index = None
    stop_reason = None
    expected_sequence = 0
    for index, observation in enumerate(observations):
        if stopped:
            continue
        reason = _gate(observation, expected_sequence)
        if reason is not None:
            stopped = True
            stop_index = index
            stop_reason = reason
            continue
        candidate_permits += 1
        expected_sequence += 1
    return {
        "kind": "control",
        "case": trace_id,
        "observations": observations,
        "static_permits": len(observations),
        "candidate_permits": candidate_permits,
        "yield_index": stop_index,
        "yield_reason": stop_reason,
    }


def build_records() -> list[dict]:
    records: list[dict] = []
    for length in range(1, MAX_LENGTH + 1):
        for ordinal, sequence in enumerate(itertools.product(DOMAIN, repeat=length)):
            first_breach = next((i for i, value in enumerate(sequence) if value > BOUND), None)
            candidate_permits = length if first_breach is None else first_breach
            observations = [
                {"generation": DECLARED_GENERATION, "sequence": i,
                 "magnitude": value, "critical": False}
                for i, value in enumerate(sequence)
            ]
            records.append({
                "kind": "trace",
                "trace_id": f"n{length}-{ordinal:04d}",
                "sequence": list(sequence),
                "static_permits": length,
                "candidate_permits": candidate_permits,
                "first_breach_index": first_breach,
                "static_post_breach_permits": 0 if first_breach is None else length - first_breach - 1,
                "candidate_post_breach_permits": 0,
                "disposition": "CONTINUE" if first_breach is None else "YIELD_REQUIRED",
            })

    controls = [
        ("critical-first", [{"generation": 1, "sequence": 0, "magnitude": 0, "critical": True}]),
        ("critical-after-safe", [
            {"generation": 1, "sequence": 0, "magnitude": 1, "critical": False},
            {"generation": 1, "sequence": 1, "magnitude": 0, "critical": True},
        ]),
        ("generation-change", [
            {"generation": 1, "sequence": 0, "magnitude": 1, "critical": False},
            {"generation": 2, "sequence": 1, "magnitude": 1, "critical": False},
        ]),
        ("sequence-gap", [
            {"generation": 1, "sequence": 0, "magnitude": 1, "critical": False},
            {"generation": 1, "sequence": 2, "magnitude": 1, "critical": False},
        ]),
        ("duplicate-sequence", [
            {"generation": 1, "sequence": 0, "magnitude": 1, "critical": False},
            {"generation": 1, "sequence": 0, "magnitude": 1, "critical": False},
        ]),
        ("bound-edge-3", [{"generation": 1, "sequence": 0, "magnitude": 3, "critical": False}]),
        ("breach-edge-4", [{"generation": 1, "sequence": 0, "magnitude": 4, "critical": False}]),
        ("no-silent-rearm", [
            {"generation": 1, "sequence": 0, "magnitude": 4, "critical": False},
            {"generation": 1, "sequence": 1, "magnitude": 0, "critical": False},
        ]),
    ]
    records.extend(evaluate_observations(observations, trace_id=name) for name, observations in controls)
    return records


def main() -> int:
    for row in build_records():
        sys.stdout.write(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

