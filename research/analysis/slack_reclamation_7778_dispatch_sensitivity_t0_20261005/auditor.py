"""Independent raw-event auditor; it does not import candidate.py."""
import itertools
import json
from collections import defaultdict

POLICIES = ("PRIORITY_ONLY", "STATIC_RESERVATION", "DEMAND_GUARDED_SLACK_STEAL")
PERIOD = 8
CONTROL_BUDGET = 2
SOFT_BUDGET = 6
VALID_CLASSES = {"control", "best_effort"}


def classify(job):
    if job.get("class") not in VALID_CLASSES:
        return "REJECT_INVALID_JOB_CLASS"
    if job.get("wcet") is None:
        return "HOLD_UNKNOWN_WCET"
    if type(job.get("wcet")) is not int or job["wcet"] <= 0:
        return "HOLD_INVALID_WCET"
    if job.get("preemptible") is not True:
        return "UNKNOWN_MODEL_MISMATCH"
    return "ELIGIBLE"


def future_release_sets(case, after, release_history):
    """Independent recursion over all declared future choices and stream gaps."""
    released_ids = {job["id"] for job in release_history}
    remaining = [job for job in case["controls"] if job["id"] not in released_ids]
    last = {}
    for job in release_history:
        last[job["stream"]] = max(last.get(job["stream"], -1), job["actual_release"])
    domains = []
    for job in remaining:
        low = max(after, last.get(job["stream"], -10**9) + job["min_interarrival"])
        domain = [r for r in job["release_choices"] if r >= low]
        if not domain:
            return []
        domains.append(domain)
    results = []

    def visit(index, assigned, per_stream):
        if index == len(remaining):
            results.append([
                {"id": job["id"], "release": release,
                 "deadline": release + job["relative_deadline"],
                 "work": job["wcet"]}
                for job, release in zip(remaining, assigned)
            ])
            return
        job = remaining[index]
        for release in domains[index]:
            prior = per_stream.get(job["stream"], [])
            if any(abs(release - old) < job["min_interarrival"] for old in prior):
                continue
            per_stream.setdefault(job["stream"], []).append(release)
            visit(index + 1, assigned + [release], per_stream)
            per_stream[job["stream"]].pop()

    visit(0, [], {})
    return results


def exhaustive_feasible(jobs, start, horizon):
    """Enumerate all unit-slot control schedules with state merging."""
    if not jobs:
        return True
    initial = tuple(job["work"] for job in jobs)
    states = {initial}
    for tick in range(start, horizon):
        following = set()
        for remaining in states:
            if any(remaining[i] and jobs[i]["deadline"] <= tick for i in range(len(jobs))):
                continue
            ready = [i for i, job in enumerate(jobs)
                     if job["release"] <= tick and remaining[i] > 0]
            for picked in ready + [-1]:
                row = list(remaining)
                if picked >= 0:
                    row[picked] -= 1
                candidate = tuple(row)
                if any(candidate[i] and jobs[i]["deadline"] <= tick + 1
                       for i in range(len(jobs))):
                    continue
                following.add(candidate)
        states = following
    return tuple(0 for _ in jobs) in states


def actual_control_oracle(case, overhead):
    jobs = [{"id": j["id"], "release": j["actual_release"],
             "deadline": j["actual_release"] + j["relative_deadline"],
             "work": j["wcet"] + overhead} for j in case["controls"]]
    return exhaustive_feasible(jobs, 0, case["horizon"])


def maximum_soft_work_oracle(case, overhead):
    """Exhaust all unit-time schedules; maximize soft payload under hard deadlines."""
    jobs = []
    control_count = len(case["controls"])
    for job in case["controls"]:
        jobs.append({"id": job["id"], "release": job["actual_release"],
                     "deadline": job["actual_release"] + job["relative_deadline"],
                     "payload": job["wcet"], "overhead": overhead,
                     "hard": True, "initial": job["wcet"] + overhead})
    for job in case["soft_jobs"]:
        jobs.append({"id": job["id"], "release": job["release"],
                     "deadline": case["horizon"], "payload": job["wcet"],
                     "overhead": overhead, "hard": False,
                     "initial": job["wcet"] + overhead})
    states = {tuple(job["initial"] for job in jobs)}
    for tick in range(case["horizon"]):
        following = set()
        for rem in states:
            if any(rem[i] and jobs[i]["hard"] and jobs[i]["deadline"] <= tick
                   for i in range(control_count)):
                continue
            ready = [i for i, job in enumerate(jobs)
                     if job["release"] <= tick and rem[i] > 0]
            for picked in ready + [-1]:
                nxt = list(rem)
                if picked >= 0:
                    nxt[picked] -= 1
                state = tuple(nxt)
                if any(state[i] and jobs[i]["hard"] and jobs[i]["deadline"] <= tick + 1
                       for i in range(control_count)):
                    continue
                following.add(state)
        states = following
    best = None
    for rem in states:
        if any(rem[i] for i in range(control_count)):
            continue
        payload = 0
        for index in range(control_count, len(jobs)):
            job = jobs[index]
            consumed = job["initial"] - rem[index] - job["overhead"]
            payload += min(job["payload"], max(0, consumed))
        best = payload if best is None else max(best, payload)
    return best


def demand_witness(case, overhead):
    jobs = [
        {"release": job["actual_release"],
         "deadline": job["actual_release"] + job["relative_deadline"],
         "work": job["wcet"] + overhead}
        for job in case["controls"]
    ]
    points = sorted({0, case["horizon"]}
                    | {j["release"] for j in jobs}
                    | {j["deadline"] for j in jobs})
    for left in points:
        for right in points:
            if right <= left:
                continue
            demand = sum(j["work"] for j in jobs
                         if j["release"] >= left and j["deadline"] <= right)
            if demand > right - left:
                return {"start": left, "end": right, "demand": demand,
                        "capacity": right - left, "excess": demand - (right - left)}
    return None


def guard_oracle(case, now, release_history, overhead):
    possibilities = future_release_sets(case, now + 1, release_history)
    if not possibilities:
        return False
    return all(
        exhaustive_feasible(
            [dict(job, work=job["work"] + overhead) for job in schedule],
            now + 1, case["horizon"]
        )
        for schedule in possibilities
    )


def _expected_kind(case, policy, overhead, tick, released, ctrl_rem,
                   soft_rem, ctrl_started, soft_started, c_used, b_used):
    controls = [j for j in released if ctrl_rem[j["id"]] > 0]
    soft = [j for j in case["soft_jobs"] if soft_rem[j["id"]] > 0]
    chosen = None
    if policy == "PRIORITY_ONLY":
        if controls:
            chosen = min(controls, key=lambda j: (j["actual_release"] + j["relative_deadline"], j["id"]))
        elif soft:
            chosen = min(soft, key=lambda j: j["id"])
    elif policy == "STATIC_RESERVATION":
        if controls and c_used < CONTROL_BUDGET:
            chosen = min(controls, key=lambda j: (j["actual_release"] + j["relative_deadline"], j["id"]))
        elif soft and b_used < SOFT_BUDGET:
            chosen = min(soft, key=lambda j: j["id"])
    elif policy == "DEMAND_GUARDED_SLACK_STEAL":
        if controls:
            chosen = min(controls, key=lambda j: (j["actual_release"] + j["relative_deadline"], j["id"]))
        elif soft and guard_oracle(case, tick, released, overhead):
            chosen = min(soft, key=lambda j: j["id"])
    if chosen is None:
        return "idle", None
    is_control = chosen["id"] in ctrl_rem
    started = ctrl_started[chosen["id"]] if is_control else soft_started[chosen["id"]]
    prefix = "control" if is_control else "soft"
    kind = prefix + ("_dispatch" if overhead and not started else "_work")
    return kind, chosen["id"]


def audit(raw_rows, refusal_rows, frozen):
    errors = []
    expected_cases = {case["case_id"]: case for case in frozen.get("cases", [])}
    expected_keys = {
        (case["case_id"], overhead, policy)
        for case in frozen.get("cases", [])
        for overhead in frozen["model"]["overhead_sensitivity_units_per_job_dispatch"]
        for policy in POLICIES
    }
    rows_by_key = {}
    for row in raw_rows:
        key = (row.get("case_id"), row.get("overhead_units"), row.get("policy"))
        if key in rows_by_key:
            errors.append("duplicate_row:" + str(key))
        rows_by_key[key] = row
    if set(rows_by_key) != expected_keys:
        errors.append("row_key_set")
    metrics = {}
    for key, row in rows_by_key.items():
        case_id, overhead, policy = key
        if row.get("schema") != "7778-slack-reclamation-raw-v1":
            errors.append("raw_schema:" + str(key))
        if row.get("row_id") != f"{case_id}|oh={overhead}|{policy}":
            errors.append("row_identity:" + str(key))
        case = expected_cases.get(case_id)
        if case is None:
            errors.append("unknown_case:" + str(case_id))
            continue
        if row.get("input") != case:
            errors.append("input_mismatch:" + str(case_id))
        if overhead not in (0, 1) or policy not in POLICIES:
            errors.append("invalid_model_factor:" + str(key))
            continue
        controls = {j["id"]: j for j in case["controls"]}
        soft = {j["id"]: j for j in case["soft_jobs"]}
        ctrl_rem = {j["id"]: j["wcet"] + overhead for j in case["controls"]}
        soft_rem = {j["id"]: j["wcet"] + overhead for j in case["soft_jobs"]}
        ctrl_started = {jid: False for jid in ctrl_rem}
        soft_started = {jid: False for jid in soft_rem}
        release_map = defaultdict(list)
        for job in case["controls"]:
            release_map[job["actual_release"]].append(job["id"])
        released = []
        control_used = defaultdict(int)
        soft_used = defaultdict(int)
        events = row.get("events")
        if not isinstance(events, list) or len(events) != case["horizon"]:
            errors.append("event_count:" + str(key))
            continue
        completion = {}
        soft_payload = 0
        busy = 0
        dispatches = 0
        for tick, event in enumerate(events):
            if not isinstance(event, dict) or event.get("tick") != tick:
                errors.append("tick_order:" + str(key))
                continue
            newly = sorted(release_map.get(tick, []))
            if event.get("releases") != newly:
                errors.append("omitted_or_forged_release:" + str(key) + f"@{tick}")
            released.extend(controls[jid] for jid in newly)
            period = tick // PERIOD
            c_before, b_before = control_used[period], soft_used[period]
            if event.get("period") != period or event.get("control_used_before") != c_before or event.get("soft_used_before") != b_before:
                errors.append("budget_counter:" + str(key) + f"@{tick}")
            expected_kind, expected_job = _expected_kind(
                case, policy, overhead, tick, released, ctrl_rem, soft_rem,
                ctrl_started, soft_started, c_before, b_before
            )
            if event.get("kind") != expected_kind or event.get("job_id") != expected_job:
                errors.append("policy_action:" + str(key) + f"@{tick}")
            kind, jid = event.get("kind"), event.get("job_id")
            if kind != "idle":
                busy += 1
            if kind in {"control_dispatch", "control_work"}:
                if jid not in ctrl_rem or jid not in {j["id"] for j in released}:
                    errors.append("control_provenance:" + str(key) + f"@{tick}")
                control_used[period] += 1
            elif kind in {"soft_dispatch", "soft_work"}:
                if jid not in soft_rem or soft[jid]["release"] > tick:
                    errors.append("soft_provenance:" + str(key) + f"@{tick}")
                soft_used[period] += 1
                if kind == "soft_work":
                    soft_payload += 1
            elif kind != "idle":
                errors.append("invalid_event_kind:" + str(key) + f"@{tick}")
            if kind in {"control_dispatch", "soft_dispatch"}:
                dispatches += 1
                if kind == "control_dispatch":
                    ctrl_started[jid] = True
                    ctrl_rem[jid] -= 1
                else:
                    soft_started[jid] = True
                    soft_rem[jid] -= 1
            elif kind in {"control_work", "soft_work"}:
                if kind == "control_work":
                    ctrl_rem[jid] -= 1
                else:
                    soft_rem[jid] -= 1
                rem = ctrl_rem.get(jid, soft_rem.get(jid))
                if rem == 0 and jid not in completion:
                    completion[jid] = tick + 1
            if policy == "STATIC_RESERVATION":
                if control_used[period] > CONTROL_BUDGET:
                    errors.append("control_reservation_exceeded:" + str(key) + f"@{tick}")
                if soft_used[period] > SOFT_BUDGET:
                    errors.append("soft_budget_exceeded:" + str(key) + f"@{tick}")
        misses = sorted(
            jid for jid, job in controls.items()
            if jid not in completion or completion[jid] > job["actual_release"] + job["relative_deadline"]
        )
        summary = {
            "control_deadline_misses": misses,
            "control_completed": sum(jid in completion for jid in controls),
            "control_response_ticks": sorted(
                completion[j["id"]] - j["actual_release"]
                for j in case["controls"] if j["id"] in completion
            ),
            "soft_payload_units": soft_payload,
            "soft_jobs_completed": sum(jid in completion for jid in soft),
            "cpu_busy_ticks": busy,
            "overhead_dispatch_ticks": dispatches,
        }
        if row.get("summary") != summary:
            errors.append("summary_mismatch:" + str(key))
        if policy == "DEMAND_GUARDED_SLACK_STEAL":
            for event in events:
                if event.get("kind") == "soft_work" or event.get("kind") == "soft_dispatch":
                    history = [j for j in case["controls"] if j["actual_release"] <= event["tick"]]
                    if not guard_oracle(case, event["tick"], history, overhead):
                        errors.append("unsafe_slack_grant:" + str(key) + f"@{event['tick']}")
                        break
        feasible = actual_control_oracle(case, overhead)
        metrics[key] = {
            **summary,
            "control_only_feasible": feasible,
            "oracle_max_soft_payload_units": maximum_soft_work_oracle(case, overhead),
        }
        oracle_soft = metrics[key]["oracle_max_soft_payload_units"]
        if oracle_soft is not None and summary["soft_payload_units"] > oracle_soft:
            errors.append("soft_work_exceeds_exhaustive_oracle:" + str(key))
    expected_refusals = {x["id"]: x for x in frozen.get("refusal_controls", [])}
    got_refusals = {x.get("id"): x for x in refusal_rows}
    if set(got_refusals) != set(expected_refusals):
        errors.append("refusal_set")
    for rid, expected in expected_refusals.items():
        row = got_refusals.get(rid, {})
        if row.get("input") != expected["job"] or row.get("expected") != expected["expected"]:
            errors.append("refusal_input:" + rid)
        if classify(expected["job"]) != expected["expected"] or row.get("result") != expected["expected"]:
            errors.append("refusal_not_fail_closed:" + rid)
    primary = [case for case in frozen["cases"] if not errors]
    feasible_guard_failures = []
    for case in primary:
        for overhead in frozen["model"]["overhead_sensitivity_units_per_job_dispatch"]:
            key = (case["case_id"], overhead, "DEMAND_GUARDED_SLACK_STEAL")
            observed = metrics.get(key)
            if observed and observed["control_only_feasible"] and observed["control_deadline_misses"]:
                feasible_guard_failures.append(f"{case['case_id']}|oh={overhead}")
    positive = [case for case in primary if case["positive_slack_subset"]]
    static_units = sum(metrics.get((c["case_id"], 0, "STATIC_RESERVATION"), {}).get("soft_payload_units", 0) for c in positive)
    slack_units = sum(metrics.get((c["case_id"], 0, "DEMAND_GUARDED_SLACK_STEAL"), {}).get("soft_payload_units", 0) for c in positive)
    method_status = "PASS_METHOD_SCOPED" if not errors else "FAIL_METHOD"
    hypothesis_status = (
        "H_PASS_SCOPED" if method_status == "PASS_METHOD_SCOPED" and positive and not feasible_guard_failures and slack_units > static_units
        else "H_FAIL_SCOPED"
    )
    case_metrics = [
        {"case_id": case_id, "overhead_units": overhead, "policy": policy, **value}
        for (case_id, overhead, policy), value in sorted(metrics.items())
    ]
    infeasible_models = []
    for case in frozen["cases"]:
        for overhead in frozen["model"]["overhead_sensitivity_units_per_job_dispatch"]:
            control_key = (case["case_id"], overhead, "PRIORITY_ONLY")
            control_metric = metrics.get(control_key)
            if control_metric and not control_metric["control_only_feasible"]:
                infeasible_models.append({
                    "case_id": case["case_id"], "overhead_units": overhead,
                    "status": "INFEASIBLE" if demand_witness(case, overhead) else "UNKNOWN",
                    "demand_witness": demand_witness(case, overhead),
                    "deadline_misses_by_policy": {
                        policy: metrics.get((case["case_id"], overhead, policy), {}).get("control_deadline_misses", [])
                        for policy in POLICIES
                    },
                })
    return {
        "method_status": method_status,
        "hypothesis_status": hypothesis_status,
        "errors": errors,
        "rows": len(raw_rows), "refusal_controls": len(refusal_rows),
        "positive_slack_case_count": len(positive),
        "positive_slack_static_payload_units": static_units,
        "positive_slack_guarded_payload_units": slack_units,
        "feasible_guard_deadline_failures": feasible_guard_failures,
        "case_metrics": case_metrics,
        "infeasible_models": infeasible_models,
        "model_scope": "finite integer-time preemptive uniprocessor; simulator only",
    }


if __name__ == "__main__":
    import argparse
    from pathlib import Path
    parser = argparse.ArgumentParser()
    parser.add_argument("--raw", required=True)
    parser.add_argument("--refusals", required=True)
    parser.add_argument("--cases", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    raw = [json.loads(line) for line in Path(args.raw).read_text(encoding="utf-8").splitlines() if line]
    refusal_rows = json.loads(Path(args.refusals).read_text(encoding="utf-8"))
    frozen = json.loads(Path(args.cases).read_text(encoding="utf-8"))
    result = audit(raw, refusal_rows, frozen)
    Path(args.out).write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, sort_keys=True))
