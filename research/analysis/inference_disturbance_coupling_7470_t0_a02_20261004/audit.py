#!/usr/bin/env python3
"""Independent raw-only audit of fixed-marginal pairing trajectories."""
from __future__ import annotations

import hashlib
import itertools
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
RAW = HERE / "results" / "candidate.json"


def reconstruct(spec: dict) -> dict:
    assignments = []
    for latencies in itertools.permutations(spec["latencies"]):
        label = "rank_aligned" if list(latencies) == spec["latencies"] else "rank_reversed" if list(latencies) == spec["latencies"][::-1] else "permutation"
        arms = {}
        for name, gain in (("null", spec["null_gain"]), ("interaction", spec["interaction_gain"])):
            x = 0.0
            cumulative = 0
            states, event_rows = [], []
            for index in range(len(spec["disturbances"])):
                d, s = latencies[index], spec["disturbances"][index]
                prior = x
                overlap = d * s
                dx = s - spec["action_cap"] + gain * overlap
                without_action = max(0.0, prior + s + gain * overlap)
                x = max(0.0, x + dx)
                cumulative += d
                event_rows.append({
                    "event": index,
                    "latency": d,
                    "severity": s,
                    "bounded_cover_action": spec["action_cap"],
                    "state_before": round(prior, 12),
                    "state_delta": round(dx, 12),
                    "state_after": round(x, 12),
                    "fresh_action_available_at_tick": cumulative,
                    "fresh_action_useful_by_oracle": x < without_action,
                    "useful_fresh_action_at_tick": cumulative if x < without_action else None,
                    "stale_cover_ticks": d,
                    "stale_severity_overlap": overlap,
                })
                states.append(round(x, 12))
            arms[name] = {
                "latencies": list(latencies),
                "disturbances": spec["disturbances"],
                "events": event_rows,
                "state_trace": states,
                "peak_state": round(max(states, default=0.0), 12),
                "outside_envelope_event_ticks": sum(value > spec["envelope_max"] for value in states),
                "stale_cover_occupancy_ticks": sum(latencies),
                "stale_severity_exposure": sum(row["stale_severity_overlap"] for row in event_rows),
                "termination_release_tick": cumulative,
            }
        assignments.append({"pairing": label, "latency_assignment": list(latencies), **arms})
    return {
        "schema": "inference-disturbance-coupling-candidate-v1",
        "spec": spec,
        "pairing_count": len(assignments),
        "trajectory_count": 2 * len(assignments),
        "pairings": assignments,
    }


def mutations_rejected(raw: dict, expected: dict) -> bool:
    changed_marginal = json.loads(json.dumps(raw))
    changed_marginal["pairings"][0]["latency_assignment"][0] += 1
    missing_event = json.loads(json.dumps(raw))
    missing_event["pairings"].pop()
    wrong_score = json.loads(json.dumps(raw))
    wrong_score["pairings"][0]["interaction"]["peak_state"] += 1
    return all(mutant != expected for mutant in (changed_marginal, missing_event, wrong_score))


def main() -> int:
    raw = json.loads(RAW.read_text())
    spec = json.loads((HERE / "spec.json").read_text())
    expected = reconstruct(spec)
    if raw != expected:
        print("FAIL_METHOD exact_trajectory_reconstruction=no")
        return 1
    aligned = next(x for x in expected["pairings"] if x["pairing"] == "rank_aligned")
    reversed_pair = next(x for x in expected["pairings"] if x["pairing"] == "rank_reversed")
    null_traces = {tuple(x["null"]["state_trace"]) for x in expected["pairings"]}
    null_outcomes = {(x["null"]["peak_state"], x["null"]["outside_envelope_event_ticks"]) for x in expected["pairings"]}
    gate = (
        len(null_traces) == 1
        and len(null_outcomes) == 1
        and aligned["interaction"]["peak_state"] > reversed_pair["interaction"]["peak_state"]
        and aligned["interaction"]["stale_severity_exposure"] > reversed_pair["interaction"]["stale_severity_exposure"]
        and len(expected["pairings"]) == 24
        and all(sorted(x["latency_assignment"]) == sorted(spec["latencies"]) for x in expected["pairings"])
        and all(x["null"]["disturbances"] == spec["disturbances"] and x["interaction"]["disturbances"] == spec["disturbances"] for x in expected["pairings"])
        and mutations_rejected(raw, expected)
    )
    if not gate:
        print("FAIL_METHOD gates=not_satisfied")
        return 1
    digest = hashlib.sha256(RAW.read_bytes()).hexdigest()
    print(f"PASS_METHOD_SCOPED pairings=24 trajectories=48 null_states={len(null_traces)} aligned_peak={aligned['interaction']['peak_state']} reversed_peak={reversed_pair['interaction']['peak_state']} mutations=3/3 sha256={digest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
