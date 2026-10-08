"""Deterministic T0 candidate for Issue #7383; standard library only."""
from __future__ import annotations

import json
from pathlib import Path


HERE = Path(__file__).resolve().parent
SPEC = HERE / "spec.json"


def percentile(values: list[int], q: float) -> int | None:
    if not values:
        return None
    ordered = sorted(values)
    rank = max(1, (len(ordered) * int(q * 100) + 99) // 100)
    return ordered[rank - 1]


def primary_time(i: int) -> int:
    return 80 + i % 21 if i % 10 == 0 else 4 + i % 3


def traces(spec: dict) -> tuple[list[int], list[dict]]:
    calibration = [primary_time(i + 10_000) for i in range(spec["calibration_count"])]
    cases = []
    n = spec["test_count_per_condition"]
    for condition in spec["conditions"]:
        for i in range(n):
            p = primary_time(i + 20_000)
            s = p if condition == "correlated_tail" else 5 + ((i * 2) % 3)
            cases.append({
                "case_id": f"{condition}-{i:04d}",
                "condition": condition,
                "index": i,
                "primary_service_ms": p,
                "secondary_service_ms": s,
                "generation_transition_ms": 7 if condition == "generation_between_captures" else None,
                "capture_delay_ms": spec["capture_delay_ms"],
                "deadline_ms": spec["deadline_ms"],
                "cancel_lag_ms": spec["cancel_lag_ms"]["delayed_cancellation"] if condition == "delayed_cancellation" else spec["cancel_lag_ms"]["default"],
                "single_server": condition == "shared_queue_saturation",
            })
    return calibration, cases


def epoch_at(case: dict, time_ms: int) -> int:
    transition = case["generation_transition_ms"]
    return int(transition is not None and time_ms >= transition)


def run_arm(case: dict, arm: str, hedge_ms: int) -> dict:
    p = case["primary_service_ms"]
    if arm == "single":
        launches = [("primary", 0, p)]
    elif arm == "delayed_hedge":
        launches = [("primary", 0, p)]
        if p > hedge_ms:
            launches.append(("secondary", hedge_ms, case["secondary_service_ms"]))
    elif arm == "immediate_duplicate":
        launches = [("primary", 0, p), ("secondary", 0, case["secondary_service_ms"])]
    else:
        raise ValueError(arm)

    requests = []
    for rid, launch, service in launches:
        start = max(launch, p) if case["single_server"] and rid == "secondary" else launch
        capture = start + case["capture_delay_ms"]
        done = start + service
        requests.append({
            "request_id": rid,
            "launch_ms": launch,
            "start_ms": start,
            "capture_ms": capture,
            "complete_ms": done,
            "capture_epoch": epoch_at(case, capture),
            "complete": True,
            "service_ms": service,
        })

    valid = [r for r in requests if r["complete"] and r["capture_epoch"] == epoch_at(case, r["complete_ms"])]
    winner = min(valid, key=lambda r: (r["complete_ms"], r["request_id"])) if valid else None
    decision_ms = winner["complete_ms"] if winner else case["deadline_ms"]
    consumer = {
        "disposition": "ADMIT" if winner else "YIELD",
        "admitted_request_ids": [winner["request_id"]] if winner else [],
        "decision_ms": decision_ms,
        "latency_ms": winner["complete_ms"] if winner else None,
        "current_epoch": epoch_at(case, decision_ms),
        "deadline_miss": winner is None or winner["complete_ms"] > case["deadline_ms"],
        "timely_current_effect": bool(winner and winner["complete_ms"] <= case["deadline_ms"]),
    }

    for r in requests:
        if winner is None:
            cancel_at = case["deadline_ms"]
            ack_at = cancel_at + case["cancel_lag_ms"]
        elif r["request_id"] == winner["request_id"]:
            cancel_at = ack_at = None
        else:
            cancel_at = decision_ms
            ack_at = cancel_at + case["cancel_lag_ms"]
        if r["complete_ms"] <= (ack_at if ack_at is not None else r["complete_ms"]):
            consumed = r["service_ms"]
        elif cancel_at is None:
            consumed = r["service_ms"]
        else:
            consumed = max(0, min(r["service_ms"], ack_at - r["start_ms"]))
        r["cancel_requested_ms"] = cancel_at
        r["cancel_ack_ms"] = ack_at
        r["service_consumed_ms"] = consumed

    return {"arm": arm, "requests": requests, "consumer": consumer}


def summarize(rows: list[dict], arm_name: str) -> dict:
    consumers = [r["arms"][arm_name]["consumer"] for r in rows]
    latencies = [c["latency_ms"] for c in consumers if c["latency_ms"] is not None]
    primary = sum(r["primary_service_ms"] for r in rows)
    secondary_work = sum(
        req["service_consumed_ms"]
        for row in rows for arm in row["arms"].values()
        if arm["arm"] == "delayed_hedge"
        for req in arm["requests"] if req["request_id"] == "secondary"
    )
    return {
        "n": len(rows), "n_current": len(latencies),
        "p50_ms": percentile(latencies, 0.50),
        "p95_ms": percentile(latencies, 0.95),
        "p99_ms": percentile(latencies, 0.99),
        "deadline_misses": sum(c["deadline_miss"] for c in consumers),
        "timely_current_effects": sum(c["timely_current_effect"] for c in consumers),
        "baseline_primary_work_ms": primary,
        "delayed_secondary_work_ms": secondary_work,
        "delayed_duplicate_work_ratio": secondary_work / primary if primary else 0.0,
    }


def run(spec: dict) -> dict:
    calibration, cases = traces(spec)
    hedge_ms = percentile(calibration, spec["hedge_quantile"])
    rows = []
    for case in cases:
        rows.append({
            **case,
            "arms": {
                arm: run_arm(case, arm, hedge_ms)
                for arm in spec["arms"]
            },
        })
    summaries = {}
    for condition in spec["conditions"]:
        group = [r for r in rows if r["condition"] == condition]
        summaries[condition] = {
            arm: summarize(group, arm) for arm in spec["arms"]
        }
    return {
        "allocation": spec["allocation"],
        "base_main": spec["base_main"],
        "hedge_threshold_ms": hedge_ms,
        "calibration_n": len(calibration),
        "calibration_p90_ms": hedge_ms,
        "rows": rows,
        "summaries": summaries,
    }


def main() -> None:
    spec = json.loads(SPEC.read_text())
    result = run(spec)
    out = HERE / "results" / "candidate.json"
    if not out.parent.is_dir() or any(out.parent.iterdir()):
        raise SystemExit("fresh results directory required")
    out.write_text(json.dumps(result, sort_keys=True, indent=2) + "\n")
    print(json.dumps({"output": "results/candidate.json", "rows": len(result["rows"]), "hedge_threshold_ms": result["hedge_threshold_ms"]}, sort_keys=True))


if __name__ == "__main__":
    main()
