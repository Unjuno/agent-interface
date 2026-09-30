#!/usr/bin/env python3
"""Independent trace/result auditor for Issue #5278 synthetic T0."""
import base64
import copy
import hashlib
import json
import os
from pathlib import Path
import sys

POLICIES = ("FIXED_SMALL", "FIXED_LARGE", "ELASTIC_DEADLINE_FRESHNESS_AWARE")


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def sha256_bytes(value):
    return hashlib.sha256(value).hexdigest()


def semantic_digest(job, verifier):
    # Deliberately restated here; this auditor imports no simulator code.
    projection = {
        "job_id": job["job_id"],
        "required_version": job["required_version"],
        "payload_sha256": job["payload_sha256"],
        "verifier_id": verifier["verifier_id"],
        "verifier_version": verifier["version"],
        "authority": "none",
    }
    return sha256_bytes(canonical(projection).encode("utf-8"))


def version_at(case, at_ms):
    current = case["initial_version"]
    for change in case["invalidations"]:
        if change["at_ms"] <= at_ms:
            current = change["new_version"]
    return current


def peak_concurrency(workers):
    points = []
    for worker in workers:
        points.append((worker["start_ms"], 1))
        points.append((worker["end_ms"], -1))
    live = peak = 0
    for _, delta in sorted(points, key=lambda p: (p[0], p[1])):
        live += delta
        peak = max(peak, live)
    return peak


def audit(raw, workloads):
    errors = []

    def fail(code, case_id=None, policy=None, subject=None):
        errors.append({"code": code, "case_id": case_id, "policy": policy,
                       "subject": subject})

    expected_hash = sha256_bytes(canonical(workloads).encode("utf-8"))
    if raw.get("schema") != "elastic-capacity-t0-v1":
        fail("RAW_SCHEMA")
    if raw.get("workload_sha256") != expected_hash:
        fail("WORKLOAD_HASH")
    expected_keys = {(c["case_id"], p) for c in workloads["cases"] for p in POLICIES}
    rows = raw.get("cases")
    if not isinstance(rows, list):
        return [{"code": "ROWS_NOT_LIST", "case_id": None, "policy": None, "subject": None}]
    actual_keys = [(r.get("case_id"), r.get("policy")) for r in rows if isinstance(r, dict)]
    if len(actual_keys) != len(rows) or len(actual_keys) != len(set(actual_keys)):
        fail("DUPLICATE_OR_MALFORMED_CASE_ROWS")
    if set(actual_keys) != expected_keys:
        fail("CASE_POLICY_SET")
    case_inputs = {c["case_id"]: c for c in workloads["cases"]}
    audited = {}
    max_workers = workloads["config"]["max_workers"]
    startup_ms = workloads["config"]["startup_ms"]
    teardown_ms = workloads["config"]["teardown_ms"]

    for row in rows:
        if not isinstance(row, dict):
            continue
        cid, policy = row.get("case_id"), row.get("policy")
        case = case_inputs.get(cid)
        if case is None or policy not in POLICIES:
            fail("UNKNOWN_CASE_OR_POLICY", cid, policy)
            continue
        jobs_in = {j["job_id"]: j for j in case["jobs"]}
        job_rows = row.get("jobs", [])
        jobs_out = {j.get("job_id"): j for j in job_rows if isinstance(j, dict)}
        if len(jobs_out) != len(job_rows) or set(jobs_out) != set(jobs_in):
            fail("JOB_SET", cid, policy)
        attempts = row.get("attempts", [])
        by_job = {}
        for attempt in attempts:
            jid = attempt.get("job_id")
            by_job.setdefault(jid, []).append(attempt)
        for jid, group in by_job.items():
            if jid not in jobs_in or len(group) != 1:
                fail("ATTEMPT_CARDINALITY", cid, policy, jid)
        workers = row.get("workers", [])
        worker_map = {w.get("worker_id"): w for w in workers if isinstance(w, dict)}
        if len(worker_map) != len(workers):
            fail("WORKER_IDS", cid, policy)
        if len(workers) > max_workers or peak_concurrency(workers) > max_workers:
            fail("RESOURCE_ENVELOPE", cid, policy)
        expected_initial = 4 if policy == "FIXED_LARGE" else 1
        initial = [w for w in workers if w.get("start_ms") == 0]
        if len(initial) != expected_initial:
            fail("INITIAL_CAPACITY", cid, policy)
        if policy != "ELASTIC_DEADLINE_FRESHNESS_AWARE" and len(workers) != expected_initial:
            fail("FIXED_POLICY_SCALED", cid, policy)

        worker_attempts = {}
        worker_ms = 0
        startup_total = 0
        teardown_total = 0
        teardown_count = 0
        for worker in workers:
            wid = worker.get("worker_id")
            start, ready, end = worker.get("start_ms"), worker.get("ready_ms"), worker.get("end_ms")
            stop_start, stop_at = worker.get("stop_start_ms"), worker.get("stop_ms")
            if not all(isinstance(x, int) for x in (start, ready, end)):
                fail("WORKER_TIME_TYPE", cid, policy, wid)
                continue
            if start < 0 or ready != start + startup_ms or end < start or end > case["horizon_ms"]:
                fail("WORKER_LIFETIME", cid, policy, wid)
            worker_ms += end - start
            startup_total += ready - start
            if stop_start is not None:
                teardown_count += 1
                if not isinstance(stop_at, int) or stop_at != stop_start + teardown_ms:
                    fail("TEARDOWN_TIMING", cid, policy, wid)
                teardown_total += max(0, min(case["horizon_ms"], stop_at) - stop_start)
                if end != min(case["horizon_ms"], stop_at):
                    fail("TEARDOWN_END", cid, policy, wid)
            elif stop_at is not None:
                fail("TEARDOWN_FIELDS", cid, policy, wid)
        for attempt in attempts:
            jid, wid = attempt.get("job_id"), attempt.get("worker_id")
            job = jobs_in.get(jid)
            worker = worker_map.get(wid)
            if job is None or worker is None:
                fail("ATTEMPT_REFERENCE", cid, policy, jid)
                continue
            start, end, reason = attempt.get("start_ms"), attempt.get("end_ms"), attempt.get("reason")
            if not isinstance(start, int) or not isinstance(end, int) or end < start:
                fail("ATTEMPT_TIME", cid, policy, jid)
                continue
            if start < job["arrival_ms"] or start < worker["ready_ms"] or end > worker["end_ms"]:
                fail("ATTEMPT_OUTSIDE_ADMISSION", cid, policy, jid)
            worker_attempts.setdefault(wid, []).append((start, end, jid))
            result = jobs_out.get(jid, {})
            if result.get("start_ms") != start or result.get("finish_ms") != end:
                fail("RESULT_ATTEMPT_TIME", cid, policy, jid)
            if result.get("worker_id") != wid:
                fail("RESULT_WORKER", cid, policy, jid)
            if reason == "COMPLETED":
                if end - start != job["service_ms"] or end > job["deadline_ms"]:
                    fail("COMPLETION_DURATION_OR_DEADLINE", cid, policy, jid)
                if version_at(case, end) != job["required_version"]:
                    fail("STALE_COMPLETION", cid, policy, jid)
                if result.get("status") != "COMPLETED":
                    fail("COMPLETION_STATUS", cid, policy, jid)
                if result.get("result_sha256") != semantic_digest(job, raw.get("verifier", {})):
                    fail("SEMANTIC_RESULT_HASH", cid, policy, jid)
            else:
                if result.get("status") != reason:
                    fail("CANCEL_STATUS", cid, policy, jid)
                if reason == "STALE_ACTIVE":
                    changes = [x for x in case["invalidations"]
                               if start < x["at_ms"] <= end and x["new_version"] != job["required_version"]]
                    if not changes or end != min(x["at_ms"] for x in changes):
                        fail("STALE_CANCEL_TIME", cid, policy, jid)
                elif reason == "DEADLINE_ACTIVE":
                    if end != job["deadline_ms"] or end - start >= job["service_ms"]:
                        fail("DEADLINE_CANCEL_TIME", cid, policy, jid)
                elif reason == "HORIZON_ACTIVE":
                    if end != case["horizon_ms"]:
                        fail("HORIZON_CANCEL_TIME", cid, policy, jid)
                else:
                    fail("UNKNOWN_ATTEMPT_REASON", cid, policy, jid)
        for wid, spans in worker_attempts.items():
            spans.sort()
            for prev, nxt in zip(spans, spans[1:]):
                if nxt[0] < prev[1]:
                    fail("WORKER_OVERLAP", cid, policy, wid)

        completed = 0
        mandatory_misses = 0
        waits = []
        stale_pre = infeasible_pre = deadline_pre = 0
        for jid, job in jobs_in.items():
            result = jobs_out.get(jid, {})
            status = result.get("status")
            group = by_job.get(jid, [])
            if status == "COMPLETED":
                completed += 1
                if len(group) != 1 or group[0].get("reason") != "COMPLETED":
                    fail("UNTRACED_COMPLETION", cid, policy, jid)
            elif group:
                if len(group) != 1 or group[0].get("reason") != status:
                    fail("UNTRACED_CANCELLATION", cid, policy, jid)
            elif status == "STALE_BEFORE_START":
                stale_pre += 1
                if result.get("finish_ms") is None or version_at(case, result["finish_ms"]) == job["required_version"]:
                    fail("STALE_PRECONDITION", cid, policy, jid)
            elif status == "INFEASIBLE_BEFORE_START":
                infeasible_pre += 1
            elif status == "DEADLINE_BEFORE_START":
                deadline_pre += 1
                if result.get("finish_ms") is None or result["finish_ms"] <= job["deadline_ms"]:
                    fail("DEADLINE_PRECONDITION", cid, policy, jid)
            elif status == "HORIZON_QUEUED":
                pass
            else:
                fail("UNEXPECTED_FINAL_STATUS", cid, policy, jid)
            if job["criticality"] == "MANDATORY" and status != "COMPLETED":
                mandatory_misses += 1
            if result.get("start_ms") is not None:
                expected_wait = result["start_ms"] - job["arrival_ms"]
                if result.get("wait_ms") != expected_wait:
                    fail("WAIT_METRIC", cid, policy, jid)
                waits.append(expected_wait)
            elif result.get("wait_ms") is not None:
                fail("WAIT_WITHOUT_START", cid, policy, jid)

        expected_outcome = "PASS" if any(j["criticality"] == "MANDATORY" for j in jobs_in.values()) and mandatory_misses == 0 else "UNCERTAIN"
        if row.get("plan_outcome") != expected_outcome:
            fail("MANDATORY_FAIL_CLOSED", cid, policy)

        busy_ms = sum(a["end_ms"] - a["start_ms"] for a in attempts)
        peak = peak_concurrency(workers)
        metrics = row.get("metrics", {})
        recomputed = {
            "worker_ms": worker_ms,
            "busy_ms": busy_ms,
            "idle_ms": worker_ms - busy_ms,
            "startup_count": len(workers),
            "startup_ms": startup_total,
            "teardown_count": teardown_count,
            "teardown_ms": teardown_total,
            "stale_before_start": stale_pre,
            "infeasible_before_start": infeasible_pre,
            "deadline_before_start": deadline_pre,
            "stale_active": sum(a.get("reason") == "STALE_ACTIVE" for a in attempts),
            "deadline_active": sum(a.get("reason") == "DEADLINE_ACTIVE" for a in attempts),
            "horizon_active": sum(a.get("reason") == "HORIZON_ACTIVE" for a in attempts),
            "completed": completed,
            "mandatory_deadline_or_freshness_misses": mandatory_misses,
            "stale_or_infeasible_before_execution": stale_pre + infeasible_pre + deadline_pre,
            "wasted_compute_ms": sum(a["end_ms"] - a["start_ms"] for a in attempts
                                     if a.get("reason") != "COMPLETED"),
            "peak_workers": peak,
            "capacity_changes": len(row.get("capacity_events", [])),
            "queue_age_max_ms": max(waits, default=0),
        }
        recomputed["utilization"] = busy_ms / worker_ms if worker_ms else 0.0
        for key, expected in recomputed.items():
            observed = metrics.get(key)
            if isinstance(expected, float):
                equal = isinstance(observed, (float, int)) and abs(observed - expected) < 1e-12
            else:
                equal = observed == expected
            if not equal:
                fail("METRIC_MISMATCH:" + key, cid, policy)
        audited[(cid, policy)] = row

    for case in workloads["cases"]:
        outputs = {}
        for policy in POLICIES:
            row = audited.get((case["case_id"], policy))
            if row:
                outputs[policy] = {j["job_id"]: j.get("result_sha256")
                                   for j in row.get("jobs", []) if j.get("status") == "COMPLETED"}
        ids = set().union(*(set(v) for v in outputs.values())) if outputs else set()
        for jid in ids:
            digests = {outputs[p][jid] for p in outputs if jid in outputs[p]}
            if len(digests) > 1:
                fail("CROSS_POLICY_SEMANTIC_DIVERGENCE", case["case_id"], None, jid)
    return errors


def corruption_controls(raw, workloads):
    controls = []

    def record(name, change):
        candidate = copy.deepcopy(raw)
        change(candidate)
        errs = audit(candidate, workloads)
        controls.append({"name": name, "rejected": bool(errs), "errors": len(errs)})

    def remove_job(doc):
        doc["cases"][0]["jobs"].pop()
    def alter_digest(doc):
        row = next(r for r in doc["cases"] if r["case_id"] == "short_burst" and r["policy"] == "ELASTIC_DEADLINE_FRESHNESS_AWARE")
        job = next(j for j in row["jobs"] if j["status"] == "COMPLETED")
        job["result_sha256"] = "0" * 64
    def forge_untraced_completion(doc):
        row = next(r for r in doc["cases"] if r["case_id"] == "startup_too_late" and r["policy"] == "FIXED_SMALL")
        job = row["jobs"][0]
        job["status"] = "COMPLETED"
        job["result_sha256"] = "0" * 64
    def corrupt_resource_metric(doc):
        doc["cases"][0]["metrics"]["worker_ms"] += 1
    def forge_mandatory_pass(doc):
        row = next(r for r in doc["cases"] if r["case_id"] == "startup_too_late" and r["policy"] == "FIXED_SMALL")
        row["plan_outcome"] = "PASS"

    for name, fn in [
        ("missing_job_row", remove_job),
        ("forged_semantic_digest", alter_digest),
        ("untraced_completion", forge_untraced_completion),
        ("resource_conservation", corrupt_resource_metric),
        ("mandatory_fail_closed", forge_mandatory_pass),
    ]:
        record(name, fn)
    return controls


def load_workloads():
    encoded = os.environ.get("WORKLOADS_B64")
    if encoded:
        return json.loads(base64.b64decode(encoded))
    return json.loads(Path(__file__).with_name("workloads.json").read_text(encoding="utf-8"))


def main():
    workloads = load_workloads()
    raw = json.loads(Path(os.environ["RAW_PATH"]).read_text(encoding="utf-8"))
    errors = audit(raw, workloads)
    controls = corruption_controls(raw, workloads)
    report = {"errors": errors, "error_count": len(errors), "corruptions": controls,
              "corruptions_rejected": sum(x["rejected"] for x in controls),
              "raw_sha256": sha256_bytes(Path(os.environ["RAW_PATH"]).read_bytes())}
    print(canonical(report))
    if errors or report["corruptions_rejected"] != 5:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
