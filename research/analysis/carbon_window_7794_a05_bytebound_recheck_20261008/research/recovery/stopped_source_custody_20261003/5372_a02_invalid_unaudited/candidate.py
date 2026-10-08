"""Finite open-loop queue stressor with retry admission and aging controls."""
import json
import sys


def run(spec):
    all_offers = []
    for tick in range(spec["offer_ticks"]):
        for rank, cls in enumerate(spec["offers_per_tick"]):
            all_offers.append({"task_id": f"{cls[0]}{tick:02d}", "class": cls,
                               "arrival": tick, "order": tick * 2 + rank})

    results = {"schema": "backpressure-priority-fairness-raw-v1",
               "allocation": spec["allocation"], "arms": {}}
    for arm in spec["arms"]:
        pressure = arm.startswith("PRESSURE_")
        priority = arm != "FIFO_OPEN"
        aging = arm == "PRESSURE_AGING"
        queue = []
        verified = {}
        retries = suppressed = started = canceled = 0
        max_backlog = 0
        events = []
        safety = []
        by_tick = {}
        for task in all_offers:
            by_tick.setdefault(task["arrival"], []).append(task)
        for tick in range(spec["horizon_ticks"]):
            for task in by_tick.get(tick, []):
                job = {"task_id": task["task_id"], "class": task["class"],
                       "kind": "primary", "enqueued": tick, "order": task["order"]}
                queue.append(job)
                events.append({"tick": tick, "event": "primary_enqueued", **job})
            for task in all_offers:
                if task["arrival"] + spec["retry_after_ticks"] != tick:
                    continue
                if task["task_id"] in verified:
                    continue
                if pressure and len(queue) >= spec["pressure_retry_queue_threshold"]:
                    suppressed += 1
                    events.append({"tick": tick, "event": "retry_suppressed",
                                   "task_id": task["task_id"], "class": task["class"],
                                   "queue_depth": len(queue)})
                else:
                    job = {"task_id": task["task_id"], "class": task["class"],
                           "kind": "retry", "enqueued": tick, "order": task["order"]}
                    queue.append(job)
                    retries += 1
                    events.append({"tick": tick, "event": "retry_enqueued", **job})

            max_backlog = max(max_backlog, len(queue))
            if queue:
                if not priority:
                    selected = min(queue, key=lambda j: (j["order"], j["kind"] != "primary"))
                elif aging:
                    aged_low = [j for j in queue if j["class"] == "LOW"
                                and tick - j["enqueued"] >= spec["fairness_age_ticks"]]
                    selected = min(aged_low, key=lambda j: (j["enqueued"], j["order"], j["kind"] != "primary")) if aged_low else min(queue, key=lambda j: (j["class"] != "HIGH", j["enqueued"], j["order"], j["kind"] != "primary"))
                else:
                    selected = min(queue, key=lambda j: (j["class"] != "HIGH", j["enqueued"], j["order"], j["kind"] != "primary"))
                queue.remove(selected)
                finish = tick + spec["normal_service_per_tick"]
                started += 1
                events.append({"tick": tick, "event": "job_started", **selected})
                events.append({"tick": finish, "event": "job_finished", **selected})
                if selected["task_id"] not in verified:
                    task = next(t for t in all_offers if t["task_id"] == selected["task_id"])
                    verified[selected["task_id"]] = {"finish": finish, "arrival": task["arrival"],
                                                       "class": task["class"], "kind": selected["kind"]}
                    duplicates = [j for j in queue if j["task_id"] == selected["task_id"]]
                    for duplicate in duplicates:
                        queue.remove(duplicate)
                        canceled += 1
                        events.append({"tick": tick, "event": "duplicate_canceled", **duplicate})
            for arrival in spec["safety_events"]:
                if arrival == tick:
                    finish = tick + spec["safety_service_ticks"]
                    safety.append({"arrival": tick, "finish": finish,
                                   "deadline_met": finish - tick <= spec["safety_deadline_ticks"]})
                    events.append({"tick": tick, "event": "mandatory_safety_served",
                                   "arrival": tick, "finish": finish})

        rows = []
        for task in all_offers:
            result = verified.get(task["task_id"])
            latency = result["finish"] - result["arrival"] if result else None
            rows.append({"task_id": task["task_id"], "class": task["class"],
                         "arrival": task["arrival"], "status": "VERIFIED" if result else "UNKNOWN",
                         "finish": result["finish"] if result else None, "latency": latency,
                         "fresh": bool(result and latency <= spec["freshness_deadline_ticks"])})
        results["arms"][arm] = {
            "offered": rows,
            "events": events,
            "safety": safety,
            "jobs_started": started,
            "retries_enqueued": retries,
            "retries_suppressed": suppressed,
            "duplicates_canceled": canceled,
            "max_backlog": max_backlog,
            "pending_at_horizon": len(queue),
            "verified": sum(r["status"] == "VERIFIED" for r in rows),
            "fresh": sum(r["fresh"] for r in rows),
            "stale": sum(r["status"] == "VERIFIED" and not r["fresh"] for r in rows),
            "unknown": sum(r["status"] == "UNKNOWN" for r in rows),
            "verified_by_class": {cls: sum(r["class"] == cls and r["status"] == "VERIFIED" for r in rows)
                                  for cls in ("HIGH", "LOW")},
        }
    return results


if __name__ == "__main__":
    with open(sys.argv[1], encoding="utf-8") as stream:
        spec = json.load(stream)
    print(json.dumps(run(spec), sort_keys=True, separators=(",", ":")))

