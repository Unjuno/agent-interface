#!/usr/bin/env python3
"""Frozen deterministic mode-flap simulator; emits raw events and metric rows."""
import hashlib, json, random, sys
from pathlib import Path

fixture_path, output_path = map(Path, sys.argv[1:3])
fx = json.loads(fixture_path.read_text(encoding="utf-8"))

def episode(family, seed, split):
    rng = random.Random(seed + 900_000 * fx["families"].index(family))
    q = 0
    mode = "A"
    switch_at = 10 + rng.randrange(3)
    next_flip = 3
    cusum = 0.0
    rows = []
    probe_start = None
    recoveries = []
    for t in range(fx["horizon_ticks"]):
        changed = False
        if family == "endogenous_flicker" and t == switch_at and t < fx["degraded_onset_tick"]:
            mode = "B" if mode == "A" else "A"
            changed = True
            # The explicit switch schedule accelerates before the fixed service boundary.
            switch_at = t + max(1, 8 - t // 8)
        elif family == "endogenous_flicker" and t == fx["degraded_onset_tick"]:
            mode, changed = "DEGRADED", mode != "DEGRADED"
        elif family == "policy_oscillation" and t == next_flip:
            mode = "B" if mode == "A" else "A"
            changed = True
            next_flip += 3

        demand = 3
        if family == "demand_drift":
            demand = 2 if t < 20 else (3 if t < 40 else 4)
        elif family == "single_mode_noise":
            demand = 3
        probe = int(t in fx["probe_ticks"])
        offered = demand + probe

        if family == "endogenous_flicker":
            service = 1 if mode == "DEGRADED" else (5 if mode == "A" else 2)
            if changed and mode != "DEGRADED":
                service = max(0, service - 1)  # one tick of transition overhead
        elif family == "demand_drift":
            service = 4
        elif family == "single_mode_noise":
            service = 4
            service_observation = rng.choice([2, 5])
            mode = "SINGLE"
            changed = False
        elif family == "policy_oscillation":
            service = 4  # labels oscillate, effective service does not
        elif family == "abrupt_failure":
            service = 0 if t >= fx["abrupt_onset_tick"] else 4
        else:
            service = 4
        if family != "single_mode_noise":
            service_observation = service

        before = q
        safety_service = 1
        safety_backlog = 0
        q = max(0, q + offered - service)
        cusum = max(0.0, cusum + (q - before) - fx["cusum_reference"])
        if probe:
            probe_start = {"tick": t, "baseline_queue": before}
        elif probe_start is not None and q <= probe_start["baseline_queue"]:
            recoveries.append(t - probe_start["tick"])
            probe_start = None
        rec_ratio = (recoveries[-1] / recoveries[0]) if len(recoveries) >= 2 and recoveries[0] else 0.0
        rows.append({"tick": t, "demand": demand, "probe": probe, "offered": offered,
                     "service": service, "service_observation": service_observation,
                     "service_mode": mode, "mode_transition": int(changed),
                     "queue_before": before, "queue": q, "safety_service": safety_service,
                     "safety_backlog": safety_backlog, "cusum_state": round(cusum, 6),
                     "recovery_durations": list(recoveries), "scores": {}})

    # Scores use only observable rows ending at the current tick.
    for i, row in enumerate(rows):
        w = rows[max(0, i - fx["rolling_window_ticks"] + 1):i + 1]
        deficits = [max(0, r["demand"] + r["probe"] - r["service_observation"]) for r in w]
        row["scores"] = {
            "rolling_mode_transition_count": sum(r["mode_transition"] for r in w),
            "rolling_mean_queue": sum(r["queue"] for r in w) / len(w),
            "rolling_maximum_service_margin_deficit": max(deficits),
            "recovery_duration_ratio": (row["recovery_durations"][-1] / row["recovery_durations"][0]
                                          if len(row["recovery_durations"]) >= 2 and row["recovery_durations"][0] else 0.0),
            "positive_queue_cusum": row["cusum_state"]
        }

    loss_tick = None
    k = fx["persistent_loss_ticks"]
    for i in range(len(rows) - k + 1):
        if all(r["queue"] >= fx["queue_loss_threshold"] for r in rows[i:i + k]):
            loss_tick = i
            break
    for i, row in enumerate(rows):
        row["warning_eligible"] = (i < fx["abrupt_onset_tick"] if family == "abrupt_failure"
                                    else loss_tick is None or i < loss_tick)
    return {"family": family, "seed": seed, "split": split, "loss_tick": loss_tick, "events": rows}

episodes = []
for family in fx["families"]:
    seeds = [("calibration", s) for s in fx["calibration_seeds"]] + [("heldout", s) for s in fx["heldout_seeds"]]
    episodes.extend(episode(family, seed, split) for split, seed in seeds)

metrics = fx["metrics"]
thresholds = {}
for metric in metrics:
    values = [r["scores"][metric] for e in episodes if e["split"] == "calibration" and e["family"] in fx["negative_calibration_families"] for r in e["events"] if r["warning_eligible"]]
    thresholds[metric] = max(values)
for e in episodes:
    for metric in metrics:
        e["alarms"] = {metric: next((r["tick"] for r in e["events"] if r["warning_eligible"] and r["scores"][metric] > thresholds[metric]), None)}

raw = {"schema": "mode-flap-raw-a01", "fixture_sha256": hashlib.sha256(fixture_path.read_bytes()).hexdigest(),
       "thresholds": thresholds, "episodes": episodes}
output_path.write_text(json.dumps(raw, sort_keys=True, separators=(",", ":")), encoding="utf-8")
print(json.dumps({"candidate": "RAW_WRITTEN", "episodes": len(episodes), "rows": sum(len(e["events"]) for e in episodes), "thresholds": thresholds}, sort_keys=True))
