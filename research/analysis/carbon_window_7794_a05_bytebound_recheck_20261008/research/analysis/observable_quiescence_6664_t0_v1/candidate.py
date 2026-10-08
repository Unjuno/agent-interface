"""Candidate policy implementations; outputs preserve the input event ledger."""

from __future__ import annotations

import json
import sys

import scenarios


SNAPSHOTS = ("boundary", "grace_deadline", "horizon")


def _time(case: dict, label: str) -> int:
    boundary = next(e["t"] for e in case["events"] if e["kind"] == "TAKEOVER")
    if label == "boundary":
        return boundary
    if label == "grace_deadline":
        return boundary + 1
    return max(e["t"] for e in case["events"])


def _accounted(case: dict, snapshot: int) -> tuple[str, list[str]]:
    events = [e for e in case["events"] if e["t"] <= snapshot]
    takeover = next(e for e in events if e["kind"] == "TAKEOVER")
    boundary_key = (takeover["t"], takeover["seq"])
    reasons: list[str] = []
    accepted: dict[str, list[dict]] = {}
    for event in events:
        if event["kind"] == "ADMISSION":
            if event.get("epoch") == 1 and (event["t"], event["seq"]) > boundary_key:
                if event.get("decision") != "REJECTED_STALE":
                    reasons.append("old_epoch_admission_not_rejected")
            if event.get("decision") == "ACCEPTED":
                accepted.setdefault(event["op_id"], []).append(event)
    for op_id, admissions in accepted.items():
        if len(admissions) != 1:
            reasons.append(f"duplicate_operation_id:{op_id}")
            continue
        op_events = [e for e in events if e.get("op_id") == op_id]
        restarts = [e for e in events if e["kind"] == "BACKEND_RESTART"]
        relevant_restart = [e for e in restarts
                            if (e["t"], e["seq"]) >
                            (admissions[0]["t"], admissions[0]["seq"])]
        terminal = None
        for event in op_events:
            if event["kind"] == "COMPLETE_ACK":
                effect = any(x["kind"] == "EFFECT"
                             and (x["t"], x["seq"]) < (event["t"], event["seq"])
                             and x.get("backend_gen") == event.get("backend_gen")
                             for x in op_events)
                if effect:
                    terminal = event
            elif event["kind"] == "CANCEL_ACK":
                prior = [x["kind"] for x in op_events
                         if (x["t"], x["seq"]) < (event["t"], event["seq"])]
                valid = ((event.get("outcome") == "CANCELLED_BEFORE_START"
                          and "START" not in prior and "EFFECT" not in prior)
                         or (event.get("outcome") == "CANCELLED_BEFORE_EFFECT"
                             and "EFFECT" not in prior))
                if valid:
                    terminal = event
            elif event["kind"] == "RECONCILIATION_ACK":
                if event.get("backend_gen") == max(
                    [e.get("backend_gen", 1) for e in events], default=1
                ):
                    terminal = event
        if terminal is None:
            reasons.append(f"operation_unresolved:{op_id}")
        elif relevant_restart and terminal["backend_gen"] != max(
                e.get("backend_gen", 1) for e in events):
            reasons.append(f"operation_not_reconciled_after_restart:{op_id}")

    downs = {(e.get("op_id"), e.get("input")) for e in events
             if e["kind"] == "INPUT_DOWN"}
    releases = {(e.get("op_id"), e.get("input")) for e in events
                if e["kind"] == "INPUT_RELEASE_ACK"}
    for down in downs - releases:
        reasons.append(f"input_release_unconfirmed:{down[0]}:{down[1]}")

    observations = [e for e in events if e["kind"] == "OBSERVATION"
                    and e.get("epoch") == 2
                    and e.get("freshness") == "FRESH"
                    and e["t"] > takeover["t"]]
    if not observations:
        reasons.append("fresh_post_boundary_observation_missing")
    else:
        obs = max(observations, key=lambda e: e["seq"])
        latest_prior = max((e["seq"] for e in events
                            if e["seq"] < obs["seq"]
                            and e["kind"] != "OBSERVATION"), default=0)
        if obs.get("covers_through_seq", -1) < latest_prior:
            reasons.append("observation_does_not_cover_prior_state")
    return ("QUIESCENT" if not reasons else "UNKNOWN", sorted(set(reasons)))


def run() -> dict:
    rows = []
    for case in scenarios.build_scenarios():
        decisions = []
        for label in SNAPSHOTS:
            snapshot = _time(case, label)
            accounted_status, reasons = _accounted(case, snapshot)
            boundary = next(e["t"] for e in case["events"]
                            if e["kind"] == "TAKEOVER")
            decisions.extend([
                {"policy": "EPOCH_ONLY", "snapshot": label, "t": snapshot,
                 "status": "QUIESCENT" if snapshot >= boundary else "UNKNOWN",
                 "reasons": [] if snapshot >= boundary else ["before_boundary"]},
                {"policy": "TIME_DELAY", "snapshot": label, "t": snapshot,
                 "status": "QUIESCENT" if snapshot >= boundary + 1 else "UNKNOWN",
                 "reasons": [] if snapshot >= boundary + 1 else ["grace_not_elapsed"]},
                {"policy": "ACCOUNTED_QUIESCENCE", "snapshot": label,
                 "t": snapshot, "status": accounted_status, "reasons": reasons},
            ])
        rows.append({"case_id": case["case_id"], "events": case["events"],
                     "decisions": decisions})
    return {"schema": "observable-quiescence-raw-v1", "rows": rows}


if __name__ == "__main__":
    json.dump(run(), sys.stdout, sort_keys=True, separators=(",", ":"))
    sys.stdout.write("\n")
