"""Independent raw-only opportunity ledger; deliberately does not import runner."""
from __future__ import annotations

import argparse
import json
import hashlib
import math
from pathlib import Path
from typing import Any


EXPECTED_SCENARIOS = ("inversion", "no_stall", "safe_stop", "expiry", "censored", "overlap", "unsynced", "no_exogenous")
EXPECTED_FIXTURE_SHA256 = "9a1f4068afbc95244dbd5e9331a136e3e441df23d3f19b4c9bd23374e90a9cee"


def _int(value: Any) -> bool:
    return type(value) is int


def _p95(cycles: list[dict[str, Any]], errors: list[str], where: str) -> int | None:
    latencies = []
    for i, cycle in enumerate(cycles):
        if not isinstance(cycle, dict):
            errors.append(f"{where}:cycle:{i}:not_object")
            continue
        start, end = cycle.get("start_ms"), cycle.get("end_ms")
        if not _int(start) or not _int(end) or end < start:
            errors.append(f"{where}:cycle:{i}:invalid_time")
            continue
        latencies.append(end - start)
    if not latencies:
        return None
    latencies.sort()
    return latencies[math.ceil(0.95 * len(latencies)) - 1]


def _outcomes(scenario: dict[str, Any], arm: dict[str, Any], errors: list[str], where: str) -> tuple[dict[str, str], dict[str, int | None], int | None]:
    opportunities = scenario.get("opportunities", [])
    horizon = scenario.get("horizon_ms")
    clock_aligned = scenario.get("clock_aligned")
    effects = arm.get("effects", [])
    stops = arm.get("safe_stops", [])
    if not isinstance(opportunities, list):
        errors.append(f"{where}:opportunities")
        opportunities = []
    if not _int(horizon) or type(clock_aligned) is not bool:
        errors.append(f"{where}:clock_or_horizon")
    if not isinstance(effects, list):
        errors.append(f"{where}:effects")
        effects = []
    valid_effects = []
    effect_ids = set()
    for i, event in enumerate(effects):
        if not isinstance(event, dict):
            errors.append(f"{where}:effect:{i}:not_object")
            continue
        event_id, event_time, regions = event.get("id"), event.get("time_ms"), event.get("regions")
        if not isinstance(event_id, str) or event_id in effect_ids:
            errors.append(f"{where}:effect:{i}:duplicate_or_invalid_id")
            continue
        effect_ids.add(event_id)
        if not _int(event_time) or not isinstance(regions, list) or any(not isinstance(x, str) for x in regions):
            errors.append(f"{where}:invalid_event_time")
            continue
        if clock_aligned is True and _int(horizon) and event_time > horizon:
            errors.append(f"{where}:event_after_observation_horizon")
            continue
        valid_effects.append(event)
    effects = valid_effects
    if not isinstance(stops, list):
        errors.append(f"{where}:safe_stops")
        stops = []
    valid_stops = []
    for i, stop in enumerate(stops):
        if not isinstance(stop, dict) or not _int(stop.get("time_ms")) or not isinstance(stop.get("region"), str):
            errors.append(f"{where}:safe_stop:{i}:invalid")
            continue
        if clock_aligned is True and _int(horizon) and stop["time_ms"] > horizon:
            errors.append(f"{where}:safe_stop:{i}:after_horizon")
            continue
        valid_stops.append(stop)
    stops = valid_stops
    out: dict[str, str] = {}
    first_effect_latency: dict[str, int | None] = {}
    uncovered_gaps: list[int] = []
    has_unknown = False
    ids = set()
    for i, opp in enumerate(opportunities):
        if not isinstance(opp, dict):
            errors.append(f"{where}:opportunity:{i}:not_object")
            continue
        oid, onset, expiry, region = (opp.get(k) for k in ("id", "onset_ms", "expiry_ms", "region"))
        if not isinstance(oid, str) or oid in ids:
            errors.append(f"{where}:opportunity:{i}:duplicate_or_invalid_id")
            continue
        ids.add(oid)
        if not _int(onset) or not _int(expiry) or expiry < onset or not isinstance(region, str):
            errors.append(f"{where}:opportunity:{oid}:invalid_contract")
            continue
        if clock_aligned is not True:
            out[oid] = "UNKNOWN"
            first_effect_latency[oid] = None
            has_unknown = True
            continue
        matched = [e for e in effects if region in e["regions"]]
        timely = [e for e in matched if onset <= e["time_ms"] <= expiry]
        late = [e for e in matched if e["time_ms"] > expiry]
        stopped = [e for e in stops if e.get("region") in (region, "*") and onset <= e["time_ms"] <= expiry]
        if timely:
            out[oid] = "MET"
            latency = min(e["time_ms"] for e in timely) - onset
            first_effect_latency[oid] = latency
            uncovered_gaps.append(latency)
        elif stopped:
            out[oid] = "SAFE_STOP"
            first_effect_latency[oid] = None
            uncovered_gaps.append(expiry - onset)
        elif late:
            out[oid] = "LATE"
            first_effect_latency[oid] = None
            uncovered_gaps.append(expiry - onset)
        elif not _int(horizon) or horizon < expiry:
            out[oid] = "UNKNOWN"
            first_effect_latency[oid] = None
            has_unknown = True
        else:
            out[oid] = "MISS"
            first_effect_latency[oid] = None
            uncovered_gaps.append(expiry - onset)
    longest_gap = max(uncovered_gaps) if uncovered_gaps and not has_unknown else None
    return out, first_effect_latency, longest_gap


def _busy_expired(scenario: dict[str, Any], arm: dict[str, Any], outcomes: dict[str, str], errors: list[str], where: str) -> list[str]:
    busy = arm.get("busy_intervals", [])
    cycles = arm.get("cycles", [])
    if not isinstance(busy, list):
        errors.append(f"{where}:busy_intervals")
        return []
    valid_busy = []
    for i, interval in enumerate(busy):
        if not isinstance(interval, dict) or not _int(interval.get("start_ms")) or not _int(interval.get("end_ms")) or interval["end_ms"] < interval["start_ms"]:
            errors.append(f"{where}:busy_interval:{i}:invalid")
            continue
        valid_busy.append(interval)
    if not isinstance(cycles, list):
        return []
    for ci, cycle in enumerate(cycles):
        if not isinstance(cycle, dict) or not _int(cycle.get("start_ms")) or not _int(cycle.get("end_ms")):
            continue
        for bi, interval in enumerate(valid_busy):
            if cycle["start_ms"] < interval["end_ms"] and cycle["end_ms"] > interval["start_ms"]:
                errors.append(f"{where}:cycle:{ci}:overlaps_busy_interval:{bi}")
    expired = []
    for opp in scenario.get("opportunities", []):
        if not isinstance(opp, dict) or not _int(opp.get("onset_ms")) or not _int(opp.get("expiry_ms")):
            continue
        fully_busy = any(i["start_ms"] <= opp["onset_ms"] and opp["expiry_ms"] <= i["end_ms"] for i in valid_busy)
        if fully_busy and outcomes.get(opp.get("id")) != "MET":
            expired.append(opp["id"])
    return sorted(expired)


def audit_raw(raw: dict[str, Any]) -> dict[str, Any]:
    errors: list[str] = []
    fixture_bytes = json.dumps(raw, sort_keys=True, separators=(",", ":")).encode("utf-8")
    fixture_sha256 = hashlib.sha256(fixture_bytes).hexdigest()
    if fixture_sha256 != EXPECTED_FIXTURE_SHA256:
        errors.append("fixture_identity")
    if not isinstance(raw, dict):
        errors.append("root_not_object")
        return {"disposition": "FAIL_METHOD", "raw_fixture_sha256": fixture_sha256, "results": {}, "errors": errors}
    if raw.get("schema") != "exogenous-opportunity-5694-raw-v1":
        errors.append("schema")
    scenarios = raw.get("scenarios")
    if not isinstance(scenarios, list) or tuple(s.get("name") for s in scenarios if isinstance(s, dict)) != EXPECTED_SCENARIOS:
        errors.append("scenario_matrix")
        scenarios = scenarios if isinstance(scenarios, list) else []
    results: dict[str, Any] = {}
    for scenario in scenarios:
        if not isinstance(scenario, dict):
            errors.append("invalid_scenario")
            continue
        name = scenario.get("name")
        arms = scenario.get("arms")
        if not isinstance(arms, dict):
            errors.append(f"{name}:arms")
            continue
        arm_results = {}
        for arm_name, arm in arms.items():
            if not isinstance(arm, dict):
                errors.append(f"{name}:{arm_name}:invalid_arm")
                continue
            if "opportunity_outcomes" in arm or "outcomes" in arm:
                errors.append(f"{name}:{arm_name}:precomputed_outcome_forbidden")
            outcomes, first_effect_latency, longest_gap = _outcomes(scenario, arm, errors, f"{name}:{arm_name}")
            cycles = arm.get("cycles", [])
            if not isinstance(cycles, list):
                errors.append(f"{name}:{arm_name}:cycles")
                cycles = []
            p95 = _p95(cycles, errors, f"{name}:{arm_name}")
            busy_expired = _busy_expired(scenario, arm, outcomes, errors, f"{name}:{arm_name}")
            arm_results[arm_name] = {
                "completed_cycle_p95_ms": p95,
                "opportunity_outcomes": outcomes,
                "useful_effects": {"met": sum(v == "MET" for v in outcomes.values()), "total": len(scenario.get("opportunities", []))},
                "opportunity_applicability": "APPLICABLE" if scenario.get("opportunities") else "NOT_APPLICABLE",
                "first_useful_effect_latency_ms": first_effect_latency,
                "longest_uncovered_opportunity_gap_ms": longest_gap,
                "busy_expired_opportunity_ids": busy_expired,
            }
        results[name] = {"arms": arm_results}
    inv = results.get("inversion", {}).get("arms", {})
    dense = inv.get("dense", {})
    sparse = inv.get("sparse", {})
    if dense.get("completed_cycle_p95_ms") != 30 or sparse.get("completed_cycle_p95_ms") != 5:
        errors.append("inversion:p95_expectation")
    if dense.get("useful_effects") != {"met": 3, "total": 3} or sparse.get("useful_effects") != {"met": 2, "total": 3}:
        errors.append("inversion:coverage_expectation")
    if sparse.get("opportunity_outcomes", {}).get("O2") != "MISS":
        errors.append("inversion:expired_opportunity_not_retained")
    if dense.get("first_useful_effect_latency_ms") != {"O1": 35, "O2": 35, "O3": 35} or dense.get("longest_uncovered_opportunity_gap_ms") != 35:
        errors.append("inversion:dense_effect_gap")
    if sparse.get("first_useful_effect_latency_ms") != {"O1": 10, "O2": None, "O3": 20} or sparse.get("longest_uncovered_opportunity_gap_ms") != 80:
        errors.append("inversion:sparse_effect_gap")
    if sparse.get("busy_expired_opportunity_ids") != ["O2"] or dense.get("busy_expired_opportunity_ids") != []:
        errors.append("inversion:busy_expiry")
    control = results.get("no_stall", {}).get("arms", {})
    fast, dense_control = control.get("fast", {}), control.get("dense", {})
    if fast.get("completed_cycle_p95_ms") != 5 or dense_control.get("completed_cycle_p95_ms") != 30:
        errors.append("no_stall:p95_expectation")
    full_coverage = {"met": 3, "total": 3}
    if fast.get("useful_effects") != full_coverage or dense_control.get("useful_effects") != full_coverage:
        errors.append("no_stall:coverage_expectation")
    if fast.get("longest_uncovered_opportunity_gap_ms") != 10 or dense_control.get("longest_uncovered_opportunity_gap_ms") != 35:
        errors.append("no_stall:effect_gap")
    stopped = results.get("safe_stop", {}).get("arms", {}).get("guarded", {})
    if stopped.get("opportunity_outcomes") != {"S1": "SAFE_STOP"} or stopped.get("useful_effects") != {"met": 0, "total": 1}:
        errors.append("safe_stop:classification")
    if stopped.get("longest_uncovered_opportunity_gap_ms") != 100:
        errors.append("safe_stop:window_gap")
    expired = results.get("expiry", {}).get("arms", {}).get("idle", {})
    censored = results.get("censored", {}).get("arms", {}).get("idle", {})
    if expired.get("opportunity_outcomes") != {"E1": "MISS"}:
        errors.append("expiry:classification")
    if censored.get("opportunity_outcomes") != {"C1": "UNKNOWN"}:
        errors.append("censored:classification")
    if censored.get("longest_uncovered_opportunity_gap_ms") is not None:
        errors.append("censored:unknown_gap_not_null")
    overlap = results.get("overlap", {}).get("arms", {})
    if overlap.get("both", {}).get("opportunity_outcomes") != {"A": "MET", "B": "MET"}:
        errors.append("overlap:both_regions")
    if overlap.get("both", {}).get("useful_effects") != {"met": 2, "total": 2}:
        errors.append("overlap:one_effect_per_opportunity")
    if overlap.get("b_only", {}).get("opportunity_outcomes") != {"A": "MISS", "B": "MET"}:
        errors.append("overlap:b_only_region")
    if overlap.get("both", {}).get("longest_uncovered_opportunity_gap_ms") != 75 or overlap.get("b_only", {}).get("longest_uncovered_opportunity_gap_ms") != 100:
        errors.append("overlap:gap")
    unsynced = results.get("unsynced", {}).get("arms", {}).get("local", {})
    if unsynced.get("completed_cycle_p95_ms") != 5 or unsynced.get("opportunity_outcomes") != {"U1": "UNKNOWN"}:
        errors.append("unsynced:clock_alignment")
    if unsynced.get("longest_uncovered_opportunity_gap_ms") is not None:
        errors.append("unsynced:unknown_gap_not_null")
    no_exogenous = results.get("no_exogenous", {}).get("arms", {}).get("idle", {})
    if no_exogenous.get("opportunity_applicability") != "NOT_APPLICABLE" or no_exogenous.get("useful_effects") != {"met": 0, "total": 0}:
        errors.append("no_exogenous:invented_denominator")
    return {"disposition": "PASS_METHOD_SCOPED" if not errors else "FAIL_METHOD", "raw_fixture_sha256": fixture_sha256, "results": results, "errors": errors}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("raw")
    parser.add_argument("--out")
    args = parser.parse_args()
    result = audit_raw(json.loads(Path(args.raw).read_text(encoding="utf-8")))
    text = json.dumps(result, sort_keys=True, separators=(",", ":")) + "\n"
    if args.out:
        Path(args.out).write_text(text, encoding="utf-8")
    print(text, end="")
    return 0 if result["disposition"] == "PASS_METHOD_SCOPED" else 1


if __name__ == "__main__":
    raise SystemExit(main())
