#!/usr/bin/env python3
"""Candidate for the frozen matched probe/no-probe intervention experiment."""
import hashlib
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
FIXTURE = HERE / "fixture.json"


def capacity_at(fx, demand, mechanism, tick):
    initial = demand + fx["capacity_initial_slack"]
    drops = max(0, tick - fx["capacity_drift_start_tick"]) // fx["capacity_drop_every_ticks"]
    if mechanism in ("gradual_capacity_loss", "gradual_capacity_no_loss"):
        cap = initial - drops
        if mechanism == "gradual_capacity_no_loss":
            cap = max(demand + fx["no_loss_capacity_floor_slack"], cap)
        return cap
    if mechanism == "abrupt_capacity_loss" and tick >= fx["abrupt_loss_tick"]:
        return demand - 2
    return initial


def demand_at(fx, demand, mechanism, tick):
    if mechanism != "demand_drift_no_loss" or tick < fx["demand_drift_start_tick"]:
        return demand
    extra = 1 + (tick - fx["demand_drift_start_tick"]) // fx["demand_drift_every_ticks"]
    return demand + min(fx["demand_drift_max_extra"], extra)


def simulate_arm(fx, load_index, load, mechanism, eid, probed):
    phase_tick = (eid * 11 + load_index * 3) % fx["horizon_ticks"]
    backlog = 0
    over_limit_run = 0
    loss_tick = None
    delivered_probe_ticks = []
    rows = []
    for tick in range(fx["horizon_ticks"]):
        demand = demand_at(fx, load, mechanism, tick)
        phase = fx["phase_arrival_units"] if tick == phase_tick else 0
        probe = fx["probe_units"] if probed and loss_tick is None and tick in fx["probe_ticks"] else 0
        if probe:
            delivered_probe_ticks.append(tick)
        cap = capacity_at(fx, load, mechanism, tick)
        before = backlog
        offered = demand + phase + probe
        served = min(cap, before + offered)
        backlog = before + offered - served
        over_limit_run = over_limit_run + 1 if backlog > load * fx["loss_backlog_multiplier"] else 0
        if loss_tick is None and over_limit_run >= fx["loss_consecutive_ticks"]:
            loss_tick = tick - fx["loss_consecutive_ticks"] + 1
        rows.append({"tick": tick, "demand": demand, "phase_arrival": phase,
                     "probe_arrival": probe, "capacity": cap, "backlog_before": before,
                     "served": served, "backlog": backlog, "over_limit_run": over_limit_run,
                     "loss_tick_so_far": loss_tick})
    return {"load": load, "mechanism": mechanism, "episode_id": eid,
            "phase_tick": phase_tick, "condition": "probe" if probed else "no_probe",
            "loss_tick": loss_tick, "backlog_area": sum(r["backlog"] for r in rows),
            "probe_ticks_delivered": delivered_probe_ticks,
            "probe_units_total": sum(r["probe_arrival"] for r in rows), "events": rows}


def build(fx):
    pairs = []
    for load_index, (load_name, demand) in enumerate(fx["loads"].items()):
        for mechanism in fx["mechanisms"]:
            for eid in range(fx["episodes_per_cell"]):
                key = f"{load_name}:{mechanism}:{eid:02d}"
                pairs.append({"pair_id": key,
                              "probe": simulate_arm(fx, load_index, demand, mechanism, eid, True),
                              "no_probe": simulate_arm(fx, load_index, demand, mechanism, eid, False)})
    return {"schema": "recovery-sentinel-probe-intervention-raw-v1",
            "allocation": fx["allocation"],
            "fixture_sha256": hashlib.sha256(FIXTURE.read_bytes()).hexdigest(),
            "pairs": pairs}


def main():
    if len(sys.argv) != 2:
        raise SystemExit("usage: runner.py OUTPUT.json")
    out = Path(sys.argv[1])
    if out.exists():
        raise SystemExit("STOP_OUTPUT_EXISTS")
    fx = json.loads(FIXTURE.read_text())
    raw = (json.dumps(build(fx), sort_keys=True, separators=(",", ":")) + "\n").encode()
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(raw)
    print(json.dumps({"candidate": "EXIT_0", "pairs": 90, "arms": 180,
                      "event_rows": 180 * fx["horizon_ticks"],
                      "raw_sha256": hashlib.sha256(raw).hexdigest()}, sort_keys=True))


if __name__ == "__main__":
    main()
