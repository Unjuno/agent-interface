#!/usr/bin/env python3
"""Independent host-only replay; no candidate or prior runner/auditor imports."""
import hashlib
import json
import statistics
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SOURCE = HERE.parent / "recovery_sentinel_5776_probe_intervention_t1_20261001_02"
FIXTURE = json.loads((SOURCE / "fixture.json").read_text())
FIXTURE_BYTES = (SOURCE / "fixture.json").read_bytes()
AMPLITUDES = (1, 2, 3, 4, 6, 8, 12, 16, 20, 24, 28, 32, 36, 40)
SCHEDULES = ((16,), (32,), (48,), (16, 32), (16, 48), (32, 48), (16, 32, 48))
NO_LOSS = {"gradual_capacity_no_loss", "demand_drift_no_loss", "stable_no_loss"}


def expected(fx, li, demand, mechanism, eid, probed):
    phase_tick = (eid * 11 + li * 3) % fx["horizon_ticks"]
    backlog = 0
    over = 0
    loss = None
    rows = []
    delivered = []
    for tick in range(fx["horizon_ticks"]):
        if mechanism == "demand_drift_no_loss" and tick >= fx["demand_drift_start_tick"]:
            extra = 1 + (tick - fx["demand_drift_start_tick"]) // fx["demand_drift_every_ticks"]
            demand_now = demand + min(fx["demand_drift_max_extra"], extra)
        else:
            demand_now = demand
        cap = demand + fx["capacity_initial_slack"]
        if mechanism in ("gradual_capacity_loss", "gradual_capacity_no_loss"):
            cap -= max(0, tick - fx["capacity_drift_start_tick"]) // fx["capacity_drop_every_ticks"]
            if mechanism == "gradual_capacity_no_loss":
                cap = max(demand + fx["no_loss_capacity_floor_slack"], cap)
        elif mechanism == "abrupt_capacity_loss" and tick >= fx["abrupt_loss_tick"]:
            cap = demand - 2
        phase = fx["phase_arrival_units"] if tick == phase_tick else 0
        probe = fx["probe_units"] if probed and loss is None and tick in fx["probe_ticks"] else 0
        if probe:
            delivered.append(tick)
        before = backlog
        served = min(cap, before + demand_now + phase + probe)
        backlog = before + demand_now + phase + probe - served
        over = over + 1 if backlog > demand * fx["loss_backlog_multiplier"] else 0
        if loss is None and over >= fx["loss_consecutive_ticks"]:
            loss = tick - fx["loss_consecutive_ticks"] + 1
        rows.append({"tick": tick, "demand": demand_now, "phase_arrival": phase,
                     "probe_arrival": probe, "capacity": cap, "backlog_before": before,
                     "served": served, "backlog": backlog, "over_limit_run": over,
                     "loss_tick_so_far": loss})
    return {"loss_tick": loss, "backlog_area": sum(r["backlog"] for r in rows),
            "probe_ticks_delivered": delivered,
            "probe_units_total": sum(r["probe_arrival"] for r in rows), "events": rows}


def digest(events):
    return hashlib.sha256(json.dumps(events, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def audit(doc):
    errors = []
    if doc.get("schema") != "recovery-sentinel-probe-schedule-construction-raw-v1":
        errors.append("schema")
    if doc.get("allocation") != "construction-only-5776-schedule-amplitude-grid-20261001-01":
        errors.append("allocation")
    fixture_hash = hashlib.sha256(FIXTURE_BYTES).hexdigest()
    if doc.get("source_fixture_sha256") != fixture_hash:
        errors.append("fixture_identity")
    if doc.get("grid") != {"amplitudes": list(AMPLITUDES), "schedules": [list(x) for x in SCHEDULES]}:
        errors.append("grid")
    cells = doc.get("cells", [])
    expected_cells = [(s, a) for s in SCHEDULES for a in AMPLITUDES]
    if [(tuple(c.get("probe_ticks", [])), c.get("probe_units")) for c in cells] != expected_cells:
        errors.append("cell_inventory_order")
    result_rows = []
    for ci, ((ticks, units), cell) in enumerate(zip(expected_cells, cells)):
        fx = dict(FIXTURE, probe_ticks=list(ticks), probe_units=units)
        pairs = cell.get("pairs", [])
        wanted = [(li, name, demand, mech, eid)
                  for li, (name, demand) in enumerate(fx["loads"].items())
                  for mech in fx["mechanisms"]
                  for eid in range(fx["episodes_per_cell"])]
        pair_ids = [f"{name}:{mech}:{eid:02d}" for _, name, _, mech, eid in wanted]
        if [p.get("pair_id") for p in pairs] != pair_ids:
            errors.append(f"pair_inventory:{ci}")
        advances = []
        target_probe_losses = target_no_probe_losses = 0
        control_created = control_probe_losses = control_no_probe_losses = 0
        for pi, (li, name, demand, mech, eid) in enumerate(wanted):
            if pi >= len(pairs):
                break
            pair = pairs[pi]
            for key, probed in (("probe", True), ("no_probe", False)):
                arm = expected(fx, li, demand, mech, eid, probed)
                actual = pair.get(key, {})
                if pair.get("phase_tick") != (eid * 11 + li * 3) % fx["horizon_ticks"]:
                    errors.append(f"phase:{ci}:{pi}")
                if actual.get("event_sha256") != digest(arm["events"]):
                    errors.append(f"event_digest:{ci}:{pi}:{key}")
                for field in ("loss_tick", "backlog_area", "probe_ticks_delivered", "probe_units_total"):
                    if actual.get(field) != arm[field]:
                        errors.append(f"endpoint:{ci}:{pi}:{key}:{field}")
            if mech == "gradual_capacity_loss":
                p = pair["probe"]["loss_tick"]
                n = pair["no_probe"]["loss_tick"]
                target_probe_losses += p is not None
                target_no_probe_losses += n is not None
                if p is not None and n is not None:
                    advances.append(n - p)
            if mech in NO_LOSS:
                p = pair["probe"]["loss_tick"]
                n = pair["no_probe"]["loss_tick"]
                control_probe_losses += p is not None
                control_no_probe_losses += n is not None
                control_created += p is not None and n is None
        result_rows.append({
            "probe_ticks": list(ticks), "probe_units": units,
            "pulse_count": len(ticks),
            "target_pairs": len(advances),
            "target_probe_losses": target_probe_losses,
            "target_no_probe_losses": target_no_probe_losses,
            "median_target_advance_ticks": statistics.median(advances) if advances else None,
            "control_pairs": 54,
            "control_probe_losses": control_probe_losses,
            "control_no_probe_losses": control_no_probe_losses,
            "control_created_losses": control_created,
        })
    # Pareto minimize control-created losses and pulse count; maximize median advance.
    frontier = []
    for row in result_rows:
        advance = row["median_target_advance_ticks"]
        harm = row["control_created_losses"]
        pulses = row["pulse_count"]
        dominated = any(
            other is not row
            and other["median_target_advance_ticks"] is not None
            and advance is not None
            and other["median_target_advance_ticks"] >= advance
            and other["control_created_losses"] <= harm
            and other["pulse_count"] <= pulses
            and (other["median_target_advance_ticks"] > advance
                 or other["control_created_losses"] < harm
                 or other["pulse_count"] < pulses)
            for other in result_rows
        )
        if not dominated:
            frontier.append(row)
    return {"audit": "PASS_EVENT_COMMITMENT_REPLAY" if not errors else "FAIL_AUDIT",
            "errors": sorted(set(errors)), "cells_reconstructed": len(result_rows),
            "pairs_reconstructed": sum(len(c.get("pairs", [])) for c in cells),
            "arms_reconstructed": 2 * sum(len(c.get("pairs", [])) for c in cells),
            "metrics": result_rows, "pareto_frontier": frontier,
            "scope": "deterministic synthetic host-only construction; compact event hashes, not lossless event archive"}


def main():
    if len(sys.argv) != 3:
        raise SystemExit("usage: audit.py RAW.json AUDIT.json")
    raw_path, audit_path = map(Path, sys.argv[1:])
    if audit_path.exists():
        raise SystemExit("STOP_AUDIT_OUTPUT_EXISTS")
    raw = raw_path.read_bytes()
    result = audit(json.loads(raw))
    result["raw_sha256"] = hashlib.sha256(raw).hexdigest()
    encoded = (json.dumps(result, sort_keys=True, indent=2) + "\n").encode()
    audit_path.write_bytes(encoded)
    print(json.dumps({"audit": result["audit"], "errors": len(result["errors"]),
                      "cells": result["cells_reconstructed"],
                      "raw_sha256": result["raw_sha256"],
                      "audit_sha256": hashlib.sha256(encoded).hexdigest()}, sort_keys=True))
    raise SystemExit(0 if result["audit"] == "PASS_EVENT_COMMITMENT_REPLAY" else 1)


if __name__ == "__main__":
    main()
