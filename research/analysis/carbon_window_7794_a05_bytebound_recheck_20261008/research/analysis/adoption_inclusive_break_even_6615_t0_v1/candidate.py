#!/usr/bin/env python3
"""Materialize the frozen synthetic adoption-cost ledger."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def _event(
    rows: list[dict[str, Any]],
    case_id: str,
    route_name: str,
    *,
    kind: str,
    status: str,
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
    seq = sum(1 for row in rows if row["case_id"] == case_id and row["route"] == route_name)
    rows.append(
        {
            "event_id": f"{case_id}:{route_name}:e{seq:03d}",
            "case_id": case_id,
            "route": route_name,
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
        }
    )


def build_events(fixture: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for case in fixture["cases"]:
        case_id = case["case_id"]
        for route_name in fixture["routes"]:
            route = case["routes"][route_name]
            setup = route["setup"]
            setup_ok = setup["status"] == "success"
            _event(
                rows,
                case_id,
                route_name,
                kind="setup",
                status="SETUP_SUCCESS" if setup_ok else "SETUP_FAILED",
                attempted=True,
                wall_ms=setup["wall_ms"],
                human_ms=setup["human_ms"],
                app_version_after=setup["app_version"],
            )
            current_version = setup["app_version"]
            repairs = {item["before_task_id"]: item for item in route["repairs"]}
            for opportunity in route["opportunities"]:
                task_id = opportunity["task_id"]
                if not setup_ok:
                    _event(
                        rows,
                        case_id,
                        route_name,
                        kind="task_opportunity",
                        task_id=task_id,
                        status="BLOCKED_SETUP_FAILURE",
                        eligible=opportunity["eligible"],
                        app_version_after=opportunity["app_version"],
                    )
                    continue
                if not opportunity["eligible"]:
                    _event(
                        rows,
                        case_id,
                        route_name,
                        kind="task_opportunity",
                        task_id=task_id,
                        status="INELIGIBLE",
                        eligible=False,
                        app_version_before=current_version,
                        app_version_after=opportunity["app_version"],
                    )
                    continue
                if route["version_sensitive"] and current_version != opportunity["app_version"]:
                    repair = repairs.get(task_id)
                    if (
                        repair is None
                        or repair["from_version"] != current_version
                        or repair["to_version"] != opportunity["app_version"]
                    ):
                        _event(
                            rows,
                            case_id,
                            route_name,
                            kind="task_opportunity",
                            task_id=task_id,
                            status="BLOCKED_STALE_ROUTE",
                            eligible=True,
                            app_version_before=current_version,
                            app_version_after=opportunity["app_version"],
                        )
                        continue
                    _event(
                        rows,
                        case_id,
                        route_name,
                        kind="repair",
                        task_id=task_id,
                        status="REPAIR_SUCCESS",
                        eligible=True,
                        attempted=True,
                        wall_ms=repair["wall_ms"],
                        human_ms=repair["human_ms"],
                        app_version_before=repair["from_version"],
                        app_version_after=repair["to_version"],
                    )
                    current_version = repair["to_version"]
                attempts = opportunity["attempts"]
                if not attempts:
                    _event(
                        rows,
                        case_id,
                        route_name,
                        kind="task_opportunity",
                        task_id=task_id,
                        status="NOT_ATTEMPTED",
                        eligible=True,
                        app_version_before=current_version,
                        app_version_after=opportunity["app_version"],
                    )
                    continue
                for attempt_no, attempt in enumerate(attempts, start=1):
                    success = attempt["outcome"] == "verified_success"
                    _event(
                        rows,
                        case_id,
                        route_name,
                        kind="task_attempt",
                        task_id=task_id,
                        attempt_no=attempt_no,
                        status="VERIFIED_SUCCESS" if success else "FAILED",
                        eligible=True,
                        attempted=True,
                        verified_useful=success,
                        wall_ms=attempt["wall_ms"],
                        human_ms=attempt["human_ms"],
                        app_version_before=current_version,
                        app_version_after=opportunity["app_version"],
                    )
    return rows


def _route_curve(
    events: list[dict[str, Any]], route_name: str, horizon: int, setup_status: str
) -> dict[str, Any]:
    route_events = [row for row in events if row["route"] == route_name]
    setup = next(row for row in route_events if row["kind"] == "setup")
    if setup_status != "success":
        return {
            "status": "NOT_APPLICABLE_SETUP_FAILED",
            "assigned_opportunities": 0,
            "eligible_opportunities": 0,
            "attempted_attempts": 0,
            "verified_useful_tasks": 0,
            "adoption": {str(n): {"status": "NOT_REACHED"} for n in range(1, horizon + 1)},
            "prepared_only": {str(n): {"status": "NOT_APPLICABLE_SETUP_FAILED"} for n in range(1, horizon + 1)},
        }

    cumulative_wall = 0
    cumulative_human = 0
    successes: dict[int, dict[str, int]] = {}
    completed: set[str] = set()
    for row in route_events:
        cumulative_wall += row["wall_ms"]
        cumulative_human += row["human_ms"]
        if row["verified_useful"] and row["task_id"] not in completed:
            completed.add(row["task_id"])
            successes[len(completed)] = {
                "wall_ms": cumulative_wall,
                "human_ms": cumulative_human,
            }
    adoption: dict[str, Any] = {}
    prepared: dict[str, Any] = {}
    for n in range(1, horizon + 1):
        key = str(n)
        if n not in successes:
            adoption[key] = {"status": "NOT_REACHED"}
            prepared[key] = {"status": "NOT_REACHED"}
        else:
            adoption[key] = {"status": "REACHED", **successes[n]}
            prepared[key] = {
                "status": "REACHED",
                "wall_ms": successes[n]["wall_ms"] - setup["wall_ms"],
                "human_ms": successes[n]["human_ms"] - setup["human_ms"],
            }
    return {
        "status": "SETUP_SUCCESS",
        "adoption": adoption,
        "prepared_only": prepared,
    }


def _comparison(
    curves: dict[str, Any], horizon: int, curve_name: str, metric: str
) -> dict[str, Any]:
    comparable: list[tuple[int, bool]] = []
    first_unreached_n = None
    for n in range(1, horizon + 1):
        direct = curves["direct"][curve_name][str(n)]
        guarded = curves["guarded"][curve_name][str(n)]
        if direct["status"] == "REACHED" and guarded["status"] == "REACHED":
            comparable.append((n, guarded[metric] < direct[metric]))
        else:
            first_unreached_n = n
            break
    relation_switch_n = None
    crossing_n = None
    seen_not_faster = False
    previous = None
    for n, guarded_faster in comparable:
        if previous is not None and guarded_faster != previous and relation_switch_n is None:
            relation_switch_n = n
        if not guarded_faster:
            seen_not_faster = True
        elif seen_not_faster and crossing_n is None:
            crossing_n = n
        previous = guarded_faster
    return {
        "comparable_n": [n for n, _ in comparable],
        "first_unreached_n": first_unreached_n,
        "guarded_faster_by_n": {str(n): faster for n, faster in comparable},
        "guarded_faster_all_comparable_n": bool(comparable) and first_unreached_n is None and len(comparable) == horizon and all(faster for _, faster in comparable),
        "guarded_faster_all_reached_n": bool(comparable) and all(faster for _, faster in comparable),
        "relation_switch_n": relation_switch_n,
        "crossing_after_nonbenefit_n": crossing_n,
    }


def build_analysis(fixture: dict[str, Any], events: list[dict[str, Any]]) -> dict[str, Any]:
    cases: dict[str, Any] = {}
    for case in fixture["cases"]:
        case_id = case["case_id"]
        case_events = [row for row in events if row["case_id"] == case_id]
        route_curves: dict[str, Any] = {}
        denominators: dict[str, Any] = {}
        for route_name in fixture["routes"]:
            route_spec = case["routes"][route_name]
            route_events = [row for row in case_events if row["route"] == route_name]
            setup_status = route_spec["setup"]["status"]
            curve = _route_curve(route_events, route_name, case["horizon_n"], setup_status)
            curve["assigned_opportunities"] = len(route_spec["opportunities"])
            curve["eligible_opportunities"] = sum(bool(item["eligible"]) for item in route_spec["opportunities"])
            curve["attempted_attempts"] = sum(row["kind"] == "task_attempt" for row in route_events)
            curve["verified_useful_tasks"] = len({
                row["task_id"] for row in route_events if row["verified_useful"]
            })
            route_curves[route_name] = curve
            denominators[route_name] = {
                key: curve[key]
                for key in ("assigned_opportunities", "eligible_opportunities", "attempted_attempts", "verified_useful_tasks")
            }
        comparisons = {}
        for curve_name in ("prepared_only", "adoption"):
            comparisons[curve_name] = {
                metric: _comparison(route_curves, case["horizon_n"], curve_name, metric)
                for metric in ("wall_ms", "human_ms")
            }
        cases[case_id] = {
            "horizon_n": case["horizon_n"],
            "denominators": denominators,
            "curves": route_curves,
            "comparisons": comparisons,
        }
    return {"cases": cases}


def run(fixture: dict[str, Any]) -> dict[str, Any]:
    events = build_events(fixture)
    return {
        "schema": "adoption-inclusive-verified-work-raw-v1",
        "allocation_id": fixture["allocation_id"],
        "events": events,
        "analysis": build_analysis(fixture, events),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("fixture")
    parser.add_argument("output")
    args = parser.parse_args()
    fixture = json.loads(Path(args.fixture).read_text(encoding="utf-8"))
    result = run(fixture)
    Path(args.output).write_text(json.dumps(result, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"allocation_id": result["allocation_id"], "event_rows": len(result["events"])}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
