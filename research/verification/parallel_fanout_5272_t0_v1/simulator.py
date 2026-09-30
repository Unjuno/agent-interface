#!/usr/bin/env python3
"""Deterministic synthetic parallel verifier fan-out T0 (no verifier side effects)."""
import hashlib
import json
import os
from pathlib import Path

POLICIES = {"SERIAL_VERIFIERS": 1, "PARALLEL_FANOUT": 3}


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def sha256_bytes(data):
    return hashlib.sha256(data).hexdigest()


def digest_result(case, job):
    value = {
        "job_id": job["job_id"],
        "input_sha256": job["input_sha256"],
        "source_version": "plan-v1",
        "verifier_id": "stub-v1",
        "verifier_version": "1.0",
        "outcome": job["outcome"],
    }
    return sha256_bytes(canonical(value).encode("utf-8"))


def terminal(row):
    return row["status"] not in {"PENDING", "RUNNING"}


def _decision(jobs, case):
    mandatory = [jobs[j["job_id"]] for j in case["jobs"] if j["required"]]
    if any(x.get("outcome") == "FAIL" for x in mandatory):
        return "FAIL"
    if all(x["status"] == "COMPLETED" and x.get("outcome") == "PASS" for x in mandatory):
        return "PASS"
    return "UNCERTAIN"


def simulate(case, policy, input_config):
    max_workers = POLICIES[policy]
    jobs = {
        spec["job_id"]: {
            "job_id": spec["job_id"], "required": spec["required"],
            "status": "PENDING", "outcome": None, "worker_id": None,
            "start_ms": None, "finish_ms": None, "elapsed_ms": 0,
            "effective_service_ms": None, "cost_units": spec["cost_units"],
            "result_sha256": None, "reason": None,
        }
        for spec in case["jobs"]
    }
    specs = {x["job_id"]: x for x in case["jobs"]}
    available_slots = list(range(max_workers))
    active = {}
    trace = []
    now = 0
    budget_left = case["budget_units"]
    reserved_units = 0
    decision = None
    decision_ready_ms = None
    cancelled_work_ms = 0

    def add_event(kind, jid, at):
        trace.append({"at_ms": at, "kind": kind, "job_id": jid})

    def cancel_remaining(kind, at):
        nonlocal cancelled_work_ms
        for jid, state in list(active.items()):
            row = jobs[jid]
            row["status"] = kind
            row["outcome"] = None
            row["finish_ms"] = at
            row["elapsed_ms"] = at - row["start_ms"]
            cancelled_work_ms += row["elapsed_ms"]
            add_event(kind, jid, at)
            available_slots.append(state["worker_id"])
            del active[jid]
        for jid, row in jobs.items():
            if row["status"] == "PENDING":
                row["status"] = kind
                row["reason"] = "decision_complete"
                row["finish_ms"] = at
                add_event(kind, jid, at)

    def resolve_blocked():
        changed = True
        while changed:
            changed = False
            for jid, row in jobs.items():
                if row["status"] != "PENDING":
                    continue
                deps = specs[jid]["dependencies"]
                if deps and all(terminal(jobs[d]) for d in deps):
                    if any(jobs[d].get("outcome") != "PASS" for d in deps):
                        row["status"] = "SKIPPED_DEPENDENCY"
                        row["reason"] = "dependency_not_pass"
                        row["finish_ms"] = now
                        add_event(row["status"], jid, now)
                        changed = True

    while decision is None:
        resolve_blocked()

        mandatory_rows = [jobs[s["job_id"]] for s in case["jobs"] if s["required"]]
        # A mandatory FAIL is decisive immediately; no other verifier can change FAIL.
        failed = [r for r in mandatory_rows if r["status"] == "COMPLETED" and r.get("outcome") == "FAIL"]
        if failed:
            decision = "FAIL"
            decision_ready_ms = min(r["finish_ms"] for r in failed)
            cancel_remaining("CANCELLED_AFTER_FAIL", decision_ready_ms)
            break

        mandatory_done = all(terminal(r) for r in mandatory_rows) and not any(
            jobs[j]["required"] for j in active
        )
        if mandatory_done:
            decision = _decision(jobs, case)
            decision_ready_ms = now
            cancel_remaining("CANCELLED_AFTER_DECISION", now)
            break

        dispatched = True
        while dispatched and available_slots and decision is None:
            dispatched = False
            runnable = []
            for jid, row in jobs.items():
                if row["status"] != "PENDING":
                    continue
                deps = specs[jid]["dependencies"]
                if all(jobs[d]["status"] == "COMPLETED" and jobs[d].get("outcome") == "PASS" for d in deps):
                    runnable.append(jid)
            runnable.sort(key=lambda jid: (
                0 if specs[jid]["required"] else 1,
                specs[jid].get("job_deadline_ms", case["deadline_ms"]),
                jid,
            ))
            for jid in runnable:
                row, spec = jobs[jid], specs[jid]
                deadline = min(case["deadline_ms"], spec.get("job_deadline_ms", case["deadline_ms"]))
                if now >= deadline:
                    row["status"] = "SKIPPED_DEADLINE"
                    row["reason"] = "deadline_before_start"
                    row["finish_ms"] = now
                    add_event(row["status"], jid, now)
                    dispatched = True
                    continue
                if spec["cost_units"] > budget_left:
                    row["status"] = "SKIPPED_BUDGET"
                    row["reason"] = "budget_exhausted"
                    row["finish_ms"] = now
                    add_event(row["status"], jid, now)
                    dispatched = True
                    if spec["required"] and not active:
                        decision = "UNCERTAIN"
                        decision_ready_ms = now
                        cancel_remaining("CANCELLED_AFTER_DECISION", now)
                        break
                    continue
                if not available_slots:
                    break
                budget_left -= spec["cost_units"]
                reserved_units += spec["cost_units"]
                worker = min(available_slots)
                available_slots.remove(worker)
                slowdown = case["slowdown_per_other_worker"] if policy == "PARALLEL_FANOUT" else 0
                duration = spec["duration_ms"] * (1 + slowdown * len(active))
                timeout = spec.get("timeout_ms")
                deadline_limit = deadline
                planned = now + duration
                if timeout is not None and now + timeout < min(planned, deadline_limit):
                    event_at, event_kind = now + timeout, "TIMEOUT"
                elif deadline_limit <= planned:
                    event_at, event_kind = deadline_limit, "DEADLINE"
                else:
                    event_at, event_kind = planned, "COMPLETED"
                row.update({"status": "RUNNING", "worker_id": worker, "start_ms": now,
                            "effective_service_ms": duration, "reason": None})
                active[jid] = {"worker_id": worker, "event_at": event_at,
                               "event_kind": event_kind}
                add_event("START", jid, now)
                dispatched = True
                if not available_slots:
                    break

        if decision is not None:
            break
        if not any(jobs[jid]["required"] for jid in active) and any(
            terminal(jobs[s["job_id"]]) and jobs[s["job_id"]]["status"] != "COMPLETED"
            for s in case["jobs"] if jobs[s["job_id"]]["required"]
        ):
            decision = "UNCERTAIN"
            decision_ready_ms = now
            cancel_remaining("CANCELLED_AFTER_DECISION", now)
            break
        if not active:
            # Nothing can run; any remaining required item is unresolved and fail-closed.
            decision = _decision(jobs, case)
            if decision == "UNCERTAIN":
                raise AssertionError("unresolved required work must be terminalized before idle decision")
            decision_ready_ms = max((jobs[s["job_id"]]["finish_ms"] or 0)
                                    for s in case["jobs"] if jobs[s["job_id"]]["required"])
            cancel_remaining("CANCELLED_AFTER_DECISION", decision_ready_ms)
            break

        now = min(x["event_at"] for x in active.values())
        due = sorted(
            [jid for jid, state in active.items() if state["event_at"] == now],
            key=lambda jid: jid,
        )
        for jid in due:
            state = active.pop(jid)
            row, spec = jobs[jid], specs[jid]
            row["finish_ms"] = now
            row["elapsed_ms"] = now - row["start_ms"]
            row["status"] = state["event_kind"]
            if row["status"] == "COMPLETED":
                row["outcome"] = spec["outcome"]
                row["result_sha256"] = digest_result(case, {
                    **spec, "outcome": row["outcome"]
                })
            else:
                row["outcome"] = "UNKNOWN"
                row["reason"] = state["event_kind"].lower()
                cancelled_work_ms += row["elapsed_ms"]
            available_slots.append(state["worker_id"])
            add_event(row["status"], jid, now)

    intervals = sorted(
        [(r["start_ms"], r["finish_ms"], r["worker_id"])
         for r in jobs.values() if r["start_ms"] is not None],
        key=lambda x: (x[0], x[1], x[2]),
    )
    points = []
    for start, end, worker in intervals:
        points.append((start, 1))
        points.append((end, -1))
    live = peak = 0
    for at, delta in sorted(points, key=lambda x: (x[0], x[1])):
        live += delta
        peak = max(peak, live)
    rows = [jobs[s["job_id"]] for s in case["jobs"]]
    return {
        "case_id": case["case_id"], "policy": policy, "decision": decision,
        "decision_ready_ms": decision_ready_ms, "jobs": rows,
        "trace": sorted(trace, key=lambda x: (x["at_ms"], x["kind"], x["job_id"])),
        "metrics": {
            "peak_concurrency": peak,
            "reserved_budget_units": reserved_units,
            "budget_limit_units": case["budget_units"],
            "compute_ms": sum(r["elapsed_ms"] for r in rows if r["start_ms"] is not None),
            "cancelled_or_timed_out_ms": cancelled_work_ms,
        },
    }


def load_workloads():
    return json.loads(Path(__file__).with_name("workloads.json").read_text(encoding="utf-8"))


def run_all(workloads):
    raw_cases = []
    for case in workloads["cases"]:
        for policy in POLICIES:
            raw_cases.append(simulate(case, policy, workloads["config"]))
    return {
        "schema": "parallel-fanout-t0-v1",
        "workload_sha256": sha256_bytes(canonical(workloads).encode("utf-8")),
        "cases": raw_cases,
    }


def sha256_bytes(data):
    return hashlib.sha256(data).hexdigest()


def main():
    workloads = load_workloads()
    raw = run_all(workloads)
    output = Path(os.environ["RAW_OUT"])
    if output.exists():
        raise SystemExit("STOP_OUTPUT_COLLISION")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(canonical(raw) + "\n", encoding="utf-8")
    print(json.dumps({
        "rows": len(raw["cases"]),
        "raw_sha256": sha256_bytes(output.read_bytes()),
        "workload_sha256": raw["workload_sha256"],
        "decisions": [{"case": r["case_id"], "policy": r["policy"], "decision": r["decision"],
                       "decision_ready_ms": r["decision_ready_ms"],
                       "peak": r["metrics"]["peak_concurrency"],
                       "budget": r["metrics"]["reserved_budget_units"]}
                      for r in raw["cases"]],
    }, sort_keys=True, separators=(",", ":")))


if __name__ == "__main__":
    main()
