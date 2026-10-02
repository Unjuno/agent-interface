"""Deterministic route-expansion fixture; emits a complete assignment/event ledger."""
import json
import sys
from collections import deque


def run(spec):
    result = {"schema": "backpressure-route-expansion-raw-v1", "allocation": spec["allocation"], "arms": {}}
    for arm in spec["arms"]:
        tasks = spec["tasks"]
        remaining_budget = spec["pressure_policy"]["optional_fast_verification_reservation_budget"]
        selected = []
        for task in tasks:
            if arm == "BASE_ONLY":
                route = "base"
            elif arm == "EXPANDED_GREEDY":
                route = "optional_fast"
            elif arm == "EXPANDED_PRESSURE" and remaining_budget >= spec["routes"]["optional_fast"]["verification_jobs"]:
                route = "optional_fast"
                remaining_budget -= spec["routes"][route]["verification_jobs"]
            else:
                route = "base"
            selected.append({"task_id": task["id"], "arrival": task["arrival"], "route": route,
                             "local_finish": task["arrival"] + spec["routes"][route]["local_ticks"],
                             "verification_jobs": spec["routes"][route]["verification_jobs"]})

        # Events are added to one FIFO queue at local completion, with stable task/job order.
        arrivals = {}
        for row in selected:
            for j in range(row["verification_jobs"]):
                arrivals.setdefault(row["local_finish"], []).append({"task_id": row["task_id"], "job_index": j})
        queue = deque()
        events = []
        finish_by_task = {}
        horizon = spec["horizon_inclusive"]
        for tick in range(horizon):
            for item in arrivals.get(tick, []):
                queue.append(item)
                events.append({"tick": tick, "event": "verification_enqueued", **item})
            if queue:
                item = queue.popleft()
                finish = tick + spec["normal_verifier"]["job_service_ticks"]
                events.append({"tick": tick, "event": "verification_started", **item})
                events.append({"tick": finish, "event": "verification_finished", **item})
                finish_by_task[item["task_id"]] = max(finish_by_task.get(item["task_id"], 0), finish)
        # Include jobs arriving after the horizon and all remaining queued jobs in the ledger.
        enqueued = sum(len(v) for v in arrivals.values())
        started = sum(e["event"] == "verification_started" for e in events)
        for tick, items in arrivals.items():
            if tick >= horizon:
                for item in items:
                    events.append({"tick": tick, "event": "verification_enqueued", **item})
        safety_events = []
        for item in spec["mandatory_safety_events"]:
            finish = item["arrival"] + spec["safety_verifier"]["service_ticks"]
            safety_events.append({"event_id": item["id"], "arrival": item["arrival"], "finish": finish,
                                  "served": finish - item["arrival"] <= spec["safety_verifier"]["deadline_ticks"]})
        completed = [task["id"] for task in tasks if finish_by_task.get(task["id"], horizon + 1) <= horizon]
        result["arms"][arm] = {
            "offered_task_ids": [t["id"] for t in tasks],
            "selected_routes": selected,
            "verification_events": events,
            "verification_jobs_enqueued": enqueued,
            "verification_jobs_started_by_horizon": started,
            "normal_jobs_pending_at_horizon": max(0, enqueued - started),
            "verified_task_ids_by_horizon": completed,
            "verified_by_horizon": len(completed),
            "local_ticks_total": sum(spec["routes"][r["route"]]["local_ticks"] for r in selected),
            "completed_task_latency": {tid: finish_by_task[tid] - next(t["arrival"] for t in tasks if t["id"] == tid) for tid in completed},
            "mandatory_safety_events": safety_events
        }
    return result


if __name__ == "__main__":
    with open(sys.argv[1], encoding="utf-8") as f:
        spec = json.load(f)
    print(json.dumps(run(spec), sort_keys=True, separators=(",", ":")))
