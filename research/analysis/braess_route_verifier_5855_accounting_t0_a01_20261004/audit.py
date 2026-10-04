"""Independent event-only ledger and finite-window audit for #5855 A01."""
import json
import math
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parent
RAW = ROOT / "candidate-output.json"
OUT = ROOT / "audit-result.json"
PRIORITY = {"verified": 0, "attempt_failed": 1, "offer": 2, "start": 3, "horizon": 9}


def replay(trace):
    errors = []
    offered = {}
    state = {}
    seen_event = set()
    seen_receipt = set()
    snapshots = []
    verified_at = {}
    horizon = trace["horizon"]
    events = trace["events"]
    expected_order = sorted(events, key=lambda e: (e["tick"], PRIORITY[e["kind"]], e["event_id"]))
    if events != expected_order:
        errors.append("event_order")
    previous_tick = -1
    area = 0
    active = 0
    last_tick = 0
    for event in events:
        tick, kind = event["tick"], event["kind"]
        if tick < previous_tick or tick > horizon:
            errors.append("event_time")
        if tick > last_tick:
            area += active * (tick - last_tick)
            last_tick = tick
        previous_tick = tick
        eid = event["event_id"]
        if eid in seen_event:
            errors.append("duplicate_event_id")
        seen_event.add(eid)
        task = event.get("task_id")
        if kind == "offer":
            if task in offered:
                errors.append("duplicate_offer")
            else:
                offered[task] = tick
                state[task] = "queued"
        elif kind == "start":
            if task not in offered or state.get(task) != "queued":
                errors.append("invalid_start")
            else:
                state[task] = "in_service"
        elif kind == "attempt_failed":
            receipt = event.get("receipt_id")
            if receipt in seen_receipt:
                errors.append("duplicate_receipt_id")
            seen_receipt.add(receipt)
            if task not in offered or state.get(task) != "in_service":
                errors.append("invalid_attempt_failure")
            else:
                state[task] = "queued"
        elif kind in {"verified", "rejected", "skipped", "lost"}:
            receipt = event.get("receipt_id")
            if receipt in seen_receipt:
                errors.append("duplicate_receipt_id")
            seen_receipt.add(receipt)
            if task not in offered or state.get(task) != "in_service":
                errors.append("duplicate_or_unmatched_terminal")
            else:
                state[task] = kind
                if kind == "verified":
                    verified_at[task] = tick
        elif kind == "horizon":
            pass
        else:
            errors.append("unknown_event_kind")

        active = sum(value in {"queued", "in_service"} for value in state.values())
        counts = Counter(state.values())
        ledger = {
            "initial_pending": trace["initial_pending"],
            "offered": len(offered),
            "verified": counts["verified"],
            "rejected": counts["rejected"],
            "skipped": counts["skipped"],
            "queued": counts["queued"],
            "in_service": counts["in_service"],
            "lost": counts["lost"],
        }
        accounted = sum(ledger[k] for k in ("verified", "rejected", "skipped", "queued", "in_service", "lost"))
        if ledger["initial_pending"] + ledger["offered"] != accounted:
            errors.append("conservation")
        snapshots.append({"event_id": eid, "ledger": ledger, "conserved": ledger["initial_pending"] + ledger["offered"] == accounted})
        if kind == "horizon":
            if tick != horizon:
                errors.append("wrong_horizon_event")
            break
    if not events or events[-1]["kind"] != "horizon":
        errors.append("missing_horizon")
    if last_tick < horizon:
        area += active * (horizon - last_tick)
    counts = Counter(state.values())
    latencies = [verified_at[t] - offered[t] for t in verified_at]
    duration = horizon
    time_average_occupancy = area / duration if duration > 0 else None
    lambda_offered = len(offered) / duration if duration > 0 else None
    lambda_verified = len(verified_at) / duration if duration > 0 else None
    mean_verified_sojourn = sum(latencies) / len(latencies) if latencies else None
    return {
        "errors": sorted(set(errors)),
        "accepted": not errors,
        "offered_ids": sorted(offered),
        "verified_ids": sorted(verified_at),
        "censored_ids": sorted(task for task, value in state.items() if value in {"queued", "in_service"}),
        "terminal_counts": {k: counts[k] for k in ("verified", "rejected", "skipped", "lost")},
        "ledger_snapshots": snapshots,
        "occupancy_area": area,
        "window_ticks": duration,
        "time_average_occupancy": time_average_occupancy,
        "lambda_offered": lambda_offered,
        "lambda_verified": lambda_verified,
        "mean_verified_sojourn": mean_verified_sojourn,
        "lambda_offered_times_mean_verified_sojourn": lambda_offered * mean_verified_sojourn if mean_verified_sojourn is not None else None,
        "lambda_verified_times_mean_verified_sojourn": lambda_verified * mean_verified_sojourn if mean_verified_sojourn is not None else None,
        "verified_mean_sojourn": mean_verified_sojourn,
        "verified_count": len(verified_at),
        "offered_count": len(offered),
    }


def audit(document):
    by_name = {trace["name"]: trace for trace in document["traces"]}
    out = {name: replay(trace) for name, trace in by_name.items()}
    baseline, added = out["matched-baseline"], out["matched-route-added"]
    duplicate, transient, stable = (out["duplicate-retry-receipt"], out["transient-startup"], out["stable-periodic-control"])
    checks = {
        "matched_ids_and_offers": baseline["offered_ids"] == added["offered_ids"] == ["t0", "t1", "t2", "t3"] and
            [e["tick"] for e in by_name["matched-baseline"]["events"] if e["kind"] == "offer"] ==
            [e["tick"] for e in by_name["matched-route-added"]["events"] if e["kind"] == "offer"],
        "complete_baseline_conserved": baseline["accepted"] and not baseline["censored_ids"] and all(s["conserved"] for s in baseline["ledger_snapshots"]),
        "route_censoring_preserved": added["accepted"] and added["censored_ids"] == ["t2", "t3"] and
            added["verified_count"] == 2 and added["offered_count"] == 4 and
            added["verified_mean_sojourn"] < baseline["verified_mean_sojourn"],
        "duplicate_receipt_rejected": not duplicate["accepted"] and "duplicate_receipt_id" in duplicate["errors"] and
            "duplicate_or_unmatched_terminal" in duplicate["errors"],
        "transient_not_steady_state": transient["accepted"] and transient["censored_ids"] == ["t1", "t2"] and
            by_name["transient-startup"]["window_kind"] == "transient" and
            not math.isclose(transient["time_average_occupancy"], transient["lambda_offered_times_mean_verified_sojourn"]),
        "stable_fixture_little_identity": stable["accepted"] and not stable["censored_ids"] and
            by_name["stable-periodic-control"]["window_kind"] == "stable_fixture" and
            math.isclose(stable["time_average_occupancy"], stable["lambda_verified_times_mean_verified_sojourn"], abs_tol=1e-12),
        "every_accepted_snapshot_conserved": all(
            all(s["conserved"] for s in value["ledger_snapshots"])
            for name, value in out.items() if name != "duplicate-retry-receipt"
        ),
        "candidate_summary_not_trusted": document["candidate_diagnostics"]["route_added_complete_only_mean"] ==
            added["verified_mean_sojourn"] and document["candidate_diagnostics"]["route_added_verified_count"] == 2,
    }
    return {"schema": "braess-queue-conservation-audit-a01-v1",
            "allocation": document["allocation"], "checks": checks,
            "trace_audits": out,
            "disposition": "PASS_ACCOUNTING_CONTROLS_SCOPED" if all(checks.values()) else "FAIL_ACCOUNTING"}


def main():
    document = json.loads(RAW.read_text(encoding="utf-8"))
    result = audit(document)
    OUT.write_text(json.dumps(result, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"disposition": result["disposition"], "checks": result["checks"], "output": OUT.name}, sort_keys=True))
    return 0 if result["disposition"] == "PASS_ACCOUNTING_CONTROLS_SCOPED" else 1


if __name__ == "__main__":
    raise SystemExit(main())
