"""Independent event-ledger replay; deliberately does not import candidate.py."""
import json
import sys
from collections import deque


def expected_arm(spec, arm):
    routes = spec["routes"]
    tasks = spec["tasks"]
    budget = spec["pressure_policy"]["optional_fast_verification_reservation_budget"]
    assignments = []
    for t in tasks:
        if arm == "BASE_ONLY":
            r = "base"
        elif arm == "EXPANDED_GREEDY":
            r = min(routes, key=lambda key: (routes[key]["local_ticks"], key))
        elif arm == "EXPANDED_PRESSURE" and budget >= routes["optional_fast"]["verification_jobs"]:
            r = "optional_fast"
            budget -= routes[r]["verification_jobs"]
        else:
            r = "base"
        assignments.append({"task_id": t["id"], "arrival": t["arrival"], "route": r,
                            "local_finish": t["arrival"] + routes[r]["local_ticks"],
                            "verification_jobs": routes[r]["verification_jobs"]})
    releases = {}
    for a in assignments:
        for ordinal in range(a["verification_jobs"]):
            releases.setdefault(a["local_finish"], []).append((a["task_id"], ordinal))
    pending = deque()
    ev = []
    task_finish = {}
    enqueued = 0
    started = 0
    for now in range(spec["horizon_inclusive"]):
        for tid, ordinal in releases.get(now, []):
            pending.append((tid, ordinal))
            enqueued += 1
            ev.append({"tick": now, "event": "verification_enqueued", "task_id": tid, "job_index": ordinal})
        if pending:
            tid, ordinal = pending.popleft()
            end = now + spec["normal_verifier"]["job_service_ticks"]
            started += 1
            task_finish[tid] = max(task_finish.get(tid, 0), end)
            ev.extend([
                {"tick": now, "event": "verification_started", "task_id": tid, "job_index": ordinal},
                {"tick": end, "event": "verification_finished", "task_id": tid, "job_index": ordinal}
            ])
    for now, batch in releases.items():
        if now >= spec["horizon_inclusive"]:
            for tid, ordinal in batch:
                enqueued += 1
                ev.append({"tick": now, "event": "verification_enqueued", "task_id": tid, "job_index": ordinal})
    safe = [{"event_id": x["id"], "arrival": x["arrival"],
             "finish": x["arrival"] + spec["safety_verifier"]["service_ticks"],
             "served": spec["safety_verifier"]["service_ticks"] <= spec["safety_verifier"]["deadline_ticks"]}
            for x in spec["mandatory_safety_events"]]
    done = [x["id"] for x in tasks if task_finish.get(x["id"], spec["horizon_inclusive"] + 1) <= spec["horizon_inclusive"]]
    return {
        "offered_task_ids": [x["id"] for x in tasks], "selected_routes": assignments,
        "verification_events": ev,
        "verification_jobs_enqueued": enqueued, "verification_jobs_started_by_horizon": started,
        "normal_jobs_pending_at_horizon": max(0, enqueued - started),
        "verified_task_ids_by_horizon": done, "verified_by_horizon": len(done),
        "local_ticks_total": sum(routes[x["route"]]["local_ticks"] for x in assignments),
        "completed_task_latency": {tid: task_finish[tid] - next(x["arrival"] for x in tasks if x["id"] == tid) for tid in done}, "mandatory_safety_events": safe
    }


def audit(spec, raw):
    errors = []
    if raw.get("schema") != "backpressure-route-expansion-raw-v1": errors.append("raw schema mismatch")
    if raw.get("allocation") != spec.get("allocation"): errors.append("allocation mismatch")
    if set(raw.get("arms", {})) != set(spec["arms"]): errors.append("arm set mismatch")
    for arm in spec["arms"]:
        if raw.get("arms", {}).get(arm) != expected_arm(spec, arm): errors.append(f"independent replay mismatch:{arm}")
    arms = raw.get("arms", {})
    if set(arms) == set(spec["arms"]):
        base, greedy, pressure = (arms[k] for k in ("BASE_ONLY", "EXPANDED_GREEDY", "EXPANDED_PRESSURE"))
        if greedy["local_ticks_total"] >= base["local_ticks_total"]: errors.append("added route not locally cheaper")
        if greedy["verified_by_horizon"] >= base["verified_by_horizon"]: errors.append("planted aggregate completion inversion absent")
        if pressure["verified_by_horizon"] < base["verified_by_horizon"]: errors.append("pressure arm did not recover baseline horizon completions")
        for arm in spec["arms"]:
            a = arms[arm]
            if len(a["offered_task_ids"]) != len(spec["tasks"]): errors.append(f"denominator mismatch:{arm}")
            if any(not x["served"] or x["finish"] - x["arrival"] > spec["safety_verifier"]["deadline_ticks"] for x in a["mandatory_safety_events"]):
                errors.append(f"mandatory safety event missed:{arm}")
    return errors


def corruptions(raw):
    mutations = {}
    m = json.loads(json.dumps(raw)); m["arms"]["BASE_ONLY"]["offered_task_ids"].pop(); mutations["drop_offer"] = m
    m = json.loads(json.dumps(raw)); m["arms"]["EXPANDED_GREEDY"]["selected_routes"][0]["route"] = "base"; mutations["route_label"] = m
    m = json.loads(json.dumps(raw)); m["arms"]["EXPANDED_GREEDY"]["verification_jobs_enqueued"] -= 1; mutations["suppress_verifier_work"] = m
    m = json.loads(json.dumps(raw)); m["arms"]["BASE_ONLY"]["mandatory_safety_events"][0]["served"] = False; mutations["safety_miss"] = m
    m = json.loads(json.dumps(raw)); m["arms"]["EXPANDED_PRESSURE"]["verified_by_horizon"] += 1; mutations["forge_completion"] = m
    return mutations


if __name__ == "__main__":
    with open(sys.argv[1], encoding="utf-8") as f: spec = json.load(f)
    with open(sys.argv[2], encoding="utf-8") as f: raw = json.load(f)
    errors = audit(spec, raw)
    rejected = {name: bool(audit(spec, mutated)) for name, mutated in corruptions(raw).items()}
    result = {"disposition": "PASS_METHOD_SCOPED" if not errors and all(rejected.values()) else "FAIL_AUDIT",
              "errors": errors, "mutations_rejected": rejected,
              "arms": {k: {"local_ticks_total": v["local_ticks_total"],
                           "verification_jobs_enqueued": v["verification_jobs_enqueued"],
                           "verified_by_horizon": v["verified_by_horizon"],
                           "pending_at_horizon": v["normal_jobs_pending_at_horizon"]}
                       for k, v in raw["arms"].items()}}
    print(json.dumps(result, sort_keys=True, separators=(",", ":")))
    raise SystemExit(0 if result["disposition"] == "PASS_METHOD_SCOPED" else 1)
