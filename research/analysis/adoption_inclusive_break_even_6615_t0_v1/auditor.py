#!/usr/bin/env python3
"""Independent raw-only reconstruction for Issue #6615 T0."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


EVENT_FIELDS = {
    "event_id", "case_id", "route", "seq", "kind", "task_id", "attempt_no",
    "status", "eligible", "attempted", "verified_useful", "wall_ms",
    "human_ms", "app_version_before", "app_version_after",
}


def _record(
    result: list[dict[str, Any]],
    case_id: str,
    route: str,
    kind: str,
    status: str,
    *,
    task_id: str | None = None,
    attempt_no: int | None = None,
    eligible: bool = False,
    attempted: bool = False,
    verified_useful: bool = False,
    wall_ms: int = 0,
    human_ms: int = 0,
    app_version_before: str | None = None,
    app_version_after: str | None = None,
) -> None:
    seq = len([r for r in result if r["case_id"] == case_id and r["route"] == route])
    result.append({
        "event_id": f"{case_id}:{route}:e{seq:03d}",
        "case_id": case_id,
        "route": route,
        "seq": seq,
        "kind": kind,
        "task_id": task_id,
        "attempt_no": attempt_no,
        "status": status,
        "eligible": eligible,
        "attempted": attempted,
        "verified_useful": verified_useful,
        "wall_ms": wall_ms,
        "human_ms": human_ms,
        "app_version_before": app_version_before,
        "app_version_after": app_version_after,
    })


def _reconstruct_expected_events(fixture: dict[str, Any]) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for case in fixture["cases"]:
        cid = case["case_id"]
        for route_name in fixture["routes"]:
            spec = case["routes"][route_name]
            setup = spec["setup"]
            ready = setup["status"] == "success"
            _record(
                result, cid, route_name, "setup",
                "SETUP_SUCCESS" if ready else "SETUP_FAILED",
                attempted=True, wall_ms=setup["wall_ms"], human_ms=setup["human_ms"],
                app_version_after=setup["app_version"],
            )
            active_version = setup["app_version"]
            repair_by_task = {r["before_task_id"]: r for r in spec["repairs"]}
            for opportunity in spec["opportunities"]:
                task = opportunity["task_id"]
                version = opportunity["app_version"]
                if not ready:
                    _record(
                        result, cid, route_name, "task_opportunity", "BLOCKED_SETUP_FAILURE",
                        task_id=task, eligible=opportunity["eligible"], app_version_after=version,
                    )
                    continue
                if not opportunity["eligible"]:
                    _record(
                        result, cid, route_name, "task_opportunity", "INELIGIBLE",
                        task_id=task, eligible=False, app_version_before=active_version,
                        app_version_after=version,
                    )
                    continue
                if spec["version_sensitive"] and active_version != version:
                    repair = repair_by_task.get(task)
                    if (
                        repair is None
                        or repair["from_version"] != active_version
                        or repair["to_version"] != version
                    ):
                        _record(
                            result, cid, route_name, "task_opportunity", "BLOCKED_STALE_ROUTE",
                            task_id=task, eligible=True, app_version_before=active_version,
                            app_version_after=version,
                        )
                        continue
                    _record(
                        result, cid, route_name, "repair", "REPAIR_SUCCESS",
                        task_id=task, eligible=True, attempted=True,
                        wall_ms=repair["wall_ms"], human_ms=repair["human_ms"],
                        app_version_before=repair["from_version"],
                        app_version_after=repair["to_version"],
                    )
                    active_version = repair["to_version"]
                attempts = opportunity["attempts"]
                if len(attempts) == 0:
                    _record(
                        result, cid, route_name, "task_opportunity", "NOT_ATTEMPTED",
                        task_id=task, eligible=True, app_version_before=active_version,
                        app_version_after=version,
                    )
                for index, attempt in enumerate(attempts, 1):
                    verified = attempt["outcome"] == "verified_success"
                    _record(
                        result, cid, route_name, "task_attempt",
                        "VERIFIED_SUCCESS" if verified else "FAILED",
                        task_id=task, attempt_no=index, eligible=True, attempted=True,
                        verified_useful=verified, wall_ms=attempt["wall_ms"],
                        human_ms=attempt["human_ms"],
                        app_version_before=active_version, app_version_after=version,
                    )
    return result


def _curve_for_rows(rows: list[dict[str, Any]], horizon: int, successful_setup: bool) -> dict[str, Any]:
    if not successful_setup:
        return {
            "adoption": {str(n): {"status": "NOT_REACHED"} for n in range(1, horizon + 1)},
            "prepared_only": {
                str(n): {"status": "NOT_APPLICABLE_SETUP_FAILED"}
                for n in range(1, horizon + 1)
            },
        }
    setup_event = next(r for r in rows if r["kind"] == "setup")
    elapsed_wall = elapsed_human = 0
    first_completion_cost: dict[int, tuple[int, int]] = {}
    verified_ids: set[str] = set()
    for row in rows:
        elapsed_wall += row["wall_ms"]
        elapsed_human += row["human_ms"]
        if row["verified_useful"] and row["task_id"] not in verified_ids:
            verified_ids.add(row["task_id"])
            first_completion_cost[len(verified_ids)] = (elapsed_wall, elapsed_human)
    adoption: dict[str, Any] = {}
    prepared: dict[str, Any] = {}
    for n in range(1, horizon + 1):
        key = str(n)
        if n not in first_completion_cost:
            adoption[key] = {"status": "NOT_REACHED"}
            prepared[key] = {"status": "NOT_REACHED"}
        else:
            wall, human = first_completion_cost[n]
            adoption[key] = {"status": "REACHED", "wall_ms": wall, "human_ms": human}
            prepared[key] = {
                "status": "REACHED",
                "wall_ms": wall - setup_event["wall_ms"],
                "human_ms": human - setup_event["human_ms"],
            }
    return {"adoption": adoption, "prepared_only": prepared}


def _metric_comparison(
    curves: dict[str, Any], horizon: int, view: str, metric: str
) -> dict[str, Any]:
    values: list[tuple[int, bool]] = []
    first_unreached_n = None
    for n in range(1, horizon + 1):
        a, b = curves["direct"][view][str(n)], curves["guarded"][view][str(n)]
        if a["status"] == "REACHED" and b["status"] == "REACHED":
            values.append((n, b[metric] < a[metric]))
        else:
            first_unreached_n = n
            break
    switch, after_nonbenefit = None, None
    prior = None
    had_nonbenefit = False
    for n, faster in values:
        if prior is not None and faster != prior and switch is None:
            switch = n
        if not faster:
            had_nonbenefit = True
        elif had_nonbenefit and after_nonbenefit is None:
            after_nonbenefit = n
        prior = faster
    return {
        "comparable_n": [n for n, _ in values],
        "first_unreached_n": first_unreached_n,
        "guarded_faster_by_n": {str(n): faster for n, faster in values},
        "guarded_faster_all_comparable_n": bool(values) and first_unreached_n is None and len(values) == horizon and all(flag for _, flag in values),
        "guarded_faster_all_reached_n": bool(values) and all(flag for _, flag in values),
        "relation_switch_n": switch,
        "crossing_after_nonbenefit_n": after_nonbenefit,
    }


def _recompute_analysis(
    fixture: dict[str, Any], raw_events: list[dict[str, Any]]
) -> dict[str, Any]:
    cases: dict[str, Any] = {}
    for case in fixture["cases"]:
        cid = case["case_id"]
        rows = [r for r in raw_events if r["case_id"] == cid]
        curves: dict[str, Any] = {}
        denominators: dict[str, Any] = {}
        for route_name in fixture["routes"]:
            route_spec = case["routes"][route_name]
            route_rows = [r for r in rows if r["route"] == route_name]
            curve = _curve_for_rows(
                route_rows, case["horizon_n"], route_spec["setup"]["status"] == "success"
            )
            unique_verified = {
                r["task_id"] for r in route_rows if r["verified_useful"]
            }
            curve.update({
                "status": "SETUP_SUCCESS" if route_spec["setup"]["status"] == "success"
                else "NOT_APPLICABLE_SETUP_FAILED",
                "assigned_opportunities": len(route_spec["opportunities"]),
                "eligible_opportunities": sum(1 for o in route_spec["opportunities"] if o["eligible"]),
                "attempted_attempts": sum(1 for r in route_rows if r["kind"] == "task_attempt"),
                "verified_useful_tasks": len(unique_verified),
            })
            curves[route_name] = curve
            denominators[route_name] = {
                k: curve[k] for k in (
                    "assigned_opportunities", "eligible_opportunities",
                    "attempted_attempts", "verified_useful_tasks",
                )
            }
        comparisons: dict[str, Any] = {}
        for view in ("prepared_only", "adoption"):
            comparisons[view] = {
                metric: _metric_comparison(curves, case["horizon_n"], view, metric)
                for metric in ("wall_ms", "human_ms")
            }
        cases[cid] = {
            "horizon_n": case["horizon_n"],
            "denominators": denominators,
            "curves": curves,
            "comparisons": comparisons,
        }
    return {"cases": cases}


def _check_frozen_gates(fixture: dict[str, Any], analysis: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    for case in fixture["cases"]:
        cid = case["case_id"]
        expected = case["expected"]
        result = analysis["cases"][cid]
        for view, key in (
            ("prepared_only", "prepared"),
            ("adoption", "adoption"),
        ):
            metric = result["comparisons"][view]["wall_ms"]
            expected_values = {
                f"{key}_wall_crossing_n": metric["crossing_after_nonbenefit_n"],
                f"{key}_wall_relation_switch_n": metric["relation_switch_n"],
                f"{key}_guarded_faster_all_reached_n": metric["guarded_faster_all_comparable_n"],
                f"{key}_first_unreached_n": metric["first_unreached_n"],
            }
            for expected_key, actual in expected_values.items():
                if expected_key in expected and actual != expected[expected_key]:
                    errors.append(f"{cid}: {expected_key} expected={expected[expected_key]} actual={actual}")
        for n in range(1, case["horizon_n"] + 1):
            expected_key = f"guarded_reached_n{n}"
            if expected_key in expected:
                actual = result["curves"]["guarded"]["adoption"][str(n)]["status"] == "REACHED"
                if actual != expected[expected_key]:
                    errors.append(f"{cid}: {expected_key} expected={expected[expected_key]} actual={actual}")
    return errors


def audit(fixture: dict[str, Any], raw: dict[str, Any]) -> dict[str, Any]:
    errors: list[str] = []
    if raw.get("schema") != "adoption-inclusive-verified-work-raw-v1":
        errors.append("raw schema mismatch")
    if raw.get("allocation_id") != fixture.get("allocation_id"):
        errors.append("allocation id mismatch")
    events = raw.get("events")
    if not isinstance(events, list):
        events = []
        errors.append("raw events is not a list")
    for index, row in enumerate(events):
        if not isinstance(row, dict) or set(row) != EVENT_FIELDS:
            errors.append(f"event {index}: field inventory mismatch")
            continue
        for key in ("wall_ms", "human_ms", "seq"):
            value = row[key]
            if type(value) is not int or value < 0:
                errors.append(f"event {index}: invalid nonnegative integer {key}")
        if type(row["attempted"]) is not bool or type(row["verified_useful"]) is not bool:
            errors.append(f"event {index}: invalid boolean accounting field")
        if row["verified_useful"] and not row["attempted"]:
            errors.append(f"event {index}: verified completion without attempt")
        if row["verified_useful"] and not row["eligible"]:
            errors.append(f"event {index}: ineligible work credited as verified")
    expected_events = _reconstruct_expected_events(fixture)
    exact_event_match = events == expected_events
    if not exact_event_match:
        errors.append("raw event rows differ from independent fixture reconstruction")
    # Reconstruct from the frozen expectation when the submitted ledger is
    # malformed, so deletion/omission mutations become a typed audit failure
    # instead of crashing on a missing setup row.
    recomputed = _recompute_analysis(fixture, events if exact_event_match else expected_events)
    if raw.get("analysis") != recomputed:
        errors.append("candidate analysis differs from independent curve reconstruction")
    errors.extend(_check_frozen_gates(fixture, recomputed))
    return {
        "audit_status": "PASS_METHOD_SCOPED" if not errors else "HOLD_AUDIT_INTEGRITY",
        "allocation_id": fixture["allocation_id"],
        "event_rows": len(events),
        "reconstructed_event_rows": len(expected_events),
        "case_count": len(fixture["cases"]),
        "errors": errors,
        "scope": "synthetic accounting method only; no actual setup, user, GUI, model, or product result",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("fixture")
    parser.add_argument("raw")
    parser.add_argument("output")
    args = parser.parse_args()
    fixture = json.loads(Path(args.fixture).read_text(encoding="utf-8"))
    raw = json.loads(Path(args.raw).read_text(encoding="utf-8"))
    result = audit(fixture, raw)
    Path(args.output).write_text(json.dumps(result, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, sort_keys=True))
    return 0 if result["audit_status"] == "PASS_METHOD_SCOPED" else 2


if __name__ == "__main__":
    raise SystemExit(main())
