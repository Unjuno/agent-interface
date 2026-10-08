"""Independent simulator replay and corruption controls; does not import candidate."""
import copy
import json
import sys
from collections import deque


def replay(spec, arm):
    tasks = [{"task_id": f"{cls[0]}{tick:02d}", "class": cls,
              "arrival": tick, "order": tick * 2 + rank}
             for tick in range(spec["offer_ticks"])
             for rank, cls in enumerate(spec["offers_per_tick"])]
    queue = deque()
    verified = {}
    events, safety = [], []
    retries = suppressed = started = canceled = max_backlog = 0
    pressure, priority, aging = arm.startswith("PRESSURE_"), arm != "FIFO_OPEN", arm == "PRESSURE_AGING"
    for tick in range(spec["horizon_ticks"]):
        for t in tasks:
            if t["arrival"] == tick:
                j = (t["task_id"], t["class"], "primary", tick, t["order"])
                queue.append(j)
                events.append({"tick": tick, "event": "primary_enqueued", "task_id": j[0], "class": j[1], "kind": j[2], "enqueued": j[3], "order": j[4]})
        for t in tasks:
            if t["arrival"] + spec["retry_after_ticks"] != tick or t["task_id"] in verified:
                continue
            if pressure and len(queue) >= spec["pressure_retry_queue_threshold"]:
                suppressed += 1
                events.append({"tick": tick, "event": "retry_suppressed", "task_id": t["task_id"], "class": t["class"], "queue_depth": len(queue)})
            else:
                j = (t["task_id"], t["class"], "retry", tick, t["order"])
                queue.append(j)
                retries += 1
                events.append({"tick": tick, "event": "retry_enqueued", "task_id": j[0], "class": j[1], "kind": j[2], "enqueued": j[3], "order": j[4]})
        max_backlog = max(max_backlog, len(queue))
        if queue:
            jobs = list(queue)
            if not priority:
                j = min(jobs, key=lambda x: (x[4], x[2] != "primary"))
            elif aging:
                low = [x for x in jobs if x[1] == "LOW" and tick - x[3] >= spec["fairness_age_ticks"]]
                j = min(low, key=lambda x: (x[3], x[4], x[2] != "primary")) if low else min(jobs, key=lambda x: (x[1] != "HIGH", x[3], x[4], x[2] != "primary"))
            else:
                j = min(jobs, key=lambda x: (x[1] != "HIGH", x[3], x[4], x[2] != "primary"))
            queue.remove(j)
            finish = tick + spec["normal_service_per_tick"]
            started += 1
            def job_event(event, at):
                return {"tick": at, "event": event, "task_id": j[0], "class": j[1], "kind": j[2], "enqueued": j[3], "order": j[4]}
            events.extend([job_event("job_started", tick), job_event("job_finished", finish)])
            if j[0] not in verified:
                task = next(t for t in tasks if t["task_id"] == j[0])
                verified[j[0]] = {"finish": finish, "arrival": task["arrival"], "class": task["class"], "kind": j[2]}
                duplicate = [x for x in queue if x[0] == j[0]]
                for x in duplicate:
                    queue.remove(x)
                    canceled += 1
                    events.append({"tick": tick, "event": "duplicate_canceled", "task_id": x[0], "class": x[1], "kind": x[2], "enqueued": x[3], "order": x[4]})
        for arrival in spec["safety_events"]:
            if arrival == tick:
                finish = tick + spec["safety_service_ticks"]
                safety.append({"arrival": tick, "finish": finish, "deadline_met": finish - tick <= spec["safety_deadline_ticks"]})
                events.append({"tick": tick, "event": "mandatory_safety_served", "arrival": tick, "finish": finish})
    rows = []
    for t in tasks:
        r = verified.get(t["task_id"])
        latency = r["finish"] - r["arrival"] if r else None
        rows.append({"task_id": t["task_id"], "class": t["class"], "arrival": t["arrival"],
                     "status": "VERIFIED" if r else "UNKNOWN", "finish": r["finish"] if r else None,
                     "latency": latency, "fresh": bool(r and latency <= spec["freshness_deadline_ticks"])})
    return {"offered": rows, "events": events, "safety": safety, "jobs_started": started,
            "retries_enqueued": retries, "retries_suppressed": suppressed,
            "duplicates_canceled": canceled, "max_backlog": max_backlog, "pending_at_horizon": len(queue),
            "verified": sum(r["status"] == "VERIFIED" for r in rows),
            "fresh": sum(r["fresh"] for r in rows),
            "stale": sum(r["status"] == "VERIFIED" and not r["fresh"] for r in rows),
            "unknown": sum(r["status"] == "UNKNOWN" for r in rows),
            "verified_by_class": {cls: sum(r["class"] == cls and r["status"] == "VERIFIED" for r in rows) for cls in ("HIGH", "LOW")}}


def audit(spec, raw):
    errors = []
    if raw.get("schema") != "backpressure-priority-fairness-raw-v1": errors.append("schema")
    if raw.get("allocation") != spec.get("allocation"): errors.append("allocation")
    if set(raw.get("arms", {})) != set(spec["arms"]): errors.append("arm set")
    for arm in spec["arms"]:
        if raw.get("arms", {}).get(arm) != replay(spec, arm): errors.append("ledger mismatch:" + arm)
    return errors


def corruptions(raw):
    cases = {}
    m = copy.deepcopy(raw); m["arms"]["PRIORITY_ONLY"]["offered"].pop(); cases["drop_offer"] = m
    m = copy.deepcopy(raw); m["arms"]["PRESSURE_PRIORITY"]["retries_suppressed"] += 1; cases["forge_suppression"] = m
    m = copy.deepcopy(raw); m["arms"]["PRESSURE_AGING"]["safety"][0]["deadline_met"] = False; cases["safety_miss"] = m
    m = copy.deepcopy(raw); m["arms"]["PRIORITY_ONLY"]["offered"][0]["fresh"] = not m["arms"]["PRIORITY_ONLY"]["offered"][0]["fresh"]; cases["freshness_label"] = m
    return cases


if __name__ == "__main__":
    with open(sys.argv[1], encoding="utf-8") as f: spec = json.load(f)
    with open(sys.argv[2], encoding="utf-8") as f: raw = json.load(f)
    errors = audit(spec, raw)
    rejected = {name: bool(audit(spec, mutated)) for name, mutated in corruptions(raw).items()}
    summary = {arm: {k: v[k] for k in ("verified", "fresh", "stale", "unknown", "retries_enqueued", "retries_suppressed", "max_backlog", "pending_at_horizon", "verified_by_class")}
               for arm, v in raw.get("arms", {}).items()}
    result = {"disposition": "PASS_METHOD_SCOPED" if not errors and all(rejected.values()) else "FAIL_AUDIT",
              "errors": errors, "mutations_rejected": rejected, "summary": summary}
    print(json.dumps(result, sort_keys=True, separators=(",", ":")))
    raise SystemExit(0 if result["disposition"] == "PASS_METHOD_SCOPED" else 1)

