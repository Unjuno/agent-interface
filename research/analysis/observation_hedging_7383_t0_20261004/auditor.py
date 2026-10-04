"""Independent raw-result checker; intentionally does not import candidate.py."""
from __future__ import annotations

import copy
import json
from pathlib import Path


HERE = Path(__file__).resolve().parent


class AuditError(ValueError):
    pass


def _epoch(case: dict, t: int) -> int:
    change = case["generation_transition_ms"]
    return 0 if change is None or t < change else 1


def _calibration_p90(spec: dict) -> int:
    vals = []
    for j in range(spec["calibration_count"]):
        i = j + 10_000
        vals.append(80 + i % 21 if i % 10 == 0 else 4 + i % 3)
    vals.sort()
    return vals[(len(vals) * 90 + 99) // 100 - 1]


def _input_rows(spec: dict) -> list[dict]:
    out = []
    for condition in spec["conditions"]:
        for j in range(spec["test_count_per_condition"]):
            i = j + 20_000
            primary = 80 + i % 21 if i % 10 == 0 else 4 + i % 3
            secondary = primary if condition == "correlated_tail" else 5 + ((j * 2) % 3)
            out.append({
                "case_id": f"{condition}-{j:04d}", "condition": condition, "index": j,
                "primary_service_ms": primary, "secondary_service_ms": secondary,
                "generation_transition_ms": 7 if condition == "generation_between_captures" else None,
                "capture_delay_ms": spec["capture_delay_ms"], "deadline_ms": spec["deadline_ms"],
                "cancel_lag_ms": spec["cancel_lag_ms"]["delayed_cancellation"] if condition == "delayed_cancellation" else spec["cancel_lag_ms"]["default"],
                "single_server": condition == "shared_queue_saturation",
            })
    return out


def _reference_arm(c: dict, label: str, threshold: int) -> dict:
    p = c["primary_service_ms"]
    if label == "single":
        descriptors = [("primary", 0, p)]
    else:
        secondary_launch = threshold if label == "delayed_hedge" else 0
        descriptors = [("primary", 0, p)]
        if label == "immediate_duplicate" or p > threshold:
            descriptors.append(("secondary", secondary_launch, c["secondary_service_ms"]))

    replies = []
    for request_id, launch, service in descriptors:
        starts = max(launch, p) if c["single_server"] and request_id == "secondary" else launch
        capture = starts + c["capture_delay_ms"]
        finish = starts + service
        replies.append({
            "request_id": request_id, "launch_ms": launch, "start_ms": starts,
            "capture_ms": capture, "complete_ms": finish,
            "capture_epoch": _epoch(c, capture), "complete": True,
            "service_ms": service,
        })

    eligible = [q for q in replies if q["complete"] and q["capture_epoch"] == _epoch(c, q["complete_ms"])]
    eligible.sort(key=lambda q: (q["complete_ms"], q["request_id"]))
    winner = eligible[0] if eligible else None
    decision = winner["complete_ms"] if winner else c["deadline_ms"]
    consumer = {
        "disposition": "ADMIT" if winner else "YIELD",
        "admitted_request_ids": [winner["request_id"]] if winner else [],
        "decision_ms": decision,
        "latency_ms": winner["complete_ms"] if winner else None,
        "current_epoch": _epoch(c, decision),
        "deadline_miss": winner is None or winner["complete_ms"] > c["deadline_ms"],
        "timely_current_effect": bool(winner is not None and winner["complete_ms"] <= c["deadline_ms"]),
    }
    for q in replies:
        if winner is None:
            cancel_start = c["deadline_ms"]
            cancel_end = cancel_start + c["cancel_lag_ms"]
        elif q["request_id"] == winner["request_id"]:
            cancel_start = cancel_end = None
        else:
            cancel_start = decision
            cancel_end = cancel_start + c["cancel_lag_ms"]
        if cancel_end is None or q["complete_ms"] <= cancel_end:
            spent = q["service_ms"]
        else:
            spent = max(0, min(q["service_ms"], cancel_end - q["start_ms"]))
        q["cancel_requested_ms"] = cancel_start
        q["cancel_ack_ms"] = cancel_end
        q["service_consumed_ms"] = spent
    return {"arm": label, "requests": replies, "consumer": consumer}


def _nearest_rank(xs: list[int], pct: int) -> int | None:
    if not xs:
        return None
    ordered = sorted(xs)
    return ordered[(len(ordered) * pct + 99) // 100 - 1]


def _summary(rows: list[dict], arm_name: str) -> dict:
    selected = [r["arms"][arm_name]["consumer"] for r in rows]
    latencies = [x["latency_ms"] for x in selected if x["latency_ms"] is not None]
    baseline_work = sum(x["primary_service_ms"] for x in rows)
    duplicate = sum(
        req["service_consumed_ms"]
        for row in rows for req in row["arms"]["delayed_hedge"]["requests"]
        if req["request_id"] == "secondary"
    )
    return {
        "n": len(rows), "n_current": len(latencies),
        "p50_ms": _nearest_rank(latencies, 50),
        "p95_ms": _nearest_rank(latencies, 95),
        "p99_ms": _nearest_rank(latencies, 99),
        "deadline_misses": sum(x["deadline_miss"] for x in selected),
        "timely_current_effects": sum(x["timely_current_effect"] for x in selected),
        "baseline_primary_work_ms": baseline_work,
        "delayed_secondary_work_ms": duplicate,
        "delayed_duplicate_work_ratio": duplicate / baseline_work if baseline_work else 0.0,
    }


def validate(spec: dict, data: dict) -> dict:
    if data.get("allocation") != spec["allocation"] or data.get("base_main") != spec["base_main"]:
        raise AuditError("allocation or base ref mismatch")
    threshold = _calibration_p90(spec)
    if data.get("hedge_threshold_ms") != threshold or data.get("calibration_n") != spec["calibration_count"]:
        raise AuditError("calibration threshold mismatch")
    expected_inputs = _input_rows(spec)
    rows = data.get("rows")
    if not isinstance(rows, list) or len(rows) != len(expected_inputs):
        raise AuditError("row inventory mismatch")
    for row, source in zip(rows, expected_inputs, strict=True):
        for field, value in source.items():
            if row.get(field) != value:
                raise AuditError(f"source input mismatch: {row.get('case_id')}:{field}")
        arms = row.get("arms")
        if not isinstance(arms, dict) or set(arms) != set(spec["arms"]):
            raise AuditError(f"arm inventory mismatch: {row['case_id']}")
        for arm_name in spec["arms"]:
            want = _reference_arm(source, arm_name, threshold)
            if arms[arm_name] != want:
                raise AuditError(f"raw response/cancel/winner mismatch: {row['case_id']}:{arm_name}")
            decision = arms[arm_name]["consumer"]
            ids = decision["admitted_request_ids"]
            if len(ids) > 1 or len(set(ids)) != len(ids):
                raise AuditError("more than one winning receipt")
            if decision["disposition"] == "ADMIT":
                reply = next(x for x in arms[arm_name]["requests"] if x["request_id"] == ids[0])
                if not reply["complete"] or reply["capture_epoch"] != decision["current_epoch"]:
                    raise AuditError("partial or stale observation admitted")

    summaries = {}
    for condition in spec["conditions"]:
        group = [x for x in rows if x["condition"] == condition]
        summaries[condition] = {a: _summary(group, a) for a in spec["arms"]}
    if data.get("summaries") != summaries:
        raise AuditError("summary reconstruction mismatch")

    base = summaries["iid_heavy_tail"]["single"]
    hedge = summaries["iid_heavy_tail"]["delayed_hedge"]
    if not base["p95_ms"] or not hedge["p95_ms"]:
        raise AuditError("heavy-tail p95 missing")
    gain = (base["p95_ms"] - hedge["p95_ms"]) / base["p95_ms"]
    if gain < spec["required_p95_relative_gain"]:
        raise AuditError("heavy-tail p95 gain below preregistered floor")
    if hedge["delayed_duplicate_work_ratio"] > spec["work_ceiling_ratio"]:
        raise AuditError("duplicate-work ceiling exceeded")
    if hedge["deadline_misses"] > base["deadline_misses"]:
        raise AuditError("deadline outcome worsened")

    return {
        "disposition": "PASS_METHOD_SCOPED",
        "conditions": summaries,
        "iid_heavy_tail_p95_relative_gain": gain,
        "iid_heavy_tail_work_ratio": hedge["delayed_duplicate_work_ratio"],
        "iid_heavy_tail_deadline_misses": {
            "single": base["deadline_misses"], "delayed_hedge": hedge["deadline_misses"]
        },
        "checks": {
            "rows_reconstructed": len(rows), "arms_per_row": len(spec["arms"]),
            "all_winners_complete_current_unique": True,
            "loser_work_reconstructed": True,
            "generation_transition_fail_closed": True,
        },
    }


def mutations(spec: dict, data: dict) -> list[dict]:
    controls = []
    cases = [
        ("partial_bytes", "iid_heavy_tail-0000", "single", lambda a: a["requests"][0].__setitem__("complete", False)),
        ("old_epoch_arrived_first", "generation_between_captures-0000", "delayed_hedge", lambda a: next(r for r in a["requests"] if r["request_id"] == "secondary").__setitem__("capture_epoch", 0)),
        ("double_admission", "correlated_tail-0001", "delayed_hedge", lambda a: a["consumer"]["admitted_request_ids"].append("secondary")),
        ("loser_work_omitted", "correlated_tail-0000", "delayed_hedge", lambda a: next(r for r in a["requests"] if r["request_id"] == "secondary").__setitem__("service_consumed_ms", 0)),
    ]
    for name, case_id, arm, mutate in cases:
        altered = copy.deepcopy(data)
        row = next(x for x in altered["rows"] if x["case_id"] == case_id)
        mutate(row["arms"][arm])
        try:
            validate(spec, altered)
        except (AuditError, KeyError, TypeError, ValueError):
            controls.append({"name": name, "rejected": True})
        else:
            controls.append({"name": name, "rejected": False})
    return controls


def main() -> None:
    spec = json.loads((HERE / "spec.json").read_text())
    candidate = json.loads((HERE / "results" / "candidate.json").read_text())
    result = validate(spec, candidate)
    controls = mutations(spec, candidate)
    result["mutation_controls"] = controls
    if len(controls) != 4 or not all(x["rejected"] for x in controls):
        result["disposition"] = "FAIL_METHOD"
    target = HERE / "results" / "audit_result.json"
    target.write_text(json.dumps(result, sort_keys=True, indent=2) + "\n")
    print(json.dumps({"output": "results/audit_result.json", "disposition": result["disposition"], "mutations_rejected": sum(x["rejected"] for x in controls)}, sort_keys=True))
    if result["disposition"] != "PASS_METHOD_SCOPED":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
