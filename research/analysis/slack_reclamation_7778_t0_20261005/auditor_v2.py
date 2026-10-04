"""Independent raw-log auditor with exhaustive finite schedule enumeration."""
import json
import os
import sys
from functools import lru_cache
from pathlib import Path

ROOT = Path(__file__).parent
OUT = Path(os.environ.get("OUTPUT_DIR", ROOT))
P = json.loads((ROOT / "protocol.json").read_text())


def brute_feasible(jobs, start, horizon, blocked=()):
    jobs = tuple((j["class"], j["release"], j["deadline"], j["execution"])
                 for j in jobs)
    blocked = frozenset(blocked)

    @lru_cache(None)
    def visit(t, rem):
        if any(kind == "control" and amount and due <= t
               for (kind, rel, due, _), amount in zip(jobs, rem)):
            return False
        if t >= horizon:
            return not any(kind == "control" and amount
                           for (kind, _, _, _), amount in zip(jobs, rem))
        choices = [None]
        if t not in blocked:
            choices += [i for i, ((_, rel, _, _), amount) in
                        enumerate(zip(jobs, rem)) if rel <= t and amount > 0]
        for chosen in choices:
            nxt = list(rem)
            if chosen is not None:
                nxt[chosen] -= 1
            if visit(t + 1, tuple(nxt)):
                return True
        return False

    return visit(start, tuple(j[3] for j in jobs))


def max_optional_service(jobs, horizon):
    jobs = tuple((j["class"], j["release"], j["deadline"], j["execution"])
                 for j in jobs)

    @lru_cache(None)
    def visit(t, rem):
        if any(kind == "control" and amount and due <= t
               for (kind, _, due, _), amount in zip(jobs, rem)):
            return -1
        if t == horizon:
            return 0 if not any(kind == "control" and amount
                                for (kind, _, _, _), amount in zip(jobs, rem)) else -1
        best = visit(t + 1, rem)
        for i, ((kind, release, _, _), amount) in enumerate(zip(jobs, rem)):
            if release > t or amount <= 0:
                continue
            nxt = list(rem)
            nxt[i] -= 1
            score = visit(t + 1, tuple(nxt))
            if score >= 0:
                best = max(best, score + (kind == "soft"))
        return best

    return visit(0, tuple(j[3] for j in jobs))


def all_patterns(first, gap, last, remaining_count=None):
    patterns = [()]
    if remaining_count == 0:
        return patterns
    for r in range(first, last + 1):
        next_count = None if remaining_count is None else remaining_count - 1
        for tail in all_patterns(r + gap, gap, last, next_count):
            patterns.append((r,) + tail)
    return patterns


def guard_is_safe(t, contract, horizon, last_release, observed_count):
    gap = contract["min_interarrival"]
    wcet = contract["max_execution"]
    rel_deadline = contract["relative_deadline"]
    first = max(t + 1, last_release + gap if last_release is not None else t + 1)
    max_total = contract.get("max_jobs_total")
    remaining_count = None if max_total is None else max(0, max_total - observed_count)
    for pattern in all_patterns(first, gap, horizon - rel_deadline, remaining_count):
        jobs = [{"class": "control", "release": r,
                 "deadline": r + rel_deadline, "execution": wcet}
                for r in pattern]
        if not brute_feasible(jobs, t + 1, horizon, blocked=(t,)):
            return False
    return True


def validate_row(trace, row):
    if set(row) not in ({"trace_id", "policy", "status", "events"},
                        {"trace_id", "policy", "status", "events", "remaining",
                         "control_completed", "soft_service"}):
        return False, "ROW_SCHEMA"
    if row["trace_id"] != trace["trace_id"]:
        return False, "TRACE_ID"
    policy = row["policy"]
    if policy not in P["policies"]:
        return False, "POLICY"
    jobs = trace["jobs"]
    expected_hold = None
    if any(j.get("class") not in ("control", "soft") for j in jobs):
        expected_hold = "HOLD_INVALID_JOB_CLASS"
    elif any(j.get("execution") is None for j in jobs):
        expected_hold = "HOLD_MODEL_MISMATCH"
    elif any(not j.get("preemptible", False) for j in jobs) or not trace["contract"].get("preemptive"):
        expected_hold = "HOLD_MODEL_MISMATCH"
    if expected_hold:
        return (row["status"] == expected_hold and row["events"] == []), expected_hold
    contract = trace["contract"]
    controls_in = sorted((j for j in jobs if j["class"] == "control"),
                         key=lambda j: (j["release"], j["id"]))
    if any(j["execution"] > contract["max_execution"] or
           j["deadline"] != j["release"] + contract["relative_deadline"]
           for j in controls_in):
        return row["status"] == "HOLD_MODEL_MISMATCH" and row["events"] == [], "CONTRACT_BOUND"
    if any(b["release"] - a["release"] < contract["min_interarrival"]
           for a, b in zip(controls_in, controls_in[1:])):
        return row["status"] == "HOLD_MODEL_MISMATCH" and row["events"] == [], "CONTRACT_ARRIVAL"
    if (contract.get("max_jobs_total") is not None and
            len(controls_in) > contract["max_jobs_total"]):
        return row["status"] == "HOLD_MODEL_MISMATCH" and row["events"] == [], "CONTRACT_COUNT"

    rem = {j["id"]: j["execution"] for j in jobs}
    known_control = set()
    last_release = None
    observed_control_count = 0
    events = row["events"]
    if row["status"] == "COMPLETE" and len(events) != trace["horizon"]:
        return False, "EVENT_COUNT"
    if row["status"] == "UNKNOWN_OVERLOAD" and not (0 < len(events) <= trace["horizon"]):
        return False, "OVERLOAD_EVENT_COUNT"
    overload_seen = False
    for t, e in enumerate(events):
        if set(e) != {"tick", "arrivals", "action", "reserved"}:
            return False, "EVENT_SCHEMA"
        if e["tick"] != t:
            return False, "TICK_ORDER"
        arrivals = [j for j in jobs if j["release"] == t]
        if e["arrivals"] != [j["id"] for j in arrivals]:
            return False, "ARRIVAL_LEDGER"
        for j in arrivals:
            if j["class"] == "control":
                known_control.add(j["id"])
                last_release = t
                observed_control_count += 1
        if e["reserved"] != (t % P["reservation_period"] == 0):
            return False, "RESERVATION_PHASE"
        action = e["action"]
        if action is not None:
            if not isinstance(action, str) or action not in rem:
                return False, "UNKNOWN_ACTION"
            j = next(x for x in jobs if x["id"] == action)
            if j["release"] > t or rem[action] <= 0:
                return False, "UNRELEASED_OR_DUPLICATE_SERVICE"
            if policy == "STATIC_RESERVATION":
                if e["reserved"] != (j["class"] == "control"):
                    return False, "RESERVATION_CLASS"
            ready_hard = [x for x in jobs if x["id"] in known_control and rem[x["id"]] > 0]
            if policy in ("PRIORITY_ONLY", "DEMAND_GUARDED_SLACK_STEAL") and ready_hard:
                expected = min(ready_hard, key=lambda x: (x["deadline"], x["id"]))
                if action != expected["id"]:
                    return False, "CONTROL_PRIORITY"
            if policy == "DEMAND_GUARDED_SLACK_STEAL" and j["class"] == "soft":
                if ready_hard or not guard_is_safe(t, trace["contract"],
                                                    trace["horizon"], last_release,
                                                    observed_control_count):
                    return False, "UNSAFE_SLACK"
            rem[action] -= 1
        if any(rem[jid] and next(x for x in jobs if x["id"] == jid)["deadline"] <= t + 1
               for jid in known_control):
            if row["status"] != "UNKNOWN_OVERLOAD" or t != len(events) - 1:
                return False, "CONTROL_DEADLINE"
            overload_seen = True
            break
    controls_ok = all(rem[j["id"]] == 0 for j in jobs if j["class"] == "control")
    soft_service = sum(j["execution"] - rem[j["id"]]
                       for j in jobs if j["class"] == "soft")
    if row["remaining"] != rem or row["control_completed"] != controls_ok:
        return False, "TERMINAL_STATE"
    if row["soft_service"] != soft_service:
        return False, "SOFT_SERVICE"
    if row["status"] == "UNKNOWN_OVERLOAD":
        return overload_seen, "EXPECTED_OVERLOAD" if overload_seen else "FALSE_OVERLOAD"
    return True, "OK"


def run_audit():
    data = json.loads((OUT / "inputs.json").read_text())
    result = json.loads((OUT / "candidate.json").read_text())
    if data["allocation"] != P["allocation"] or result["allocation"] != P["allocation"]:
        raise ValueError("ALLOCATION_ID")
    traces = {x["trace_id"]: x for x in data["traces"]}
    rows = result["rows"]
    if len(traces) != P["trace_count"] or len(rows) != len(traces) * len(P["policies"]):
        raise ValueError("GRID_SIZE")
    by_key = {(r["trace_id"], r["policy"]): r for r in rows}
    if len(by_key) != len(rows):
        raise ValueError("DUPLICATE_ROW")
    checks = []
    method_ok = True
    slack_gain = []
    oracle_records = []
    for trace_id, trace in traces.items():
        jobs = trace["jobs"]
        oracle_applicable = trace["kind"] in ("eligible", "infeasible")
        optimum = max_optional_service(jobs, trace["horizon"]) if oracle_applicable else None
        feasible = optimum >= 0 if oracle_applicable else False
        if (trace["kind"] == "eligible" and not feasible) or (
                trace["kind"] == "infeasible" and feasible):
            method_ok = False
        oracle_records.append({"trace_id": trace_id, "hard_feasible": feasible,
                               "max_optional_service": optimum})
        for policy in P["policies"]:
            row = by_key[(trace_id, policy)]
            ok, detail = validate_row(trace, row)
            checks.append({"trace_id": trace_id, "policy": policy,
                           "check": detail, "pass": ok})
            if not ok:
                method_ok = False
        slack = by_key[(trace_id, "DEMAND_GUARDED_SLACK_STEAL")]
        if trace["kind"] == "eligible" and (slack["status"] != "COMPLETE" or
                not slack["control_completed"] or not feasible or
                slack["soft_service"] != optimum):
            method_ok = False
        if trace["kind"] == "infeasible" and slack["status"] != "UNKNOWN_OVERLOAD":
            method_ok = False
        for policy in P["policies"]:
            row = by_key[(trace_id, policy)]
            if (feasible and row["status"] == "COMPLETE" and
                    row["soft_service"] > optimum):
                method_ok = False
        if trace_id in P["positive_slack_traces"]:
            a = by_key[(trace_id, "DEMAND_GUARDED_SLACK_STEAL")]["soft_service"]
            b = by_key[(trace_id, "STATIC_RESERVATION")]["soft_service"]
            slack_gain.append({"trace_id": trace_id, "slack": a, "static": b,
                               "strict_gain": a > b})
    # Independent mutation checks on an eligible static row.
    base = by_key[("idle_gaps", "STATIC_RESERVATION")]
    t = traces["idle_gaps"]
    mutants = []
    mutations = []
    m = json.loads(json.dumps(base)); m["events"] = m["events"][:-1]; mutations.append(("dropped_tick", m))
    m = json.loads(json.dumps(base)); m["events"][1]["tick"] = 0; mutations.append(("duplicate_tick", m))
    m = json.loads(json.dumps(base)); m["events"][0]["arrivals"] = ["forged"]; mutations.append(("omitted_or_forged_arrival", m))
    m = json.loads(json.dumps(base)); m["events"][0]["action"] = ["s0", "s1"]; mutations.append(("double_spent_slot", m))
    m = json.loads(json.dumps(base)); m["events"][1]["reserved"] = True; mutations.append(("early_replenishment", m))
    m = json.loads(json.dumps(base)); m["events"][0]["action"] = "c0"; mutations.append(("unreleased_control", m))
    for name, mutant in mutations:
        ok, _ = validate_row(t, mutant)
        mutants.append({"mutation": name, "rejected": not ok})
        if ok:
            method_ok = False
    hypothesis = ("HOLD_AUDIT_OR_OUTCOME" if not method_ok else
                  "H_PASS_SCOPED" if all(x["strict_gain"] for x in slack_gain)
                  else "H_FAIL_SCOPED")
    return {"allocation": P["allocation"],
            "disposition": "PASS_METHOD_SCOPED" if method_ok else "FAIL_AUDIT",
            "hypothesis": hypothesis,
            "trace_count": len(traces), "policy_rows": len(rows),
            "oracle": oracle_records, "checks": checks,
            "positive_slack_comparison": slack_gain,
            "mutation_checks": mutants,
            "audit_errors": [x for x in checks if not x["pass"]] +
                            [x for x in mutants if not x["rejected"]]}


def main():
    audit = run_audit()
    (OUT / "audit.json").write_text(
        json.dumps(audit, sort_keys=True, separators=(",", ":")) + "\n",
        encoding="utf-8")
    if audit["disposition"] != "PASS_METHOD_SCOPED":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
