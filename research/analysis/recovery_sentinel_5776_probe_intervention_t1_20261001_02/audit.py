#!/usr/bin/env python3
"""Independent raw-only replay; intentionally does not import runner.py."""
import hashlib
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
FIXTURE = HERE / "fixture.json"


def expected_arm(fx, load_index, demand, mechanism, eid, is_probe):
    at = (eid * 11 + load_index * 3) % fx["horizon_ticks"]
    q, run, onset, rows, delivered = 0, 0, None, [], []
    for t in range(fx["horizon_ticks"]):
        if mechanism == "demand_drift_no_loss" and t >= fx["demand_drift_start_tick"]:
            d = demand + min(fx["demand_drift_max_extra"],
                             1 + (t - fx["demand_drift_start_tick"]) // fx["demand_drift_every_ticks"])
        else:
            d = demand
        cap = demand + fx["capacity_initial_slack"]
        if mechanism in ("gradual_capacity_loss", "gradual_capacity_no_loss"):
            cap -= max(0, t - fx["capacity_drift_start_tick"]) // fx["capacity_drop_every_ticks"]
            if mechanism == "gradual_capacity_no_loss":
                cap = max(demand + fx["no_loss_capacity_floor_slack"], cap)
        elif mechanism == "abrupt_capacity_loss" and t >= fx["abrupt_loss_tick"]:
            cap = demand - 2
        phase = fx["phase_arrival_units"] if t == at else 0
        shock = fx["probe_units"] if is_probe and onset is None and t in fx["probe_ticks"] else 0
        if shock:
            delivered.append(t)
        old = q
        incoming = d + phase + shock
        used = min(cap, old + incoming)
        q = old + incoming - used
        run = run + 1 if q > demand * fx["loss_backlog_multiplier"] else 0
        if onset is None and run >= fx["loss_consecutive_ticks"]:
            onset = t - fx["loss_consecutive_ticks"] + 1
        rows.append({"tick": t, "demand": d, "phase_arrival": phase,
                     "probe_arrival": shock, "capacity": cap, "backlog_before": old,
                     "served": used, "backlog": q, "over_limit_run": run,
                     "loss_tick_so_far": onset})
    return {"load": demand, "mechanism": mechanism, "episode_id": eid,
            "phase_tick": at, "condition": "probe" if is_probe else "no_probe",
            "loss_tick": onset, "backlog_area": sum(x["backlog"] for x in rows),
            "probe_ticks_delivered": delivered,
            "probe_units_total": sum(x["probe_arrival"] for x in rows), "events": rows}


def audit(doc, fx):
    errors = []
    if doc.get("schema") != "recovery-sentinel-probe-intervention-raw-v1":
        errors.append("schema")
    if doc.get("allocation") != fx["allocation"]:
        errors.append("allocation")
    if doc.get("fixture_sha256") != hashlib.sha256(FIXTURE.read_bytes()).hexdigest():
        errors.append("fixture_identity")
    want = [(li, name, d, m, e) for li, (name, d) in enumerate(fx["loads"].items())
            for m in fx["mechanisms"] for e in range(fx["episodes_per_cell"])]
    pairs = doc.get("pairs", [])
    expected_ids = [f"{name}:{m}:{e:02d}" for _, name, _, m, e in want]
    got_ids = [p.get("pair_id") for p in pairs]
    if got_ids != expected_ids:
        errors.append("pair_inventory_or_order")
    by_mechanism = {m: {"pairs": 0, "eligible_no_probe_losses": 0,
                        "eligible_probe_losses": 0, "probe_false_losses": 0,
                        "median_loss_advance_ticks": None, "median_backlog_area_delta": None}
                    for m in fx["mechanisms"]}
    by_cell = {f"{name}:{m}": {"pairs": 0, "no_probe_losses": 0,
                               "probe_losses": 0, "probe_false_losses": 0,
                               "loss_advances": [], "backlog_area_deltas": []}
               for name in fx["loads"] for m in fx["mechanisms"]}
    advances, areas = {m: [] for m in fx["mechanisms"]}, {m: [] for m in fx["mechanisms"]}
    for i, (li, name, demand, mech, eid) in enumerate(want):
        if i >= len(pairs):
            break
        p = pairs[i]
        for key, probe in (("probe", True), ("no_probe", False)):
            actual = p.get(key)
            expected = expected_arm(fx, li, demand, mech, eid, probe)
            if actual != expected:
                errors.append(f"replay:{i}:{key}")
        if p.get("pair_id") != expected_ids[i]:
            continue
        a = p.get("probe", {})
        b = p.get("no_probe", {})
        s = by_mechanism[mech]
        cell = by_cell[f"{name}:{mech}"]
        s["pairs"] += 1
        cell["pairs"] += 1
        if b.get("loss_tick") is not None:
            s["eligible_no_probe_losses"] += 1
            cell["no_probe_losses"] += 1
        if a.get("loss_tick") is not None:
            s["eligible_probe_losses"] += 1
            cell["probe_losses"] += 1
        if a.get("loss_tick") is not None and b.get("loss_tick") is None:
            s["probe_false_losses"] += 1
            cell["probe_false_losses"] += 1
        if a.get("loss_tick") is not None and b.get("loss_tick") is not None:
            advances[mech].append(b["loss_tick"] - a["loss_tick"])
            cell["loss_advances"].append(b["loss_tick"] - a["loss_tick"])
        areas[mech].append(a.get("backlog_area", 0) - b.get("backlog_area", 0))
        cell["backlog_area_deltas"].append(a.get("backlog_area", 0) - b.get("backlog_area", 0))
    for m in fx["mechanisms"]:
        s = by_mechanism[m]
        if advances[m]:
            v = sorted(advances[m]); n = len(v)
            s["median_loss_advance_ticks"] = (v[(n - 1) // 2] + v[n // 2]) / 2
        if areas[m]:
            v = sorted(areas[m]); n = len(v)
            s["median_backlog_area_delta"] = (v[(n - 1) // 2] + v[n // 2]) / 2
    for cell in by_cell.values():
        for source, target_key in (("loss_advances", "median_loss_advance_ticks"),
                                   ("backlog_area_deltas", "median_backlog_area_delta")):
            values = sorted(cell.pop(source))
            if values:
                n = len(values)
                cell[target_key] = (values[(n - 1) // 2] + values[n // 2]) / 2
            else:
                cell[target_key] = None
    target = by_mechanism["gradual_capacity_loss"]
    eligible = (target["pairs"] == fx["episodes_per_cell"] * len(fx["loads"])
                and target["eligible_no_probe_losses"] == target["pairs"]
                and target["eligible_probe_losses"] == target["pairs"]
                and all(p["no_probe"]["loss_tick"] > max(fx["probe_ticks"])
                        for p in pairs if p["probe"]["mechanism"] == "gradual_capacity_loss"))
    effect = target["median_loss_advance_ticks"]
    disposition = "FAIL_INTEGRITY" if errors else (
        "HOLD_NO_ELIGIBLE_OUTCOME" if not eligible else
        "PASS_PROBE_ADVANCES_ENDPOINT_IN_FIXTURE" if effect is not None and effect >= 4 else
        "NO_MATERIAL_PROBE_ADVANCE_IN_FIXTURE")
    return {"disposition": disposition, "audit": "PASS_LEDGER_SCOPED" if not errors else "FAIL_AUDIT",
            "errors": sorted(set(errors)), "event_rows_reconstructed": sum(
                len(p.get("probe", {}).get("events", [])) + len(p.get("no_probe", {}).get("events", [])) for p in pairs),
            "eligible_target": eligible, "metrics_by_mechanism": by_mechanism,
            "metrics_by_load_and_mechanism": by_cell}


def main():
    if len(sys.argv) != 2:
        raise SystemExit("usage: audit.py RAW.json")
    raw = Path(sys.argv[1]).read_bytes()
    result = audit(json.loads(raw), json.loads(FIXTURE.read_text()))
    result["raw_sha256"] = hashlib.sha256(raw).hexdigest()
    print(json.dumps(result, sort_keys=True, separators=(",", ":")))
    raise SystemExit(0 if result["audit"] == "PASS_LEDGER_SCOPED" else 1)


if __name__ == "__main__":
    main()
