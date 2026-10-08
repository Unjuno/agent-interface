#!/usr/bin/env python3
"""Independent raw-only audit for synthetic parallel verifier fan-out T0."""
import copy
import hashlib
import json
import os
from pathlib import Path

POLICIES = ("SERIAL_VERIFIERS", "PARALLEL_FANOUT")
VALID = {"PENDING", "RUNNING", "COMPLETED", "TIMEOUT", "DEADLINE",
         "SKIPPED_DEADLINE", "SKIPPED_BUDGET", "SKIPPED_DEPENDENCY",
         "CANCELLED_AFTER_FAIL", "CANCELLED_AFTER_DECISION"}


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def sha256_bytes(data):
    return hashlib.sha256(data).hexdigest()


def independent_digest(spec):
    projection = {
        "job_id": spec["job_id"],
        "input_sha256": spec["input_sha256"],
        "source_version": "plan-v1",
        "verifier_id": "stub-v1",
        "verifier_version": "1.0",
        "outcome": spec["outcome"],
    }
    return sha256_bytes(canonical(projection).encode("utf-8"))


def peak_and_slots(jobs):
    intervals = []
    for job in jobs:
        if job.get("start_ms") is not None:
            intervals.append((job["start_ms"], job["finish_ms"], job["worker_id"], job["job_id"]))
    points = []
    for start, end, worker, jid in intervals:
        points.append((start, 1, worker, jid))
        points.append((end, -1, worker, jid))
    live = peak = 0
    slot_intervals = {}
    for start, end, worker, jid in intervals:
        slot_intervals.setdefault(worker, []).append((start, end, jid))
    overlap = []
    for worker, spans in slot_intervals.items():
        spans.sort()
        for left, right in zip(spans, spans[1:]):
            if right[0] < left[1]:
                overlap.append(worker)
    for _, delta, _, _ in sorted(points, key=lambda x: (x[0], x[1])):
        live += delta
        peak = max(peak, live)
    return peak, overlap, intervals


def audit(raw, workloads):
    errors = []

    def fail(code, cid=None, policy=None, jid=None):
        errors.append({"code": code, "case_id": cid, "policy": policy, "job_id": jid})

    if not isinstance(raw, dict) or raw.get("schema") != "parallel-fanout-t0-v1":
        return [{"code": "RAW_SCHEMA", "case_id": None, "policy": None, "job_id": None}]
    expected_input = sha256_bytes(canonical(workloads).encode("utf-8"))
    if raw.get("workload_sha256") != expected_input:
        fail("WORKLOAD_HASH")
    expected = {(c["case_id"], p) for c in workloads["cases"] for p in POLICIES}
    rows = raw.get("cases")
    if not isinstance(rows, list):
        return [{"code": "ROWS_NOT_LIST", "case_id": None, "policy": None, "job_id": None}]
    actual = [(r.get("case_id"), r.get("policy")) for r in rows if isinstance(r, dict)]
    if len(actual) != len(rows) or len(set(actual)) != len(actual):
        fail("ROW_SHAPE_OR_DUPLICATE")
    if set(actual) != expected:
        fail("CASE_POLICY_MATRIX")
    case_map = {c["case_id"]: c for c in workloads["cases"]}
    by_case = {}

    for row in rows:
        if not isinstance(row, dict):
            continue
        cid, policy = row.get("case_id"), row.get("policy")
        by_case.setdefault(cid, {})[policy] = row
        case = case_map.get(cid)
        if case is None or policy not in POLICIES:
            fail("UNKNOWN_CASE_POLICY", cid, policy)
            continue
        cap = workloads["config"]["serial_workers"] if policy == "SERIAL_VERIFIERS" else workloads["config"]["max_parallel_workers"]
        expected_ids = {j["job_id"] for j in case["jobs"]}
        job_rows = row.get("jobs")
        if not isinstance(job_rows, list):
            fail("JOBS_NOT_LIST", cid, policy)
            continue
        job_map = {j.get("job_id"): j for j in job_rows if isinstance(j, dict)}
        if len(job_map) != len(job_rows) or set(job_map) != expected_ids:
            fail("JOB_SET", cid, policy)
        specs = {j["job_id"]: j for j in case["jobs"]}

        started_cost = 0
        for jid, spec in specs.items():
            got = job_map.get(jid)
            if got is None:
                continue
            status = got.get("status")
            if status not in VALID or status in {"PENDING", "RUNNING"}:
                fail("NONTERMINAL_STATUS", cid, policy, jid)
            started = got.get("start_ms")
            finished = got.get("finish_ms")
            elapsed = got.get("elapsed_ms")
            if started is None:
                if got.get("worker_id") is not None or elapsed != 0:
                    fail("UNSTARTED_FIELDS", cid, policy, jid)
            else:
                if not all(isinstance(x, int) and x >= 0 for x in (started, finished, elapsed)):
                    fail("TIME_FIELDS", cid, policy, jid)
                    continue
                if finished - started != elapsed:
                    fail("ELAPSED_MISMATCH", cid, policy, jid)
                started_cost += spec["cost_units"]
                if got.get("cost_units") != spec["cost_units"]:
                    fail("COST_IDENTITY", cid, policy, jid)
                deadline = min(case["deadline_ms"], spec.get("job_deadline_ms", case["deadline_ms"]))
                if status == "COMPLETED":
                    if finished >= deadline:
                        fail("COMPLETED_AT_OR_AFTER_DEADLINE", cid, policy, jid)
                    if finished - started != got.get("effective_service_ms"):
                        fail("SERVICE_INTERVAL", cid, policy, jid)
                    if spec.get("timeout_ms") is not None and finished - started >= spec["timeout_ms"]:
                        fail("COMPLETED_AFTER_TIMEOUT", cid, policy, jid)
                    if got.get("outcome") != spec["outcome"]:
                        fail("VERIFIER_OUTPUT", cid, policy, jid)
                    if got.get("result_sha256") != independent_digest(spec):
                        fail("RESULT_DIGEST", cid, policy, jid)
                elif status == "TIMEOUT":
                    if spec.get("timeout_ms") is None or finished != started + spec["timeout_ms"] or got.get("outcome") != "UNKNOWN":
                        fail("TIMEOUT_BOUNDARY", cid, policy, jid)
                elif status == "DEADLINE":
                    if finished != deadline or got.get("outcome") != "UNKNOWN":
                        fail("DEADLINE_BOUNDARY", cid, policy, jid)
                elif status in {"SKIPPED_DEADLINE", "SKIPPED_BUDGET", "SKIPPED_DEPENDENCY"}:
                    if started is not None or got.get("outcome") is not None:
                        fail("SKIP_HAS_EXECUTION", cid, policy, jid)
                elif status in {"CANCELLED_AFTER_FAIL", "CANCELLED_AFTER_DECISION"}:
                    if got.get("outcome") is not None:
                        fail("CANCEL_HAS_OUTCOME", cid, policy, jid)

            if status == "SKIPPED_DEPENDENCY":
                deps = spec["dependencies"]
                if not deps or not any(job_map.get(d, {}).get("outcome") != "PASS" for d in deps):
                    fail("INVALID_DEPENDENCY_SKIP", cid, policy, jid)
            if started is not None:
                for dep in spec["dependencies"]:
                    drow = job_map.get(dep, {})
                    if drow.get("status") != "COMPLETED" or drow.get("outcome") != "PASS" or drow.get("finish_ms") > started:
                        fail("DEPENDENCY_ORDER", cid, policy, jid)

        if started_cost > case["budget_units"]:
            fail("BUDGET_OVERRUN", cid, policy)
        metrics = row.get("metrics", {})
        if metrics.get("reserved_budget_units") != started_cost or metrics.get("budget_limit_units") != case["budget_units"]:
            fail("BUDGET_ACCOUNTING", cid, policy)
        peak, overlap, intervals = peak_and_slots(job_rows)
        if peak > cap or metrics.get("peak_concurrency") != peak:
            fail("WORKER_CAP_OR_PEAK", cid, policy)
        if overlap:
            fail("WORKER_SLOT_OVERLAP", cid, policy)
        expected_decision = case["expected_decision"]
        mandatory = [job_map.get(j["job_id"], {}) for j in case["jobs"] if j["required"]]
        if any(j.get("outcome") == "FAIL" for j in mandatory):
            decision = "FAIL"
            ready = min(j["finish_ms"] for j in mandatory if j.get("outcome") == "FAIL")
        else:
            decision = "PASS" if all(j.get("status") == "COMPLETED" and j.get("outcome") == "PASS" for j in mandatory) else "UNCERTAIN"
            ready = max((j.get("finish_ms") or 0) for j in mandatory)
        if row.get("decision") != decision or decision != expected_decision:
            fail("TYPED_DECISION", cid, policy)
        if row.get("decision_ready_ms") != ready:
            fail("DECISION_READY_TIME", cid, policy)
        if decision == "PASS" and any(j.get("status") != "COMPLETED" or j.get("outcome") != "PASS" for j in mandatory):
            fail("MANDATORY_MISSING_ON_PASS", cid, policy)
        if decision == "FAIL":
            fail_time = ready
            for job in job_rows:
                if job.get("start_ms") is not None and job.get("finish_ms", 0) > fail_time:
                    fail("WORK_AFTER_DECISIVE_FAIL", cid, policy, job.get("job_id"))

    for cid in case_map:
        pair = by_case.get(cid, {})
        if set(pair) != set(POLICIES):
            continue
        if pair["SERIAL_VERIFIERS"].get("decision") != pair["PARALLEL_FANOUT"].get("decision"):
            fail("POLICY_DECISION_DIVERGENCE", cid)
        sm = {j["job_id"]: j for j in pair["SERIAL_VERIFIERS"].get("jobs", [])}
        pm = {j["job_id"]: j for j in pair["PARALLEL_FANOUT"].get("jobs", [])}
        for jid in set(sm) & set(pm):
            if sm[jid].get("result_sha256") and pm[jid].get("result_sha256") and sm[jid]["result_sha256"] != pm[jid]["result_sha256"]:
                fail("SEMANTIC_DIGEST_DIVERGENCE", cid, None, jid)

    indep = by_case.get("independent", {})
    if set(indep) == set(POLICIES):
        serial_ms = indep["SERIAL_VERIFIERS"].get("decision_ready_ms")
        parallel_ms = indep["PARALLEL_FANOUT"].get("decision_ready_ms")
        if not isinstance(serial_ms, int) or not isinstance(parallel_ms, int) or parallel_ms * 4 > serial_ms * 3:
            fail("PRIMARY_LATENCY_GATE", "independent")
    return errors


def corruption_controls(raw, workloads):
    mutations = []
    x = copy.deepcopy(raw); x["cases"].pop(); mutations.append(("missing_row", x))
    x = copy.deepcopy(raw)
    x["cases"][0]["decision"] = "FAIL" if x["cases"][0]["decision"] != "FAIL" else "PASS"
    mutations.append(("altered_decision", x))
    x = copy.deepcopy(raw); x["cases"][0]["metrics"]["reserved_budget_units"] += 1; mutations.append(("budget_accounting", x))
    x = copy.deepcopy(raw); x["cases"][0]["jobs"][0]["result_sha256"] = "0" * 64; mutations.append(("forged_digest", x))
    x = copy.deepcopy(raw); x["cases"][0]["metrics"]["peak_concurrency"] = 99; mutations.append(("worker_cap", x))
    x = copy.deepcopy(raw)
    complete = next((j for j in x["cases"][0]["jobs"] if j.get("status") == "COMPLETED"), None)
    if complete:
        complete["finish_ms"] = workloads["cases"][0]["deadline_ms"] + 1
    mutations.append(("late_completion", x))
    results = []
    for name, candidate in mutations:
        errs = audit(candidate, workloads)
        results.append({"name": name, "rejected": bool(errs), "errors": len(errs)})
    return results


def main():
    workloads = json.loads(Path(__file__).with_name("workloads.json").read_text(encoding="utf-8"))
    raw_path = Path(os.environ["RAW_PATH"])
    raw = json.loads(raw_path.read_text(encoding="utf-8"))
    errors = audit(raw, workloads)
    controls = corruption_controls(raw, workloads)
    result = {"errors": errors, "error_count": len(errors), "corruption_controls": controls,
              "corruptions_rejected": sum(x["rejected"] for x in controls),
              "raw_sha256": sha256_bytes(raw_path.read_bytes())}
    print(canonical(result))
    if errors or result["corruptions_rejected"] != len(controls):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
