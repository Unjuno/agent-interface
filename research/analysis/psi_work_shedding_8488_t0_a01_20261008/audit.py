#!/usr/bin/env python3
"""Independent audit oracle. Deliberately imports no candidate code."""
import hashlib
import json
import sys
from pathlib import Path


def digest(x):
    return hashlib.sha256(json.dumps(x, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def oracle(trace, policy, c):
    n, cap = c["horizon_ticks"], c["worker_slots"]
    by_tick = [[] for _ in range(n)]
    state = {}
    for x in trace["arrivals"]:
        by_tick[x["tick"]].append(x)
        state[x["id"]] = dict(x, rem=x["service"], started=False, done=None, deferred=0)
    done, rows, transitions = set(), [], []
    shed, cool, above, below = False, 0, 0, 0
    for t in range(n):
        arrived = {x["id"] for group in by_tick[:t+1] for x in group}
        mand = [state[i] for i in arrived if state[i]["class"] in c["mandatory_classes"] and not state[i]["started"]]
        obligations = [state[i] for i in arrived if state[i]["class"] in c["mandatory_classes"] and i not in done]
        obs_index = max(0, t - trace["psi_delay_ticks"])
        psi = trace["memory_some_ms_in_1s"][obs_index]
        above = above + 1 if psi is not None and psi >= c["thresholds"]["psi_memory_some_enter_ms_in_1s"] else 0
        below = below + 1 if psi is not None and psi <= c["thresholds"]["psi_memory_some_exit_ms_in_1s"] else 0
        cool = max(cool - 1, 0)
        target, why = shed, None
        if policy == "queue_deadline" and len(mand) >= c["thresholds"]["queue_enter_waiting_mandatory"]:
            target, why = True, "queue"
        if policy == "free_memory" and trace["free_memory_mib"][t] <= c["thresholds"]["free_memory_enter_mib"]:
            target, why = True, "free_memory"
        if policy == "psi_memory":
            if not shed and above >= c["thresholds"]["psi_enter_consecutive_windows"]:
                target, why = True, "psi_memory"
            elif shed and cool == 0 and below >= c["thresholds"]["psi_exit_consecutive_windows"] and not obligations:
                target, why = False, "psi_recovered"
        if target != shed:
            transitions.append(dict(tick=t, **{"from": shed, "to": target}, reason=why))
            shed = target
            if shed and policy == "psi_memory":
                cool = c["thresholds"]["psi_cooldown_ticks"]
        real_pressure = trace["memory_stall_active"][t] or trace["nonmemory_stall_active"][t]
        slots = max(0, (1 if real_pressure else cap))
        active = [state[i] for i in arrived if state[i]["started"] and state[i]["rem"] > 0
                  and not (shed and state[i]["class"] in c["optional_classes"])]
        active.sort(key=lambda j: (j.get("deadline", n+1), j["id"]))
        for j in state.values():
            if j["id"] in arrived and j["rem"] > 0 and j["class"] in c["optional_classes"] and shed:
                j["deferred"] += 1
        for j in active:
            j["deferred"] += 1
        picked = active[:slots]
        free = slots - len(picked)
        waiting = [state[i] for i in arrived if i not in done and state[i]["rem"] > 0
                   and (not state[i]["started"] or state[i]["class"] in c["optional_classes"])]
        waiting.sort(key=lambda j: (j.get("deadline", n+1), j["id"]))
        for j in waiting:
            if free == 0:
                break
            if shed and j["class"] in c["optional_classes"]:
                j["deferred"] += 1
                continue
            j["started"] = True
            picked.append(j)
            free -= 1
        completed_now = []
        for j in picked[:slots]:
            j["rem"] -= 1
            if j["rem"] == 0:
                j["done"] = t+1
                done.add(j["id"])
                completed_now.append(j["id"])
        missed = sorted(j["id"] for j in state.values() if j.get("deadline") is not None and j["id"] in arrived and j["id"] not in done and t >= j["deadline"])
        rows.append({"tick": t, "psi_memory_some_ms": psi, "psi_observation": "KNOWN" if psi is not None else "UNKNOWN",
                     "memory_stall_active": trace["memory_stall_active"][t], "nonmemory_stall_active": trace["nonmemory_stall_active"][t],
                     "effective_slots": slots, "shed": shed, "mandatory_waiting": len(mand),
                     "running": sorted(j["id"] for j in picked[:slots] if j["rem"] > 0),
                     "completed_now": sorted(completed_now), "deadline_misses": missed})
    return {"policy": policy, "trace": trace["id"], "transitions": transitions,
            "deadline_misses": sorted({i for r in rows for i in r["deadline_misses"]}),
            "max_mandatory_age_ticks": max((j["done"]-j["tick"] for j in state.values() if j["class"] in c["mandatory_classes"] and j["done"] is not None), default=None),
            "deferred_ticks": {i: j["deferred"] for i,j in sorted(state.items()) if j["class"] in c["optional_classes"]},
            "jobs": {i: {"class": j["class"], "remaining": j["rem"], "completed_at": j["done"], "evidence_id": j["evidence_id"]} for i,j in sorted(state.items())},
            "release_outcomes": {i: ("RELEASED" if j["done"] is not None else "UNKNOWN") for i,j in state.items() if j["class"] == "mandatory_release"},
            "uncompleted_job_ids": sorted(i for i,j in state.items() if j["rem"] > 0),
            "retained_evidence_ids": sorted(set(trace["evidence_ids"]) | {j["evidence_id"] for j in state.values()}), "timeline": rows}


def reconstruct(inp):
    return {"schema": "psi-work-shedding-result-v1", "input_sha256": digest(inp),
            "rows": [oracle(tr, pol, inp) for tr in inp["traces"] for pol in inp["policies"]]}


def main(inp_path, result_path):
    inp, result = json.loads(Path(inp_path).read_text()), json.loads(Path(result_path).read_text())
    expected = reconstruct(inp)
    if result != expected:
        raise SystemExit("FAIL: candidate output differs from independent reconstruction")
    print(json.dumps({"audit": "PASS", "rows": len(expected["rows"]), "input_sha256": expected["input_sha256"]}))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
