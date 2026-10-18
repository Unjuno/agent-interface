#!/usr/bin/env python3
"""Exhaustive finite circular-phase experiment for Issue #7470."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
RESULTS = HERE / "results"


def canonical(value):
    return (json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n").encode()


def trajectory(latencies, disturbances, gain, spec):
    state = 0.0
    trace = []
    rows = []
    for i, (latency, severity) in enumerate(zip(latencies, disturbances)):
        before = state
        overlap = latency * severity
        delta = severity - spec["action_cap"] + gain * overlap
        state = max(0.0, state + delta)
        trace.append(round(state, 12))
        rows.append({"event": i, "latency": latency, "severity": severity,
                     "overlap": overlap, "state_before": round(before, 12),
                     "state_delta": round(delta, 12), "state_after": round(state, 12)})
    return {"latencies": list(latencies), "disturbances": list(disturbances),
            "events": rows, "state_trace": trace,
            "peak_state": max(trace),
            "outside_envelope_event_ticks": sum(x > spec["envelope_max"] for x in trace),
            "stale_cover_occupancy_ticks": sum(latencies),
            "stale_severity_exposure": sum(r["overlap"] for r in rows),
            "termination_release_tick": sum(latencies)}


def run(spec):
    base = spec["latency_period"]
    d = spec["disturbance_period"]
    shifts = []
    for shift in range(len(base)):
        latencies = base[shift:] + base[:shift]
        shifts.append({"shift": shift, "latency_sequence": latencies,
                       "null": trajectory(latencies, d, spec["null_gain"], spec),
                       "interaction": trajectory(latencies, d, spec["interaction_gain"], spec)})
    return {"schema": "inference-disturbance-coupling-circular-phase-v1", "spec": spec,
            "shift_count": len(shifts), "trajectory_count": 2 * len(shifts), "shifts": shifts}


def main():
    RESULTS.mkdir(parents=True, exist_ok=False)
    spec = json.loads((HERE / "spec.json").read_text())
    raw = canonical(run(spec))
    (RESULTS / "candidate.json").write_bytes(raw)
    print(f"CANDIDATE_COMPLETE shifts=4 trajectories=8 sha256={hashlib.sha256(raw).hexdigest()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
