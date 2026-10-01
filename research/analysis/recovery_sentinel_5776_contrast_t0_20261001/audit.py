#!/usr/bin/env python3
"""Independent raw-ledger replay for the #5776 contrast fixture; no runner import."""
import hashlib
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
FIXTURE = HERE / "fixture.json"


def expected_wait(mechanism, probe_index, fx):
    if mechanism in ("gradual_recovery_loss", "demand_drift_no_loss"):
        return fx["fixed_recovery_wait_ticks"][probe_index]
    return fx["fixed_recovery_wait_ticks"][0]


def audit(doc, fx):
    errors = []
    if doc.get("schema") != "recovery-sentinel-contrast-raw-v1":
        errors.append("schema")
    if doc.get("allocation") != fx["allocation"]:
        errors.append("allocation")
    if doc.get("fixture_sha256") != hashlib.sha256(FIXTURE.read_bytes()).hexdigest():
        errors.append("fixture_identity")

    expected_total = len(fx["loads"]) * len(fx["mechanisms"]) * fx["episodes_per_mechanism"]
    episodes = doc.get("episodes")
    if not isinstance(episodes, list) or len(episodes) != expected_total:
        return {"disposition": "FAIL_INTEGRITY", "errors": sorted(set(errors + ["episode_inventory"])),
                "event_rows": 0, "metrics": {}}
    keys = [(e.get("mechanism"), e.get("episode_number")) for e in episodes]
    expected_keys = [(load, m, i) for load in fx["loads"] for m in fx["mechanisms"]
                     for i in range(fx["episodes_per_mechanism"])]
    actual_keys = [(e.get("load"), e.get("mechanism"), e.get("episode_number")) for e in episodes]
    if actual_keys != expected_keys:
        errors.append("episode_order_or_inventory")

    total_rows = 0
    for e in episodes:
        mechanism = e["mechanism"]
        load = e["load"]
        eid = e["episode_number"]
        expected_partition = "reference" if eid in fx["reference_episode_ids"] else "heldout"
        if e.get("episode_id") != f"{load}-{mechanism}-{eid:02d}":
            errors.append(f"episode_id:{mechanism}:{eid}")
        if e.get("partition") != expected_partition:
            errors.append(f"partition:{mechanism}:{eid}")
        ev = e.get("events", [])
        if len(ev) != fx["horizon_ticks"] or [x.get("tick") for x in ev] != list(range(fx["horizon_ticks"])):
            errors.append(f"event_inventory:{mechanism}:{eid}")
            continue
        total_rows += len(ev)
        backlog = 0
        observed_returns = []
        pending = None
        probe_n = 0
        for tick, x in enumerate(ev):
            if x.get("backlog_before") != backlog:
                errors.append(f"backlog_before:{mechanism}:{eid}:{tick}")
            shock = x.get("probe_units")
            loss = x.get("loss_units")
            demand = x.get("demand")
            service = x.get("service_units")
            if not all(isinstance(v, int) and v >= 0 for v in (shock, loss, demand, service)):
                errors.append(f"event_types:{mechanism}:{eid}:{tick}")
                continue
            expected_shock = fx["probe_units"] if tick in fx["probe_ticks"] else 0
            if mechanism == "variable_disturbance" and tick in fx["probe_ticks"]:
                expected_shock = 1 if fx["probe_ticks"].index(tick) % 2 else 3
            if shock != expected_shock:
                errors.append(f"probe_size:{mechanism}:{eid}:{tick}")
            expected_demand = 1 if mechanism == "demand_drift_no_loss" and 54 <= tick <= 70 else 0
            if demand != expected_demand:
                errors.append(f"demand:{mechanism}:{eid}:{tick}")
            expected_loss = fx["loss_units"] if mechanism in (
                "gradual_recovery_loss", "abrupt_breaker_loss", "spontaneous_failure"
            ) and tick == fx["loss_tick"] else 0
            if loss != expected_loss:
                errors.append(f"loss_event:{mechanism}:{eid}:{tick}")

            if tick in fx["probe_ticks"]:
                probe_index = fx["probe_ticks"].index(tick)
                if pending is not None:
                    errors.append(f"overlapping_probe:{mechanism}:{eid}:{tick}")
                pending = {"probe_tick": tick,
                           "service_tick": tick + expected_wait(mechanism, probe_index, fx) + 1,
                           "wait_ticks": expected_wait(mechanism, probe_index, fx)}
                probe_n += 1
            expected_service = 0
            if pending is not None and tick == pending["service_tick"]:
                expected_service = backlog + demand + shock + loss
            if service != expected_service:
                errors.append(f"service_schedule:{mechanism}:{eid}:{tick}")
            backlog = max(0, backlog + demand + shock + loss - service)
            if x.get("backlog") != backlog:
                errors.append(f"backlog_transition:{mechanism}:{eid}:{tick}")
            envelope = backlog <= fx["return_envelope_backlog_max"]
            if x.get("in_envelope") != envelope:
                errors.append(f"envelope:{mechanism}:{eid}:{tick}")
            if x.get("pointwise_margin") != fx["loads"][load] - fx["nominal_demand"] - demand:
                errors.append(f"margin:{mechanism}:{eid}:{tick}")
            if pending is not None and tick == pending["service_tick"] and envelope:
                observed_returns.append({"probe_tick": pending["probe_tick"],
                                         "wait_ticks": pending["wait_ticks"],
                                         "duration_ticks": tick - pending["probe_tick"],
                                         "return_tick": tick})
                pending = None

        if probe_n != len(fx["probe_ticks"]):
            errors.append(f"probe_count:{mechanism}:{eid}")
        if e.get("returns") != observed_returns:
            errors.append(f"return_intervals:{mechanism}:{eid}")
        durations = [r["duration_ticks"] for r in observed_returns]
        ratio = durations[-1] / durations[0] if len(durations) >= 2 and durations[0] else None
        recovery_warning = ratio is not None and ratio >= fx["recovery_ratio_warning_threshold"]
        margins = [x["pointwise_margin"] for x in ev if x["tick"] in fx["probe_ticks"]]
        margin_min = min(margins) if margins else None
        pointwise_warning = margin_min is not None and margin_min <= fx["pointwise_margin_warning_threshold"]
        future_loss_tick = next((x["tick"] for x in ev
                                 if x["tick"] > fx["probe_ticks"][-1] and x["loss_units"] > 0), None)
        future_loss = future_loss_tick is not None
        recovery_warning_tick = observed_returns[-1]["return_tick"] if recovery_warning and observed_returns else None
        pointwise_warning_tick = next((x["tick"] for x in ev if x["tick"] in fx["probe_ticks"]
                                       and x["pointwise_margin"] <= fx["pointwise_margin_warning_threshold"]), None)
        recovery_lead = future_loss_tick - recovery_warning_tick \
            if future_loss_tick is not None and recovery_warning_tick is not None else None
        pointwise_lead = future_loss_tick - pointwise_warning_tick \
            if future_loss_tick is not None and pointwise_warning_tick is not None else None
        unknown = pending is not None
        for key, val in (("recovery_ratio", ratio), ("recovery_warning", recovery_warning),
                         ("recovery_warning_tick", recovery_warning_tick),
                         ("recovery_warning_lead_ticks", recovery_lead),
                         ("pointwise_margin_min", margin_min), ("pointwise_warning", pointwise_warning),
                         ("pointwise_warning_tick", pointwise_warning_tick),
                         ("pointwise_warning_lead_ticks", pointwise_lead),
                         ("future_loss", future_loss), ("future_loss_tick", future_loss_tick),
                         ("unknown_return", unknown)):
            if e.get(key) != val:
                errors.append(f"derived_{key}:{mechanism}:{eid}")

    heldout = [e for e in episodes if e.get("partition") == "heldout"]
    target = [e for e in heldout if e.get("mechanism") == "gradual_recovery_loss" and e.get("future_loss")]
    negatives = [e for e in heldout if not e.get("future_loss") and not e.get("unknown_return")]
    recovery_sens = sum(e["recovery_warning"] for e in target) / len(target) if target else None
    margin_sens = sum(e["pointwise_warning"] for e in target) / len(target) if target else None
    recovery_fpr = sum(e["recovery_warning"] for e in negatives) / len(negatives) if negatives else None
    target_leads = [e["recovery_warning_lead_ticks"] for e in target if e["recovery_warning"]]
    minimum_target_lead = min(target_leads) if target_leads else None
    false_alarm_by_load = {
        load: (sum(e["recovery_warning"] for e in negatives if e.get("load") == load)
               / sum(e.get("load") == load for e in negatives))
        for load in fx["loads"]
    }
    pointwise_false_alarm_by_load = {
        load: (sum(e["pointwise_warning"] for e in negatives if e.get("load") == load)
               / sum(e.get("load") == load for e in negatives))
        for load in fx["loads"]
    }
    group_summary = {}
    for load in fx["loads"]:
        for mechanism in fx["mechanisms"]:
            group = [e for e in heldout if e.get("load") == load and e.get("mechanism") == mechanism]
            group_summary[f"{load}:{mechanism}"] = {
                "episodes": len(group),
                "recovery_warnings": sum(e["recovery_warning"] for e in group),
                "pointwise_warnings": sum(e["pointwise_warning"] for e in group),
                "future_loss_episodes": sum(e["future_loss"] for e in group),
                "unknown_return_episodes": sum(e["unknown_return"] for e in group),
            }
    pass_gate = bool(target and recovery_sens >= 0.75 and recovery_sens - margin_sens >= 0.25
                     and minimum_target_lead is not None
                     and minimum_target_lead >= fx["minimum_warning_lead_ticks"]
                     and recovery_fpr is not None and recovery_fpr <= 0.10
                     and all(v <= 0.10 for v in false_alarm_by_load.values())
                     and all(v <= 0.10 for v in pointwise_false_alarm_by_load.values())
                     and not errors)
    metrics = {"heldout_episodes": len(heldout), "target_gradual_loss_episodes": len(target),
               "gradual_recovery_sensitivity": recovery_sens,
               "pointwise_margin_sensitivity": margin_sens,
               "incremental_sensitivity": recovery_sens - margin_sens if target else None,
               "minimum_target_warning_lead_ticks": minimum_target_lead,
               "negative_episodes": len(negatives), "recovery_false_alarm_rate": recovery_fpr,
               "recovery_false_alarm_rate_by_load": false_alarm_by_load,
               "pointwise_false_alarm_rate_by_load": pointwise_false_alarm_by_load,
               "heldout_groups": group_summary,
               "gradual_recovery_warnings": sum(e["recovery_warning"] for e in target),
               "pointwise_warnings_on_gradual": sum(e["pointwise_warning"] for e in target),
               "recovery_warnings_on_negatives": sum(e["recovery_warning"] for e in negatives)}
    disposition = "PASS_METHOD_SCOPED" if pass_gate else ("FAIL_INTEGRITY" if errors else "FAIL_METHOD_SCOPED")
    return {"disposition": disposition, "errors": sorted(set(errors)),
            "event_rows": total_rows, "metrics": metrics}


def main():
    if len(sys.argv) != 2:
        raise SystemExit("usage: audit.py RAW.json")
    raw_path = Path(sys.argv[1])
    raw_bytes = raw_path.read_bytes()
    doc = json.loads(raw_bytes)
    fx = json.loads(FIXTURE.read_text())
    result = audit(doc, fx)
    result["raw_sha256"] = hashlib.sha256(raw_bytes).hexdigest()
    result["audit"] = "PASS_LEDGER_SCOPED" if result["disposition"] != "FAIL_INTEGRITY" else "FAIL_AUDIT"
    print(json.dumps(result, sort_keys=True, separators=(",", ":")))
    raise SystemExit(0 if result["disposition"] != "FAIL_INTEGRITY" else 1)


if __name__ == "__main__":
    main()
