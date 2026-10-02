"""Finite producer-throttle simulator; optional generation only may be suppressed."""
from __future__ import annotations

import json
import sys
from collections import deque
from pathlib import Path


def simulate(trace: dict, params: dict, policy: str, oracle_stale: set[str] | None = None) -> dict:
    offers = {t: [] for t in range(trace["horizon"] + 1)}
    for event in trace["events"]:
        offers[event["t"]].append(event)
    for group in offers.values():
        group.sort(key=lambda x: x["id"])
    changes = {x["t"]: [] for x in trace["generation_changes"]}
    for change in trace["generation_changes"]:
        changes[change["t"]].append(change)

    pending: deque[dict] = deque()
    running: list[dict] = []
    states: dict[str, dict] = {}
    current_generation: dict[str, int] = {}
    ordinal: dict[str, int] = {}
    requests, services, state_rows, transitions = [], [], [], []

    def state_for(session: str) -> dict:
        return states.setdefault(session, {"tier": 0, "above_since": None, "below_since": None})

    stop = trace["horizon"] + 1
    for now in range(stop + 100):
        # Complete jobs first; sojourn is measured exactly to service start.
        finished = [j for j in running if j["finish"] <= now]
        for job in finished:
            running.remove(job)
            services.append(job["service_row"] | {"completed_at": job["finish"]})

        if now < stop:
            for change in changes.get(now, []):
                current_generation[change["session"]] = change["generation"]
            for event in offers.get(now, []):
                sid = event["session"]
                optional = event["kind"] == "optional"
                known = event["optional_known"] is True and sid is not None
                if sid is not None:
                    state_for(sid)
                control_status = "ACTIVE"
                tier = states.get(sid, {"tier": 0})["tier"] if sid is not None else 0
                suppress = False
                if optional and sid is not None:
                    ordinal[sid] = ordinal.get(sid, 0) + 1
                if optional and not known:
                    control_status = "UNKNOWN_SCOPE_OR_OPTIONALITY"
                elif optional and now - (now - trace["feedback_delay"]) > params["feedback_max_age"]:
                    control_status = "UNKNOWN_FEEDBACK"
                elif optional and policy == "oracle" and event["id"] in (oracle_stale or set()):
                    suppress = True
                    control_status = "ORACLE_DIAGNOSTIC_SUPPRESSION"
                elif optional and policy in ("persistence", "queue_length") and tier > 0:
                    period = params["suppression_period_by_tier"][str(tier)]
                    suppress = ordinal[sid] % period != 0
                requests.append({"trace_id": trace["id"], "id": event["id"], "session": sid,
                    "kind": event["kind"], "optional_known": event["optional_known"],
                    "offered_at": now, "offered": True, "status": "SUPPRESSED" if suppress else "EMITTED",
                    "suppression_receipt": "OPTIONAL_PRODUCER_THROTTLE" if suppress else None,
                    "control_status": control_status, "tier_at_offer": tier,
                    "generation": event["generation"], "deadline": event["deadline"]})
                if not suppress:
                    pending.append(event | {"enqueued_at": now})

            sessions = sorted({e["session"] for e in trace["events"] if e["session"] is not None})
            for sid in sessions:
                s = state_for(sid)
                sample_valid = trace["feedback_delay"] <= params["feedback_max_age"]
                elig = [e for e in pending if e["session"] == sid and e["kind"] == "optional"
                        and e["optional_known"] is True]
                oldest = now - min((e["enqueued_at"] for e in elig), default=now)
                qlen = len(elig)
                signal = (oldest >= params["age_target"] if policy == "persistence"
                          else qlen >= params["queue_threshold"])
                before = s["tier"]
                if policy in ("persistence", "queue_length") and sample_valid:
                    if signal:
                        s["below_since"] = None
                        if s["above_since"] is None:
                            s["above_since"] = now
                        if s["tier"] < params["max_tier"] and now - s["above_since"] >= params["persistence_ticks"]:
                            s["tier"] += 1
                            s["above_since"] = now
                    else:
                        s["above_since"] = None
                        if s["tier"] > 0:
                            if s["below_since"] is None:
                                s["below_since"] = now
                            if now - s["below_since"] >= params["recovery_ticks"]:
                                s["tier"] -= 1
                                s["below_since"] = now
                if s["tier"] != before:
                    transitions.append({"session": sid, "at": now, "from": before, "to": s["tier"]})
                state_rows.append({"at": now, "session": sid, "eligible_pending": qlen,
                    "oldest_pending_age": oldest, "completed_sojourn_samples": sum(
                        1 for x in services if x["session"] == sid and x["kind"] == "optional"
                        and x["optional_known"]), "feedback_valid": sample_valid,
                    "signal": signal if sample_valid else None, "tier": s["tier"],
                    "control_status": "ACTIVE" if sample_valid else "UNKNOWN_FEEDBACK"})

            if now >= trace["blackout_until"]:
                while pending and len(running) < trace["servers"]:
                    event = pending.popleft()
                    sid = event["session"]
                    gen_now = current_generation.get(sid, 0) if sid is not None else 0
                    if event["generation"] != gen_now:
                        outcome = "STALE_GENERATION"
                    elif event["deadline"] is not None and now > event["deadline"]:
                        outcome = "STALE_AT_SERVICE_START"
                    else:
                        outcome = "SERVICED_WITHIN_FRESHNESS"
                    service_row = {"trace_id": trace["id"], "id": event["id"], "session": sid,
                        "kind": event["kind"], "started_at": now,
                        "completed_at": now + event["service"],
                        "queue_sojourn": now - event["enqueued_at"],
                        "outcome": outcome, "generation": event["generation"],
                        "generation_at_start": gen_now, "deadline": event["deadline"],
                        "enqueued_at": event["enqueued_at"], "optional_known": event["optional_known"]}
                    running.append({"finish": now + event["service"], "service_row": service_row})
        else:
            # Drain after the frozen offer horizon; no new observations are generated.
            if not pending and not running:
                break
            if now >= trace["blackout_until"]:
                while pending and len(running) < trace["servers"]:
                    event = pending.popleft()
                    sid = event["session"]
                    gen_now = current_generation.get(sid, 0) if sid is not None else 0
                    if event["generation"] != gen_now:
                        outcome = "STALE_GENERATION"
                    elif event["deadline"] is not None and now > event["deadline"]:
                        outcome = "STALE_AT_SERVICE_START"
                    else:
                        outcome = "SERVICED_WITHIN_FRESHNESS"
                    service_row = {"trace_id": trace["id"], "id": event["id"], "session": sid,
                        "kind": event["kind"], "started_at": now,
                        "completed_at": now + event["service"],
                        "queue_sojourn": now - event["enqueued_at"],
                        "outcome": outcome, "generation": event["generation"],
                        "generation_at_start": gen_now, "deadline": event["deadline"],
                        "enqueued_at": event["enqueued_at"], "optional_known": event["optional_known"]}
                    running.append({"finish": now + event["service"], "service_row": service_row})
        if now >= stop + 99 and (pending or running):
            break

    mandatory_offered = {e["id"] for e in trace["events"] if e["kind"] == "mandatory"}
    mandatory_results = {x["id"]: x["outcome"] for x in services if x["kind"] == "mandatory"}
    return {"requests": requests, "services": services, "states": state_rows,
        "transitions": transitions,
        "summary": {"offered": len(trace["events"]),
            "suppressed_optional": sum(r["status"] == "SUPPRESSED" and r["kind"] == "optional" for r in requests),
            "suppressed_mandatory": sum(r["status"] == "SUPPRESSED" and r["kind"] == "mandatory" for r in requests),
            "coverage_gaps": sum(r["suppression_receipt"] is not None for r in requests),
            "stale_optional_delivered": sum(x["kind"] == "optional" and x["outcome"] != "SERVICED_WITHIN_FRESHNESS" for x in services),
            "mandatory_offered": len(mandatory_offered), "mandatory_serviced": len(mandatory_results),
            "mandatory_ids": sorted(mandatory_results), "max_mandatory_lost": len(mandatory_offered - set(mandatory_results)),
            "tier_transitions": len(transitions),
            "completed_optional_sojourn_samples": sum(x["kind"] == "optional" for x in services)}}


def run(fixture: dict) -> dict:
    traces_out = {}
    p = fixture["parameters"]
    for trace in fixture["traces"]:
        fixed = simulate(trace, p, "fixed")
        baseline_stale = {x["id"] for x in fixed["services"] if x["kind"] == "optional"
                          and x["outcome"] != "SERVICED_WITHIN_FRESHNESS"}
        traces_out[trace["id"]] = {"fixed": fixed,
            "queue_length": simulate(trace, p, "queue_length"),
            "persistence": simulate(trace, p, "persistence"),
            "oracle": simulate(trace, p, "oracle", baseline_stale)}
    return {"allocation": fixture["allocation"], "parameters": p, "traces": traces_out}


def main() -> None:
    fixture = json.loads(Path(sys.argv[1]).read_text())
    raw = run(fixture)
    Path(sys.argv[2]).write_text(json.dumps(raw, sort_keys=True, separators=(",", ":")) + "\n")
    print(json.dumps({"allocation": raw["allocation"], "traces": len(raw["traces"]),
        "offered_ids": sum(len(x["events"]) for x in fixture["traces"])}, sort_keys=True))


if __name__ == "__main__":
    main()
