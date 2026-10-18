"""Finite synthetic scheduler candidate for Issue #7778; no host scheduling."""
import argparse
import itertools
import json
from pathlib import Path

POLICIES = ("PRIORITY_ONLY", "STATIC_RESERVATION", "DEMAND_GUARDED_SLACK_STEAL")
PERIOD = 8
CONTROL_BUDGET = 2
SOFT_BUDGET = 6


def refusal_status(job):
    if job.get("class") not in {"control", "best_effort"}:
        return "REJECT_INVALID_JOB_CLASS"
    if job.get("wcet") is None:
        return "HOLD_UNKNOWN_WCET"
    if job.get("preemptible") is not True:
        return "UNKNOWN_MODEL_MISMATCH"
    if type(job.get("wcet")) is not int or job["wcet"] <= 0:
        return "HOLD_INVALID_WCET"
    return "ELIGIBLE"


def _edf_feasible(jobs, start, horizon):
    pending = {job["id"]: job["remaining"] for job in jobs}
    by_id = {job["id"]: job for job in jobs}
    for tick in range(start, horizon):
        if any(pending[j["id"]] and j["deadline"] <= tick for j in jobs):
            return False
        ready = [j for j in jobs if j["release"] <= tick and pending[j["id"]] > 0]
        if ready:
            chosen = min(ready, key=lambda j: (j["deadline"], j["id"]))
            pending[chosen["id"]] -= 1
        if any(pending[j["id"]] and j["deadline"] <= tick + 1 for j in jobs):
            return False
    return not any(pending.values())


def _future_assignments(case, now, release_history, overhead):
    controls = case["controls"]
    last = {}
    for job in release_history:
        last[job["stream"]] = max(last.get(job["stream"], -1), job["actual_release"])
    pending = [
        job for job in controls
        if job["id"] not in {x["id"] for x in release_history}
    ]
    choices = []
    for job in pending:
        earliest = max(now, last.get(job["stream"], -10**9) + job["min_interarrival"])
        legal = [r for r in job["release_choices"] if r >= earliest]
        if not legal:
            return []
        choices.append(legal)
    for assigned in itertools.product(*choices) if choices else [()]:
        releases = {}
        valid = True
        by_stream = {}
        for job, release in zip(pending, assigned):
            prior = [x for x in release_history if x["stream"] == job["stream"]]
            prior.extend(
                {"stream": other["stream"], "actual_release": other_release}
                for other, other_release in zip(pending, assigned[:len(releases)])
                if other["stream"] == job["stream"]
            )
            if any(abs(release - x["actual_release"]) < job["min_interarrival"] for x in prior):
                valid = False
                break
            by_stream.setdefault(job["stream"], []).append(release)
            releases[job["id"]] = release
        if not valid:
            continue
        future = []
        for job in pending:
            release = releases[job["id"]]
            future.append({
                "id": job["id"], "release": release,
                "deadline": release + job["relative_deadline"],
                "remaining": job["wcet"] + overhead,
            })
        yield future


def _guard(case, now, release_history, overhead):
    # Every currently unreleased control obligation must take one of its
    # declared release times.  The candidate knows the finite envelope, not
    # the selected future actual_release values.
    assignments = list(_future_assignments(case, now + 1, release_history, overhead))
    return bool(assignments) and all(
        _edf_feasible(future, now + 1, case["horizon"]) for future in assignments
    )


def simulate(case, policy, overhead):
    horizon = case["horizon"]
    controls = {j["id"]: dict(j, remaining=j["wcet"] + overhead, started=False)
                for j in case["controls"]}
    soft = {j["id"]: dict(j, remaining=j["wcet"] + overhead, started=False)
            for j in case["soft_jobs"]}
    release_by_tick = {}
    for job in case["controls"]:
        release_by_tick.setdefault(job["actual_release"], []).append(job["id"])
    released = []
    events = []
    control_used = {}
    soft_used = {}
    for tick in range(horizon):
        releases = sorted(release_by_tick.get(tick, []))
        released.extend(controls[jid] for jid in releases)
        period = tick // PERIOD
        c_used = control_used.get(period, 0)
        b_used = soft_used.get(period, 0)
        ready_control = [j for j in released if j["remaining"] > 0]
        ready_soft = [j for j in case["soft_jobs"] if soft[j["id"]]["remaining"] > 0]
        picked = None
        kind = "idle"
        if policy == "PRIORITY_ONLY":
            if ready_control:
                picked = min(ready_control, key=lambda j: (j["actual_release"] + j["relative_deadline"], j["id"]))
                kind = "control_dispatch" if not picked["started"] and overhead else "control_work"
            elif ready_soft:
                picked = min((soft[j["id"]] for j in ready_soft), key=lambda j: j["id"])
                kind = "soft_dispatch" if not picked["started"] and overhead else "soft_work"
        elif policy == "STATIC_RESERVATION":
            if ready_control and c_used < CONTROL_BUDGET:
                picked = min(ready_control, key=lambda j: (j["actual_release"] + j["relative_deadline"], j["id"]))
                kind = "control_dispatch" if not picked["started"] and overhead else "control_work"
            elif ready_soft and b_used < SOFT_BUDGET:
                picked = min((soft[j["id"]] for j in ready_soft), key=lambda j: j["id"])
                kind = "soft_dispatch" if not picked["started"] and overhead else "soft_work"
        elif policy == "DEMAND_GUARDED_SLACK_STEAL":
            if ready_control:
                picked = min(ready_control, key=lambda j: (j["actual_release"] + j["relative_deadline"], j["id"]))
                kind = "control_dispatch" if not picked["started"] and overhead else "control_work"
            elif ready_soft and _guard(case, tick, released, overhead):
                picked = min((soft[j["id"]] for j in ready_soft), key=lambda j: j["id"])
                kind = "soft_dispatch" if not picked["started"] and overhead else "soft_work"
        else:
            raise ValueError("unknown policy")
        if picked is not None:
            if kind.endswith("_dispatch"):
                picked["started"] = True
                picked["remaining"] -= 1
            else:
                picked["remaining"] -= 1
            if kind.startswith("control_"):
                control_used[period] = c_used + 1
            else:
                soft_used[period] = b_used + 1
        events.append({
            "tick": tick, "releases": releases, "kind": kind,
            "job_id": None if picked is None else picked["id"],
            "period": period, "control_used_before": c_used,
            "soft_used_before": b_used,
        })
    summary = _summarize(case, events, overhead)
    return {"events": events, "summary": summary}


def _summarize(case, events, overhead):
    control = {j["id"]: {"remaining": j["wcet"] + overhead,
                          "release": j["actual_release"],
                          "deadline": j["actual_release"] + j["relative_deadline"]}
               for j in case["controls"]}
    soft = {j["id"]: {"remaining": j["wcet"] + overhead, "wcet": j["wcet"]}
            for j in case["soft_jobs"]}
    completion = {}
    for event in events:
        jid = event["job_id"]
        if jid is None:
            continue
        record = control.get(jid) or soft.get(jid)
        if event["kind"].endswith("_dispatch"):
            record["remaining"] -= 1
        elif event["kind"].endswith("_work"):
            record["remaining"] -= 1
        if record["remaining"] == 0 and jid not in completion:
            completion[jid] = event["tick"] + 1
    misses = []
    for jid, job in control.items():
        if job["remaining"] > 0 or jid not in completion or completion[jid] > job["deadline"]:
            misses.append(jid)
    responses = [completion[j["id"]] - j["actual_release"]
                 for j in case["controls"] if j["id"] in completion]
    payload = sum(1 for e in events if e["kind"] == "soft_work")
    return {
        "control_deadline_misses": sorted(misses),
        "control_completed": len(completion.keys() & control.keys()),
        "control_response_ticks": sorted(responses),
        "soft_payload_units": payload,
        "soft_jobs_completed": sum(1 for j in case["soft_jobs"] if j["id"] in completion),
        "cpu_busy_ticks": sum(e["kind"] != "idle" for e in events),
        "overhead_dispatch_ticks": sum(e["kind"].endswith("_dispatch") for e in events),
    }


def run(cases):
    rows = []
    for case in cases["cases"]:
        for overhead in cases["model"]["overhead_sensitivity_units_per_job_dispatch"]:
            for policy in POLICIES:
                result = simulate(case, policy, overhead)
                rows.append({
                    "schema": "7778-slack-reclamation-raw-v1",
                    "row_id": f"{case['case_id']}|oh={overhead}|{policy}",
                    "case_id": case["case_id"], "input": case,
                    "policy": policy, "overhead_units": overhead,
                    **result,
                })
    refusals = []
    for control in cases["refusal_controls"]:
        refusals.append({
            "id": control["id"], "input": control["job"],
            "expected": control["expected"], "result": refusal_status(control["job"]),
        })
    return rows, refusals


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--cases", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--refusals", type=Path, required=True)
    args = parser.parse_args()
    frozen = json.loads(args.cases.read_text(encoding="utf-8"))
    rows, refusals = run(frozen)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text("".join(json.dumps(row, sort_keys=True) + "\n" for row in rows), encoding="utf-8")
    args.refusals.write_text(json.dumps(refusals, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"rows": len(rows), "refusals": len(refusals), "status": "CANDIDATE_COMPLETE"}, sort_keys=True))


if __name__ == "__main__":
    main()
