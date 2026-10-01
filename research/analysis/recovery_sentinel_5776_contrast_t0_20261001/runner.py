#!/usr/bin/env python3
"""Frozen synthetic event-ledger candidate for fresh Issue #5776 allocation."""
import hashlib
import json
import sys
from pathlib import Path

FIXTURE = Path(__file__).with_name("fixture.json")


def episode(fx, load, mechanism, eid):
    probes = fx["probe_ticks"]
    waits = list(fx["fixed_recovery_wait_ticks"])
    backlog = 0
    rows = []
    returns = []
    pending_return = None
    for tick in range(fx["horizon_ticks"]):
        shock = fx["probe_units"] if tick in probes else 0
        demand = 1 if mechanism == "demand_drift_no_loss" and 54 <= tick <= 70 else 0
        loss = fx["loss_units"] if mechanism in ("gradual_recovery_loss", "abrupt_breaker_loss", "spontaneous_failure") and tick == fx["loss_tick"] else 0
        if mechanism == "variable_disturbance" and tick in probes:
            shock = 1 if probes.index(tick) % 2 else 3
        if mechanism == "reset_hysteresis" and tick in probes:
            wait = waits[0]
        elif mechanism in ("gradual_recovery_loss", "demand_drift_no_loss") and tick in probes:
            wait = waits[probes.index(tick)]
        else:
            wait = waits[0]

        # Service is a fully recorded exogenous transfer, not hidden runner state.
        before = backlog
        service = 0
        if pending_return is not None and tick == pending_return["service_tick"]:
            service = before + demand + shock + loss
        backlog = max(0, before + demand + shock + loss - service)

        if tick in probes:
            if pending_return is not None:
                pending_return["censored"] = True
            pending_return = {"probe_tick": tick, "service_tick": tick + wait + 1,
                              "probe_index": probes.index(tick), "wait_ticks": wait}

        if pending_return is not None and tick == pending_return["service_tick"] and backlog <= fx["return_envelope_backlog_max"]:
            returns.append({"probe_tick": pending_return["probe_tick"], "wait_ticks": pending_return["wait_ticks"],
                            "duration_ticks": tick - pending_return["probe_tick"], "return_tick": tick})
            pending_return = None

        rows.append({"tick": tick, "demand": demand, "probe_units": shock,
                     "loss_units": loss, "service_units": service,
                     "backlog_before": before, "backlog": backlog,
                     "pointwise_margin": fx["loads"][load] - fx["nominal_demand"] - demand,
                     "in_envelope": backlog <= fx["return_envelope_backlog_max"]})

    durations = [r["duration_ticks"] for r in returns]
    ratio = durations[-1] / durations[0] if len(durations) >= 2 and durations[0] else None
    recovery_warning = ratio is not None and ratio >= fx["recovery_ratio_warning_threshold"]
    pointwise_margin_min = min(x["pointwise_margin"] for x in rows if x["tick"] in probes)
    pointwise_warning = pointwise_margin_min <= fx["pointwise_margin_warning_threshold"]
    future_loss_tick = next((x["tick"] for x in rows if x["tick"] > probes[-1] and x["loss_units"] > 0), None)
    recovery_warning_tick = returns[-1]["return_tick"] if recovery_warning and returns else None
    pointwise_warning_tick = next((x["tick"] for x in rows if x["tick"] in probes
                                   and x["pointwise_margin"] <= fx["pointwise_margin_warning_threshold"]), None)
    return {
        "episode_id": f"{load}-{mechanism}-{eid:02d}",
        "load": load,
        "mechanism": mechanism,
        "episode_number": eid,
        "partition": "reference" if eid in fx["reference_episode_ids"] else "heldout",
        "events": rows,
        "returns": returns,
        "recovery_ratio": ratio,
        "recovery_warning": recovery_warning,
        "recovery_warning_tick": recovery_warning_tick,
        "recovery_warning_lead_ticks": future_loss_tick - recovery_warning_tick
            if future_loss_tick is not None and recovery_warning_tick is not None else None,
        "pointwise_margin_min": pointwise_margin_min,
        "pointwise_warning": pointwise_warning,
        "pointwise_warning_tick": pointwise_warning_tick,
        "pointwise_warning_lead_ticks": future_loss_tick - pointwise_warning_tick
            if future_loss_tick is not None and pointwise_warning_tick is not None else None,
        "future_loss": future_loss_tick is not None,
        "future_loss_tick": future_loss_tick,
        "unknown_return": pending_return is not None,
    }


def build(fx):
    episodes = [episode(fx, load, mechanism, eid)
                for load in fx["loads"]
                for mechanism in fx["mechanisms"]
                for eid in range(fx["episodes_per_mechanism"])]
    return {"schema": "recovery-sentinel-contrast-raw-v1",
            "allocation": fx["allocation"],
            "fixture_sha256": hashlib.sha256(FIXTURE.read_bytes()).hexdigest(),
            "episodes": episodes}


def main():
    if len(sys.argv) != 2:
        raise SystemExit("usage: runner.py OUTPUT.json")
    out = Path(sys.argv[1])
    if out.exists():
        raise SystemExit("STOP_OUTPUT_EXISTS")
    fx = json.loads(FIXTURE.read_text())
    doc = build(fx)
    raw = (json.dumps(doc, sort_keys=True, separators=(",", ":")) + "\n").encode()
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(raw)
    print(json.dumps({"candidate": "EXIT_0", "episodes": len(doc["episodes"]),
                      "event_rows": sum(len(e["events"]) for e in doc["episodes"]),
                      "raw_sha256": hashlib.sha256(raw).hexdigest()}, sort_keys=True))


if __name__ == "__main__":
    main()
