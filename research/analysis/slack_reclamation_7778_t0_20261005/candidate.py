"""Three finite scheduler policies. The slack guard sees released jobs only."""
import json
import os
from pathlib import Path

ROOT = Path(__file__).parent
OUT = Path(os.environ.get("OUTPUT_DIR", ROOT))
P = json.loads((ROOT / "protocol.json").read_text())


def edf_feasible(jobs, start, horizon):
    pending = {j["id"]: [j["release"], j["deadline"], j["execution"]]
               for j in jobs}
    for t in range(start, horizon):
        ready = [k for k, v in pending.items() if v[0] <= t and v[2] > 0]
        if ready:
            k = min(ready, key=lambda x: (pending[x][1], x))
            pending[k][2] -= 1
        if any(v[2] > 0 and v[1] <= t + 1 for v in pending.values()):
            return False
    return not any(v[2] > 0 for v in pending.values())


def future_release_patterns(first, gap, last_tick, remaining_count=None):
    out = [()]
    if remaining_count == 0:
        return out
    for release in range(first, last_tick + 1):
        next_count = None if remaining_count is None else remaining_count - 1
        tails = future_release_patterns(release + gap, gap, last_tick, next_count)
        out.extend((release,) + tail for tail in tails)
    return out


def can_steal(t, contract, horizon, last_release, observed_count):
    """Universal check over every allowed future release sequence."""
    if (not contract.get("preemptive") or
            not isinstance(contract.get("min_interarrival"), int) or
            not isinstance(contract.get("max_execution"), int) or
            not isinstance(contract.get("relative_deadline"), int)):
        return False
    gap = contract["min_interarrival"]
    wcet = contract["max_execution"]
    rel_deadline = contract["relative_deadline"]
    if gap < 1 or wcet < 1 or rel_deadline < wcet:
        return False
    first = max(t + 1, (last_release + gap) if last_release is not None else t + 1)
    last_release_tick = horizon - rel_deadline
    max_total = contract.get("max_jobs_total")
    remaining_count = None if max_total is None else max(0, max_total - observed_count)
    patterns = future_release_patterns(first, gap, last_release_tick, remaining_count)
    for pattern in patterns:
        future = [{"id": "f%d_%d" % (i, r), "release": r,
                   "deadline": r + rel_deadline, "execution": wcet}
                  for i, r in enumerate(pattern)]
        if not edf_feasible(future, t + 1, horizon):
            return False
    return True


def classify(trace):
    if any(j.get("class") not in ("control", "soft") for j in trace["jobs"]):
        return "HOLD_INVALID_JOB_CLASS"
    if any(j.get("execution") is None or not isinstance(j.get("execution"), int)
           or j["execution"] < 1 for j in trace["jobs"]):
        return "HOLD_MODEL_MISMATCH"
    if any(not j.get("preemptible", False) for j in trace["jobs"]):
        return "HOLD_MODEL_MISMATCH"
    if not trace["contract"].get("preemptive", False):
        return "HOLD_MODEL_MISMATCH"
    contract = trace["contract"]
    controls = sorted((j for j in trace["jobs"] if j["class"] == "control"),
                      key=lambda j: (j["release"], j["id"]))
    if any(j["execution"] > contract.get("max_execution", -1) or
           j["deadline"] != j["release"] + contract.get("relative_deadline", -1)
           for j in controls):
        return "HOLD_MODEL_MISMATCH"
    if any(b["release"] - a["release"] < contract.get("min_interarrival", 0)
           for a, b in zip(controls, controls[1:])):
        return "HOLD_MODEL_MISMATCH"
    if (contract.get("max_jobs_total") is not None and
            len(controls) > contract["max_jobs_total"]):
        return "HOLD_MODEL_MISMATCH"
    return None


def run_policy(trace, policy):
    horizon = trace["horizon"]
    jobs = trace["jobs"]
    status = classify(trace)
    if status:
        return {"trace_id": trace["trace_id"], "policy": policy,
                "status": status, "events": []}
    remaining = {j["id"]: j["execution"] for j in jobs}
    known_controls = []
    last_release = None
    observed_control_count = 0
    events = []
    status = "COMPLETE"
    for t in range(horizon):
        arrivals = [j for j in jobs if j["release"] == t]
        for j in arrivals:
            if j["class"] == "control":
                known_controls.append(dict(j))
                last_release = t
                observed_control_count += 1
        ready_c = [j for j in known_controls if remaining[j["id"]] > 0]
        ready_s = [j for j in jobs if j["class"] == "soft" and
                   j["release"] <= t and remaining[j["id"]] > 0]
        action = None
        reserved = t % P["reservation_period"] == 0
        if policy == "PRIORITY_ONLY":
            if ready_c:
                action = min(ready_c, key=lambda j: (j["deadline"], j["id"]))
            elif ready_s:
                action = min(ready_s, key=lambda j: (j["deadline"], j["id"]))
        elif policy == "STATIC_RESERVATION":
            if reserved and ready_c:
                action = min(ready_c, key=lambda j: (j["deadline"], j["id"]))
            elif not reserved and ready_s:
                action = min(ready_s, key=lambda j: (j["deadline"], j["id"]))
        elif policy == "DEMAND_GUARDED_SLACK_STEAL":
            if ready_c:
                action = min(ready_c, key=lambda j: (j["deadline"], j["id"]))
            elif ready_s and can_steal(t, trace["contract"], horizon,
                                       last_release, observed_control_count):
                action = min(ready_s, key=lambda j: (j["deadline"], j["id"]))
        else:
            raise ValueError("unknown policy")
        if action is not None:
            remaining[action["id"]] -= 1
        events.append({"tick": t, "arrivals": [j["id"] for j in arrivals],
                       "action": action["id"] if action else None,
                       "reserved": reserved})
        if any(remaining[j["id"]] > 0 and j["deadline"] <= t + 1
               for j in known_controls):
            status = "UNKNOWN_OVERLOAD"
            break
    return {"trace_id": trace["trace_id"], "policy": policy,
            "status": status, "events": events,
            "remaining": remaining,
            "control_completed": all(remaining[j["id"]] == 0
                                     for j in jobs if j["class"] == "control"),
            "soft_service": sum(j["execution"] - remaining[j["id"]]
                                for j in jobs if j["class"] == "soft")}


def main():
    data = json.loads((OUT / "inputs.json").read_text())
    rows = [run_policy(trace, policy)
            for trace in data["traces"]
            for policy in P["policies"]]
    (OUT / "candidate.json").write_text(
        json.dumps({"allocation": P["allocation"], "rows": rows},
                   sort_keys=True, separators=(",", ":")) + "\n",
        encoding="utf-8")


if __name__ == "__main__":
    main()
