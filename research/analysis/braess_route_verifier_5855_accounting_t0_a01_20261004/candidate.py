"""Frozen synthetic accounting-control traces for Issue #5855 A01."""
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent
OUT = ROOT / "candidate-output.json"
HORIZON_CENSOR = 10


def trace(name, arrivals, services, horizon, *, retry_duplicate=False, window_kind="finite"):
    events = []
    free_at = 0
    for task_id, (arrival, service) in enumerate(zip(arrivals, services)):
        events.append({"tick": arrival, "kind": "offer", "task_id": f"t{task_id}",
                       "event_id": f"{name}-offer-{task_id}"})
        start = max(arrival, free_at)
        done = start + service
        free_at = done
        if start <= horizon:
            events.append({"tick": start, "kind": "start", "task_id": f"t{task_id}",
                           "attempt_id": 1, "event_id": f"{name}-start-{task_id}-1"})
        if done <= horizon:
            events.append({"tick": done, "kind": "verified", "task_id": f"t{task_id}",
                           "attempt_id": 1, "receipt_id": f"{name}-receipt-{task_id}",
                           "event_id": f"{name}-verified-{task_id}"})
    events.append({"tick": horizon, "kind": "horizon", "event_id": f"{name}-horizon"})
    if retry_duplicate:
        events = [
            {"tick": 0, "kind": "offer", "task_id": "t0", "event_id": "retry-offer"},
            {"tick": 0, "kind": "start", "task_id": "t0", "attempt_id": 1, "event_id": "retry-start-1"},
            {"tick": 1, "kind": "attempt_failed", "task_id": "t0", "attempt_id": 1,
             "receipt_id": "retry-failure-1", "event_id": "retry-failure-event"},
            {"tick": 1, "kind": "start", "task_id": "t0", "attempt_id": 2, "event_id": "retry-start-2"},
            {"tick": 2, "kind": "verified", "task_id": "t0", "attempt_id": 2,
             "receipt_id": "retry-terminal-1", "event_id": "retry-terminal-event-1"},
            {"tick": 2, "kind": "verified", "task_id": "t0", "attempt_id": 2,
             "receipt_id": "retry-terminal-1", "event_id": "retry-terminal-event-duplicate"},
            {"tick": horizon, "kind": "horizon", "event_id": "retry-horizon"},
        ]
    priorities = {"verified": 0, "attempt_failed": 1, "offer": 2, "start": 3, "horizon": 9}
    events.sort(key=lambda e: (e["tick"], priorities[e["kind"]], e["event_id"]))
    return {"name": name, "horizon": horizon, "window_kind": window_kind,
            "initial_pending": 0, "events": events}


baseline = trace("matched-baseline", [0, 1, 2, 3], [2, 2, 2, 2], 10)
added = trace("matched-route-added", [0, 1, 2, 3], [1, 1, 10, 10], 10)
duplicate = trace("duplicate-retry-receipt", [0], [2], 3, retry_duplicate=True)
transient = trace("transient-startup", [0, 1, 2], [2, 2, 2], 3, window_kind="transient")
stable = trace("stable-periodic-control", [0, 2, 4], [1, 1, 1], 6, window_kind="stable_fixture")


def complete_only_mean(t):
    offers = {e["task_id"]: e["tick"] for e in t["events"] if e["kind"] == "offer"}
    terminal = {e["task_id"]: e["tick"] for e in t["events"] if e["kind"] == "verified"}
    return sum(terminal[k] - offers[k] for k in terminal) / len(terminal) if terminal else None


result = {
    "schema": "braess-queue-conservation-a01-v1",
    "allocation": "BRAESS-QUEUE-ACCOUNTING-5855-T0-20261004-A01",
    "source_main": "9dc383a89043deb6199c847196498d867ba6bb75",
    "matched_pair_same_offers": True,
    "traces": [baseline, added, duplicate, transient, stable],
    "candidate_diagnostics": {
        "baseline_complete_only_mean": complete_only_mean(baseline),
        "route_added_complete_only_mean": complete_only_mean(added),
        "route_added_verified_count": sum(e["kind"] == "verified" for e in added["events"]),
        "route_added_offered_count": sum(e["kind"] == "offer" for e in added["events"]),
        "duplicate_terminal_receipt_rows": sum(e["kind"] == "verified" for e in duplicate["events"]),
    },
}
OUT.write_text(json.dumps(result, sort_keys=True, indent=2) + "\n", encoding="utf-8")
print(json.dumps({"trace_count": len(result["traces"]), "event_count": sum(len(t["events"]) for t in result["traces"]),
                  "output": OUT.name}, sort_keys=True))
