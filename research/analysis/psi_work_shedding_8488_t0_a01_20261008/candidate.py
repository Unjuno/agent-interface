#!/usr/bin/env python3
"""Finite deterministic event simulator for Issue #8488 T0."""
import hashlib
import json
import sys
from pathlib import Path


def canonical_hash(value):
    raw = json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(raw).hexdigest()


def simulate(trace, policy, cfg):
    horizon = cfg["horizon_ticks"]
    cap = cfg["worker_slots"]
    arrivals = {t: [] for t in range(horizon)}
    jobs = {}
    for item in trace["arrivals"]:
        arrivals[item["tick"]].append(item)
        jobs[item["id"]] = {**item, "remaining": item["service"], "started": False,
                             "completed_at": None, "deferred_ticks": 0}
    shed = False
    cooldown = 0
    enter_streak = exit_streak = 0
    transitions = []
    timeline = []
    completed = set()
    for tick in range(horizon):
        for item in arrivals[tick]:
            # The job is already registered; arrivals define eligibility below.
            pass
        arrived = {j["id"] for t in range(tick + 1) for j in arrivals[t]}
        waiting = [jobs[jid] for jid in arrived if jid not in completed and jobs[jid]["remaining"] > 0]
        mandatory_waiting = sum(j["class"] in cfg["mandatory_classes"] and not j["started"] for j in waiting)
        mandatory_obligations = sum(j["class"] in cfg["mandatory_classes"] for j in waiting)
        psi = trace["memory_some_ms_in_1s"][max(0, tick - trace["psi_delay_ticks"])]
        psi_ok = psi is not None
        enter = psi_ok and psi >= cfg["thresholds"]["psi_memory_some_enter_ms_in_1s"]
        exit_ok = psi_ok and psi <= cfg["thresholds"]["psi_memory_some_exit_ms_in_1s"]
        enter_streak = enter_streak + 1 if enter else 0
        exit_streak = exit_streak + 1 if exit_ok else 0
        if cooldown:
            cooldown -= 1
        next_shed = shed
        reason = None
        if policy == "queue_deadline" and mandatory_waiting >= cfg["thresholds"]["queue_enter_waiting_mandatory"]:
            next_shed, reason = True, "queue"
        elif policy == "free_memory" and trace["free_memory_mib"][tick] <= cfg["thresholds"]["free_memory_enter_mib"]:
            next_shed, reason = True, "free_memory"
        elif policy == "psi_memory":
            if not shed and enter_streak >= cfg["thresholds"]["psi_enter_consecutive_windows"]:
                next_shed, reason = True, "psi_memory"
            elif shed and not cooldown and exit_streak >= cfg["thresholds"]["psi_exit_consecutive_windows"]:
                if not cfg["thresholds"]["psi_exit_requires_no_mandatory_obligation"] or mandatory_obligations == 0:
                    next_shed, reason = False, "psi_recovered"
        if next_shed != shed:
            transitions.append({"tick": tick, "from": shed, "to": next_shed, "reason": reason})
            shed = next_shed
            if shed:
                cooldown = cfg["thresholds"]["psi_cooldown_ticks"] if policy == "psi_memory" else 0
        pressure_active = trace["memory_stall_active"][tick] or trace["nonmemory_stall_active"][tick]
        effective_cap = 1 if pressure_active else cap
        active = [j for j in jobs.values() if j["started"] and j["remaining"] > 0 and j["id"] in arrived
                  and not (shed and j["class"] in cfg["optional_classes"])]
        active.sort(key=lambda j: (j["deadline"] if "deadline" in j else horizon + 1, j["id"]))
        for j in jobs.values():
            if j["id"] in arrived and j["remaining"] > 0 and j["class"] in cfg["optional_classes"] and shed:
                j["deferred_ticks"] += 1
        for j in active:
            j["deferred_ticks"] += 1
        slots = max(0, effective_cap - len(active))
        eligible = [jobs[jid] for jid in arrived if jid not in completed and jobs[jid]["remaining"] > 0
                    and (not jobs[jid]["started"] or jobs[jid]["class"] in cfg["optional_classes"])]
        eligible.sort(key=lambda j: (j["deadline"] if "deadline" in j else horizon + 1, j["id"]))
        selected = active[:effective_cap]
        for j in eligible:
            if slots <= 0:
                break
            if shed and j["class"] in cfg["optional_classes"]:
                j["deferred_ticks"] += 1
                continue
            j["started"] = True
            selected.append(j)
            slots -= 1
        for j in selected[:effective_cap]:
            j["remaining"] -= 1
            if j["remaining"] == 0:
                j["completed_at"] = tick + 1
                completed.add(j["id"])
        deadline_misses = sorted(j["id"] for j in jobs.values()
                                 if "deadline" in j and j["id"] in arrived
                                 and j["id"] not in completed and tick >= j["deadline"])
        timeline.append({"tick": tick, "psi_memory_some_ms": psi, "psi_observation": "KNOWN" if psi_ok else "UNKNOWN",
                         "memory_stall_active": trace["memory_stall_active"][tick],
                         "nonmemory_stall_active": trace["nonmemory_stall_active"][tick],
                         "effective_slots": effective_cap, "shed": shed,
                         "mandatory_waiting": mandatory_waiting,
                         "running": sorted(j["id"] for j in selected[:effective_cap] if j["remaining"] > 0),
                         "completed_now": sorted(j["id"] for j in jobs.values() if j["completed_at"] == tick + 1),
                         "deadline_misses": deadline_misses})
    released = {jid: ("RELEASED" if j["completed_at"] is not None else "UNKNOWN")
                for jid, j in jobs.items() if j["class"] == "mandatory_release"}
    uncompleted = sorted(jid for jid in jobs if jobs[jid]["remaining"] > 0)
    return {"policy": policy, "trace": trace["id"], "transitions": transitions,
            "deadline_misses": sorted({x for row in timeline for x in row["deadline_misses"]}),
            "max_mandatory_age_ticks": max((j["completed_at"] - j["tick"] for j in jobs.values()
                                               if j["class"] in cfg["mandatory_classes"] and j["completed_at"] is not None), default=None),
            "deferred_ticks": {jid: j["deferred_ticks"] for jid, j in sorted(jobs.items())
                               if j["class"] in cfg["optional_classes"]},
            "jobs": {jid: {"class": j["class"], "remaining": j["remaining"],
                            "completed_at": j["completed_at"], "evidence_id": j["evidence_id"]}
                     for jid, j in sorted(jobs.items())},
            "release_outcomes": released, "uncompleted_job_ids": uncompleted,
            "retained_evidence_ids": sorted(set(trace["evidence_ids"]) | {j["evidence_id"] for j in jobs.values()}),
            "timeline": timeline}


def main(source, destination):
    cfg = json.loads(Path(source).read_text())
    rows = [simulate(trace, policy, cfg) for trace in cfg["traces"] for policy in cfg["policies"]]
    out = {"schema": "psi-work-shedding-result-v1", "input_sha256": canonical_hash(cfg), "rows": rows}
    Path(destination).write_text(json.dumps(out, indent=2, sort_keys=True) + "\n")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
