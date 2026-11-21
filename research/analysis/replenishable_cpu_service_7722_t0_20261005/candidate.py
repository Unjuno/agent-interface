#!/usr/bin/env python3
"""Frozen deterministic one-tick scheduler candidate for Issue #7722 T0."""
import argparse, hashlib, json
from collections import deque
from pathlib import Path

POLICIES = ("shared_priority", "shared_backpressure", "reserved_server")

def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def run_case(cfg, case, policy):
    period = cfg["period_ticks"]
    horizon = cfg["horizon_ticks"]
    ctl_work = cfg["control_service_ticks"]
    be_work = cfg["best_effort_service_ticks"]
    jobs = {}
    arrivals = {}
    def add(job_id, kind, release, work, deadline=None):
        jobs[job_id] = {"job_id": job_id, "job_class": kind, "release_tick": release,
                        "required_ticks": work, "remaining_ticks": work, "deadline_tick": deadline,
                        "finish_tick": None, "status": "pending"}
        arrivals.setdefault(release, []).append(job_id)
    if case["kind"] in ("schedulable", "negative"):
        for epoch, offset in enumerate(case["control_offsets"]):
            add(f"{case['case_id']}-c{epoch}", "control", epoch * period + offset,
                ctl_work, epoch * period + offset + cfg["control_deadline_ticks"])
            for j in range(case["best_effort_jobs_per_period"]):
                add(f"{case['case_id']}-b{epoch}-{j}", "best_effort", epoch * period,
                    be_work)
    else:
        for j, at in enumerate(case["control_offsets"]):
            add(f"{case['case_id']}-c{j}", "control", at, ctl_work,
                at + cfg["control_deadline_ticks"])
        be_count = case["best_effort_jobs_per_period"]
        for j in range(be_count):
            add(f"{case['case_id']}-b0-{j}", "best_effort", 0, be_work)

    ready_ctl, ready_be = deque(), deque()
    used_global, used_ctl, used_be = deque(), deque(), deque()
    events, rejected_be = [], []
    arrival_ticks = sorted(arrivals)
    arrival_index = 0
    t = 0
    while t < horizon:
        for q in (used_global, used_ctl, used_be):
            while q and q[0] <= t - period:
                q.popleft()
        while arrival_index < len(arrival_ticks) and arrival_ticks[arrival_index] == t:
            for jid in arrivals[arrival_ticks[arrival_index]]:
                job = jobs[jid]
                if job["job_class"] == "control":
                    ready_ctl.append(jid)
                elif policy == "shared_backpressure" and len(ready_be) >= cfg["backpressure_queue_jobs"]:
                    rejected_be.append(jid)
                    job["status"] = "rejected_backpressure"
                else:
                    ready_be.append(jid)
            arrival_index += 1
        jid = ready_ctl[0] if ready_ctl else (ready_be[0] if ready_be else None)
        if jid is None:
            t = arrival_ticks[arrival_index] if arrival_index < len(arrival_ticks) else horizon
            continue
        job = jobs[jid]
        blocked = None
        if len(used_global) >= cfg["total_budget_ticks"]:
            blocked = used_global[0] + period
        channels = ["global"]
        if policy == "reserved_server":
            if job["job_class"] == "control":
                if len(used_ctl) >= cfg["control_budget_ticks"]:
                    due = used_ctl[0] + period
                    blocked = due if blocked is None else max(blocked, due)
                channels.append("control")
            else:
                if len(used_be) >= cfg["best_effort_budget_ticks"]:
                    due = used_be[0] + period
                    blocked = due if blocked is None else max(blocked, due)
                channels.append("best_effort")
        if blocked is not None:
            next_arrival = arrival_ticks[arrival_index] if arrival_index < len(arrival_ticks) else horizon
            t = min(blocked, next_arrival, horizon)
            continue
        events.append({"tick": t, "job_id": jid, "job_class": job["job_class"],
                       "service_ticks": 1, "channels": channels})
        used_global.append(t)
        if policy == "reserved_server":
            (used_ctl if job["job_class"] == "control" else used_be).append(t)
        job["remaining_ticks"] -= 1
        if job["remaining_ticks"] == 0:
            job["finish_tick"] = t + 1
            job["status"] = "completed"
            (ready_ctl if job["job_class"] == "control" else ready_be).popleft()
        t += 1

    for jid in rejected_be:
        jobs[jid]["finish_tick"] = None
    controls = [j for j in jobs.values() if j["job_class"] == "control"]
    misses = [j for j in controls if j["finish_tick"] is None or
              j["finish_tick"] > j["deadline_tick"]]
    disposition = "UNKNOWN_OVERLOAD" if misses and case["kind"] in ("overload", "boundary") else (
        "DEADLINE_MISS" if misses else "COMPLETED_WITHIN_DEADLINE")
    return {"case_id": case["case_id"], "kind": case["kind"], "policy": policy,
            "events": events, "jobs": sorted(({k: v for k, v in j.items() if k != "remaining_ticks"}
                for j in jobs.values()), key=lambda j: j["job_id"]),
            "rejected_best_effort": sorted(rejected_be), "disposition": disposition}

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cases", required=True)
    ap.add_argument("--freeze", required=True)
    args = ap.parse_args()
    cases_path, freeze_path = Path(args.cases), Path(args.freeze)
    cfg = json.loads(cases_path.read_text(encoding="utf-8-sig"))
    freeze = json.loads(freeze_path.read_text(encoding="utf-8-sig"))
    manifest = freeze["source_hashes"]
    protocol_path = Path(__file__).with_name("PROTOCOL.md")
    if (sha(cases_path) != manifest["cases_sha256"] or
        sha(Path(__file__)) != manifest["candidate_sha256"] or
        sha(protocol_path) != manifest["protocol_sha256"]):
        raise SystemExit("STOP_FROZEN_SOURCE_HASH_MISMATCH")
    runs = [run_case(cfg, case, policy) for case in cfg["cases"] for policy in POLICIES]
    raw = {"schema": "cpu-control-7722-raw-v1", "allocation_id": cfg["allocation_id"],
           "cases_sha256": sha(cases_path), "candidate_sha256": sha(Path(__file__)),
           "freeze_sha256": sha(freeze_path),
           "protocol_sha256": freeze["protocol_sha256"],
           "declared_budgets": {k: cfg[k] for k in ("period_ticks", "horizon_ticks", "total_budget_ticks",
              "control_budget_ticks", "best_effort_budget_ticks", "control_service_ticks",
              "best_effort_service_ticks", "control_deadline_ticks", "backpressure_queue_jobs")},
           "runs": runs}
    print(json.dumps(raw, sort_keys=True, separators=(",", ":")))

if __name__ == "__main__":
    main()
