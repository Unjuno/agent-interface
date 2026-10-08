#!/usr/bin/env python3
"""Finite fixed-marginal inference/disturbance coupling candidate."""
from __future__ import annotations

import hashlib
import itertools
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
RESULTS = HERE / "results"


def canonical(obj: object) -> bytes:
    return (json.dumps(obj, sort_keys=True, separators=(",", ":")) + "\n").encode()


def trajectory(latencies: tuple[int, ...], disturbances: tuple[int, ...], gain: float, spec: dict) -> dict:
    state = 0.0
    trace = []
    events = []
    elapsed_inference = 0
    for index, (latency, severity) in enumerate(zip(latencies, disturbances)):
        before = state
        overlap = latency * severity
        delta = severity - spec["action_cap"] + gain * overlap
        without_action = max(0.0, before + severity + gain * overlap)
        state = max(0.0, state + delta)
        elapsed_inference += latency
        events.append({
            "event": index,
            "latency": latency,
            "severity": severity,
            "bounded_cover_action": spec["action_cap"],
            "state_before": round(before, 12),
            "state_delta": round(delta, 12),
            "state_after": round(state, 12),
            "fresh_action_available_at_tick": elapsed_inference,
            "fresh_action_useful_by_oracle": state < without_action,
            "useful_fresh_action_at_tick": elapsed_inference if state < without_action else None,
            "stale_cover_ticks": latency,
            "stale_severity_overlap": overlap,
        })
        trace.append(round(state, 12))
    return {
        "latencies": list(latencies),
        "disturbances": list(disturbances),
        "events": events,
        "state_trace": trace,
        "peak_state": round(max(trace, default=0.0), 12),
        "outside_envelope_event_ticks": sum(x > spec["envelope_max"] for x in trace),
        "stale_cover_occupancy_ticks": sum(latencies),
        "stale_severity_exposure": sum(e["stale_severity_overlap"] for e in events),
        "termination_release_tick": elapsed_inference,
    }


def run(spec: dict) -> dict:
    latencies = tuple(spec["latencies"])
    disturbances = tuple(spec["disturbances"])
    results = []
    for pairing in itertools.permutations(latencies):
        label = "rank_aligned" if pairing == latencies else "rank_reversed" if pairing == latencies[::-1] else "permutation"
        results.append({
            "pairing": label,
            "latency_assignment": list(pairing),
            "null": trajectory(pairing, disturbances, spec["null_gain"], spec),
            "interaction": trajectory(pairing, disturbances, spec["interaction_gain"], spec),
        })
    return {
        "schema": "inference-disturbance-coupling-candidate-v1",
        "spec": spec,
        "pairing_count": len(results),
        "trajectory_count": 2 * len(results),
        "pairings": results,
    }


def main() -> int:
    RESULTS.mkdir(parents=True, exist_ok=False)
    spec = json.loads((HERE / "spec.json").read_text())
    payload = run(spec)
    raw = canonical(payload)
    (RESULTS / "candidate.json").write_bytes(raw)
    print(f"CANDIDATE_COMPLETE pairings={payload['pairing_count']} trajectories={payload['trajectory_count']} sha256={hashlib.sha256(raw).hexdigest()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
