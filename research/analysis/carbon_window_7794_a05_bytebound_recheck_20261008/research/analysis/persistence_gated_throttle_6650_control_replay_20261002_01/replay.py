"""Independent finite-trace reconstruction for Issue #6650 T0.

This module intentionally does not import either predecessor implementation.
It reconstructs the schedule from the fixture as an event loop and produces
the expected observable record for comparison with immutable predecessor RAW.
"""
from __future__ import annotations

from collections import deque
from copy import deepcopy


POLICIES = ("fixed", "queue_length", "persistence", "oracle")


def _one_policy(trace: dict, params: dict, policy: str,
                oracle_stale: set[str] | None = None) -> dict:
    stop_offering = trace["horizon"] + 1
    arrivals: dict[int, list[dict]] = {}
    for item in trace["events"]:
        arrivals.setdefault(item["t"], []).append(item)
    for batch in arrivals.values():
        batch.sort(key=lambda item: item["id"])

    invalidations: dict[int, list[dict]] = {}
    for change in trace["generation_changes"]:
        invalidations.setdefault(change["t"], []).append(change)

    backlog: deque[dict] = deque()
    active: list[dict] = []
    controller: dict[str, dict] = {}
    source_generation: dict[str, int] = {}
    ordinal: dict[str, int] = {}
    requests: list[dict] = []
    services: list[dict] = []
    observations: list[dict] = []
    transitions: list[dict] = []

    def state(session: str) -> dict:
        if session not in controller:
            controller[session] = {"tier": 0, "above_since": None, "below_since": None}
        return controller[session]

    def start_jobs(tick: int) -> None:
        while backlog and len(active) < trace["servers"]:
            item = backlog.popleft()
            session = item["session"]
            generation = source_generation.get(session, 0) if session is not None else 0
            if item["generation"] != generation:
                outcome = "STALE_GENERATION"
            elif item["deadline"] is not None and tick > item["deadline"]:
                outcome = "STALE_AT_SERVICE_START"
            else:
                outcome = "SERVICED_WITHIN_FRESHNESS"
            record = {
                "trace_id": trace["id"], "id": item["id"], "session": session,
                "kind": item["kind"], "started_at": tick,
                "completed_at": tick + item["service"],
                "queue_sojourn": tick - item["enqueued_at"], "outcome": outcome,
                "generation": item["generation"], "generation_at_start": generation,
                "deadline": item["deadline"], "enqueued_at": item["enqueued_at"],
                "optional_known": item["optional_known"],
            }
            active.append({"finish": tick + item["service"], "record": record})

    sessions = sorted({item["session"] for item in trace["events"]
                       if item["session"] is not None})
    final_tick = stop_offering + 99
    for tick in range(final_tick + 1):
        done = [job for job in active if job["finish"] <= tick]
        for job in done:
            active.remove(job)
            services.append(job["record"] | {"completed_at": job["finish"]})

        if tick < stop_offering:
            for change in invalidations.get(tick, []):
                source_generation[change["session"]] = change["generation"]

            for item in arrivals.get(tick, []):
                session = item["session"]
                optional = item["kind"] == "optional"
                eligible = item["optional_known"] is True and session is not None
                if session is not None:
                    state(session)
                tier = controller.get(session, {"tier": 0})["tier"] if session is not None else 0
                reason = "ACTIVE"
                suppress = False
                if optional and session is not None:
                    ordinal[session] = ordinal.get(session, 0) + 1
                if optional and not eligible:
                    reason = "UNKNOWN_SCOPE_OR_OPTIONALITY"
                elif optional and trace["feedback_delay"] > params["feedback_max_age"]:
                    reason = "UNKNOWN_FEEDBACK"
                elif optional and policy == "oracle" and item["id"] in (oracle_stale or set()):
                    suppress, reason = True, "ORACLE_DIAGNOSTIC_SUPPRESSION"
                elif optional and policy in ("persistence", "queue_length") and tier > 0:
                    period = params["suppression_period_by_tier"][str(tier)]
                    suppress = ordinal[session] % period != 0
                requests.append({
                    "trace_id": trace["id"], "id": item["id"], "session": session,
                    "kind": item["kind"], "optional_known": item["optional_known"],
                    "offered_at": tick, "offered": True,
                    "status": "SUPPRESSED" if suppress else "EMITTED",
                    "suppression_receipt": "OPTIONAL_PRODUCER_THROTTLE" if suppress else None,
                    "control_status": reason, "tier_at_offer": tier,
                    "generation": item["generation"], "deadline": item["deadline"],
                })
                if not suppress:
                    backlog.append(item | {"enqueued_at": tick})

            for session in sessions:
                ctl = state(session)
                eligible_pending = [item for item in backlog
                                    if item["session"] == session
                                    and item["kind"] == "optional"
                                    and item["optional_known"] is True]
                count = len(eligible_pending)
                oldest_age = (tick - min(item["enqueued_at"] for item in eligible_pending)
                              if eligible_pending else 0)
                valid_feedback = trace["feedback_delay"] <= params["feedback_max_age"]
                signal = (oldest_age >= params["age_target"] if policy == "persistence"
                          else count >= params["queue_threshold"])
                prior_tier = ctl["tier"]
                if policy in ("persistence", "queue_length") and valid_feedback:
                    if signal:
                        ctl["below_since"] = None
                        if ctl["above_since"] is None:
                            ctl["above_since"] = tick
                        if (ctl["tier"] < params["max_tier"]
                                and tick - ctl["above_since"] >= params["persistence_ticks"]):
                            ctl["tier"] += 1
                            ctl["above_since"] = tick
                    else:
                        ctl["above_since"] = None
                        if ctl["tier"] > 0:
                            if ctl["below_since"] is None:
                                ctl["below_since"] = tick
                            if tick - ctl["below_since"] >= params["recovery_ticks"]:
                                ctl["tier"] -= 1
                                ctl["below_since"] = tick
                if ctl["tier"] != prior_tier:
                    transitions.append({"session": session, "at": tick,
                                       "from": prior_tier, "to": ctl["tier"]})
                observations.append({
                    "at": tick, "session": session, "eligible_pending": count,
                    "oldest_pending_age": oldest_age,
                    "completed_sojourn_samples": sum(
                        1 for row in services if row["session"] == session
                        and row["kind"] == "optional" and row["optional_known"]),
                    "feedback_valid": valid_feedback,
                    "signal": signal if valid_feedback else None,
                    "tier": ctl["tier"],
                    "control_status": "ACTIVE" if valid_feedback else "UNKNOWN_FEEDBACK",
                })

            if tick >= trace["blackout_until"]:
                start_jobs(tick)
        else:
            if not backlog and not active:
                break
            if tick >= trace["blackout_until"]:
                start_jobs(tick)
        if tick >= final_tick and (backlog or active):
            break

    mandatory_ids = {item["id"] for item in trace["events"]
                     if item["kind"] == "mandatory"}
    mandatory_outcomes = {row["id"]: row["outcome"] for row in services
                          if row["kind"] == "mandatory"}
    return {
        "requests": requests, "services": services, "states": observations,
        "transitions": transitions,
        "summary": {
            "offered": len(trace["events"]),
            "suppressed_optional": sum(row["status"] == "SUPPRESSED"
                                       and row["kind"] == "optional" for row in requests),
            "suppressed_mandatory": sum(row["status"] == "SUPPRESSED"
                                        and row["kind"] == "mandatory" for row in requests),
            "coverage_gaps": sum(row["suppression_receipt"] is not None for row in requests),
            "stale_optional_delivered": sum(row["kind"] == "optional"
                                            and row["outcome"] != "SERVICED_WITHIN_FRESHNESS"
                                            for row in services),
            "mandatory_offered": len(mandatory_ids),
            "mandatory_serviced": len(mandatory_outcomes),
            "mandatory_ids": sorted(mandatory_outcomes),
            "max_mandatory_lost": len(mandatory_ids - set(mandatory_outcomes)),
            "tier_transitions": len(transitions),
            "completed_optional_sojourn_samples": sum(
                row["kind"] == "optional" for row in services),
        },
    }


def reconstruct(fixture: dict) -> dict:
    """Recreate the four policy outcomes without using predecessor code/raw."""
    all_traces: dict[str, dict] = {}
    params = fixture["parameters"]
    for trace in fixture["traces"]:
        fixed = _one_policy(trace, params, "fixed")
        stale_under_fixed = {row["id"] for row in fixed["services"]
                             if row["kind"] == "optional"
                             and row["outcome"] != "SERVICED_WITHIN_FRESHNESS"}
        all_traces[trace["id"]] = {
            "fixed": fixed,
            "queue_length": _one_policy(trace, params, "queue_length"),
            "persistence": _one_policy(trace, params, "persistence"),
            "oracle": _one_policy(trace, params, "oracle", stale_under_fixed),
        }
    return {"allocation": fixture["allocation"], "parameters": params,
            "traces": all_traces}


def differences(expected: dict, observed: dict) -> list[str]:
    """Return exact structural paths that differ, including omitted/extra rows."""
    found: list[str] = []

    def visit(left, right, path: str) -> None:
        if type(left) is not type(right):
            found.append(path or "/")
        elif isinstance(left, dict):
            if left.keys() != right.keys():
                found.append(path + "/@keys")
            for key in sorted(left.keys() | right.keys()):
                if key in left and key in right:
                    visit(left[key], right[key], f"{path}/{key}")
                else:
                    found.append(f"{path}/{key}")
        elif isinstance(left, list):
            if len(left) != len(right):
                found.append(path + "/@length")
            for index, (a, b) in enumerate(zip(left, right)):
                visit(a, b, f"{path}/{index}")
        elif left != right:
            found.append(path or "/")

    visit(expected, observed, "")
    return found
