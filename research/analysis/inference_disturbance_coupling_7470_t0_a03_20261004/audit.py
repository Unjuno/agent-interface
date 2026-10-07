#!/usr/bin/env python3
"""Independent reconstruction from saved raw candidate output."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
RAW = HERE / "results" / "candidate.json"


def reconstruct(spec):
    base, d = spec["latency_period"], spec["disturbance_period"]
    shifts = []
    for shift in range(len(base)):
        latencies = base[shift:] + base[:shift]
        arms = {}
        for name, gain in (("null", spec["null_gain"]), ("interaction", spec["interaction_gain"])):
            x, trace, rows = 0.0, [], []
            for i, (latency, severity) in enumerate(zip(latencies, d)):
                prior = x
                overlap = latency * severity
                change = severity - spec["action_cap"] + gain * overlap
                x = max(0.0, x + change)
                trace.append(round(x, 12))
                rows.append({"event": i, "latency": latency, "severity": severity,
                             "overlap": overlap, "state_before": round(prior, 12),
                             "state_delta": round(change, 12), "state_after": round(x, 12)})
            arms[name] = {"latencies": list(latencies), "disturbances": d, "events": rows,
                          "state_trace": trace, "peak_state": max(trace),
                          "outside_envelope_event_ticks": sum(v > spec["envelope_max"] for v in trace),
                          "stale_cover_occupancy_ticks": sum(latencies),
                          "stale_severity_exposure": sum(r["overlap"] for r in rows),
                          "termination_release_tick": sum(latencies)}
        shifts.append({"shift": shift, "latency_sequence": latencies, **arms})
    return {"schema": "inference-disturbance-coupling-circular-phase-v1", "spec": spec,
            "shift_count": len(shifts), "trajectory_count": 2 * len(shifts), "shifts": shifts}


def main():
    raw = json.loads(RAW.read_text())
    spec = json.loads((HERE / "spec.json").read_text())
    expected = reconstruct(spec)
    controls = json.loads(json.dumps(expected))
    controls["shifts"][0]["latency_sequence"][0] += 1
    missing = json.loads(json.dumps(expected)); missing["shifts"].pop()
    score = json.loads(json.dumps(expected)); score["shifts"][0]["interaction"]["peak_state"] += 1
    if raw != expected or controls == expected or missing == expected or score == expected:
        print("FAIL_METHOD reconstruction_or_mutation_gate")
        return 1
    null = {tuple(row["null"]["state_trace"]) for row in expected["shifts"]}
    peaks = [row["interaction"]["peak_state"] for row in expected["shifts"]]
    gate = (len(expected["shifts"]) == 4 and len(null) == 1
            and len(set(peaks)) > 1
            and all(sorted(row["latency_sequence"]) == sorted(spec["latency_period"]) for row in expected["shifts"])
            and all(row["interaction"]["disturbances"] == spec["disturbance_period"] for row in expected["shifts"]))
    if not gate:
        print("FAIL_METHOD preregistered_gate")
        return 1
    print(f"PASS_METHOD_SCOPED shifts=4 trajectories=8 null_states={len(null)} phase_peaks={peaks} mutations=3/3 sha256={hashlib.sha256(RAW.read_bytes()).hexdigest()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
