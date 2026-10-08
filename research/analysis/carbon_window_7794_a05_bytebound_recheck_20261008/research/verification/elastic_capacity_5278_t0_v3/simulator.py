#!/usr/bin/env python3
"""Deterministic synthetic replica-capacity simulator for Issue #5278 T0."""
import base64
import hashlib
import json
import os
from pathlib import Path
import sys

POLICIES = ("FIXED_SMALL", "FIXED_LARGE", "ELASTIC_DEADLINE_FRESHNESS_AWARE")
SIM_VERSION = "elastic-capacity-t0-v1"


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def sha256_bytes(value):
    return hashlib.sha256(value).hexdigest()


def semantic_digest(job, verifier):
    payload = {
        "job_id": job["job_id"],
        "required_version": job["required_version"],
        "payload_sha256": job["payload_sha256"],
        "verifier_id": verifier["verifier_id"],
        "verifier_version": verifier["version"],
        "authority": "none",
    }
    return sha256_bytes(canonical(payload).encode("utf-8"))


def priority(job):
    return (0 if job["criticality"] == "MANDATORY" else 1,
            job["deadline_ms"], job["arrival_ms"], job["job_id"])


class Simulation:
    def __init__(self, case, policy, config, verifier):
        self.case = case
        self.policy = policy
        self.config = config
        self.verifier = verifier
        self.now = 0
        self.version = case["initial_version"]
        self.jobs = {j["job_id"]: dict(j, status="PENDING", worker_id=None,
                    start_ms=None, finish_ms=None, wait_ms=None,
                    result_sha256=None) for j in case["jobs"]}
        self.queue = []
        self.workers = []
        self.next_worker_id = 1
        self.attempts = []
        self.capacity_events = []
        self.counters = {
            "worker_ms": 0, "busy_ms": 0, "idle_ms": 0,
            "startup_count": 0, "startup_ms": 0,
            "teardown_count": 0, "teardown_ms": 0,
            "stale_before_start": 0, "infeasible_before_start": 0,
            "deadline_before_start": 0, "stale_active": 0,
            "deadline_active": 0, "horizon_active": 0,
        }
        self.peak_workers = 0
        self.invalidation_at = {}
        for change in case["invalidations"]:
            self.invalidation_at.setdefault(change["at_ms"], []).append(change["new_version"])
        self.arrivals_at = {}
        for job in case["jobs"]:
            self.arrivals_at.setdefault(job["arrival_ms"], []).append(job["job_id"])
        initial = 4 if policy == "FIXED_LARGE" else 1
        for _ in range(initial):
            self.spawn(0)

    def active_workers(self):
        return [w for w in self.workers if w["state"] != "STOPPED"]

    def spawn(self, at_ms):
        w = {"worker_id": self.next_worker_id, "state": "STARTING",
             "start_ms": at_ms, "ready_ms": at_ms + self.config["startup_ms"],
             "stop_start_ms": None, "stop_ms": None, "end_ms": None,
             "idle_since_ms": None, "job_id": None, "job_end_ms": None}
        self.next_worker_id += 1
        self.workers.append(w)
        self.counters["startup_count"] += 1
        self.counters["startup_ms"] += self.config["startup_ms"]
        self.capacity_events.append({"at_ms": at_ms, "kind": "START",
                                     "worker_id": w["worker_id"]})
        self.peak_workers = max(self.peak_workers, len(self.active_workers()))

    def set_idle(self, w, at_ms):
        w["state"] = "IDLE"
        w["idle_since_ms"] = at_ms
        w["job_id"] = None
        w["job_end_ms"] = None

    def finish_attempt(self, w, at_ms, reason):
        job = self.jobs[w["job_id"]]
        self.attempts.append({"job_id": job["job_id"], "worker_id": w["worker_id"],
                              "start_ms": job["start_ms"], "end_ms": at_ms,
                              "reason": reason})
        job["finish_ms"] = at_ms
        if reason == "COMPLETED":
            job["status"] = "COMPLETED"
            job["result_sha256"] = semantic_digest(job, self.verifier)
        else:
            job["status"] = reason
            if reason == "STALE_ACTIVE":
                self.counters["stale_active"] += 1
            elif reason == "DEADLINE_ACTIVE":
                self.counters["deadline_active"] += 1
            elif reason == "HORIZON_ACTIVE":
                self.counters["horizon_active"] += 1
        self.set_idle(w, at_ms)

    def current_version_at(self, at_ms):
        version = self.case["initial_version"]
        for change in self.case["invalidations"]:
            if change["at_ms"] <= at_ms:
                version = change["new_version"]
        return version

    def earliest_slots(self, at_ms):
        slots = []
        for w in self.active_workers():
            if w["state"] == "IDLE":
                slots.append(at_ms)
            elif w["state"] == "STARTING":
                slots.append(max(at_ms, w["ready_ms"]))
            elif w["state"] == "BUSY":
                slots.append(max(at_ms, w["job_end_ms"]))
            elif w["state"] == "STOPPING":
                slots.append(max(at_ms, w["stop_ms"]) + self.config["startup_ms"])
        if self.policy == "ELASTIC_DEADLINE_FRESHNESS_AWARE":
            spare = self.config["max_workers"] - len(self.active_workers())
            slots.extend([at_ms + self.config["startup_ms"]] * max(0, spare))
        return sorted(slots)

    def reject_queue(self, at_ms):
        survivors = []
        ordered = sorted(self.queue, key=lambda jid: priority(self.jobs[jid]))
        slots = self.earliest_slots(at_ms)
        for jid in ordered:
            job = self.jobs[jid]
            if job["required_version"] != self.version:
                job["status"] = "STALE_BEFORE_START"
                job["finish_ms"] = at_ms
                self.counters["stale_before_start"] += 1
                continue
            if at_ms > job["deadline_ms"]:
                job["status"] = "DEADLINE_BEFORE_START"
                job["finish_ms"] = at_ms
                self.counters["deadline_before_start"] += 1
                continue
            if not slots:
                # No capacity can become available within the frozen envelope.
                job["status"] = "INFEASIBLE_BEFORE_START"
                job["finish_ms"] = at_ms
                self.counters["infeasible_before_start"] += 1
                continue
            slot = slots.pop(0)
            completion = max(at_ms, slot) + job["service_ms"]
            if completion > job["deadline_ms"]:
                job["status"] = "INFEASIBLE_BEFORE_START"
                self.counters["infeasible_before_start"] += 1
                continue
            slots.append(completion)
            slots.sort()
            survivors.append(jid)
        self.queue = survivors

    def scale_out(self, at_ms):
        if self.policy != "ELASTIC_DEADLINE_FRESHNESS_AWARE":
            return
        idle_ready = sum(w["state"] == "IDLE" for w in self.active_workers())
        demand_after_idle = max(0, len(self.queue) - idle_ready)
        while demand_after_idle > 0 and len(self.active_workers()) < self.config["max_workers"]:
            self.spawn(at_ms)
            demand_after_idle -= 1

    def dispatch(self, at_ms):
        for w in self.active_workers():
            if w["state"] != "IDLE" or not self.queue:
                continue
            self.queue.sort(key=lambda jid: priority(self.jobs[jid]))
            jid = self.queue.pop(0)
            job = self.jobs[jid]
            job["status"] = "RUNNING"
            job["worker_id"] = w["worker_id"]
            job["start_ms"] = at_ms
            job["wait_ms"] = at_ms - job["arrival_ms"]
            w["state"] = "BUSY"
            w["idle_since_ms"] = None
            w["job_id"] = jid
            w["job_end_ms"] = at_ms + job["service_ms"]

    def scale_in(self, at_ms):
        if self.policy != "ELASTIC_DEADLINE_FRESHNESS_AWARE" or self.queue:
            return
        for w in self.active_workers():
            if (w["worker_id"] > 1 and w["state"] == "IDLE"
                    and at_ms - w["idle_since_ms"] >= self.config["idle_timeout_ms"]):
                w["state"] = "STOPPING"
                w["stop_start_ms"] = at_ms
                w["stop_ms"] = at_ms + self.config["teardown_ms"]
                self.counters["teardown_count"] += 1
                self.capacity_events.append({"at_ms": at_ms, "kind": "STOPPING",
                                             "worker_id": w["worker_id"]})

    def run(self):
        horizon = self.case["horizon_ms"]
        for at_ms in range(horizon + 1):
            self.now = at_ms
            for new_version in self.invalidation_at.get(at_ms, []):
                self.version = new_version
                for w in self.active_workers():
                    if w["state"] == "BUSY":
                        j = self.jobs[w["job_id"]]
                        if j["required_version"] != self.version:
                            self.finish_attempt(w, at_ms, "STALE_ACTIVE")
            for w in self.active_workers():
                if w["state"] == "BUSY":
                    j = self.jobs[w["job_id"]]
                    if at_ms >= w["job_end_ms"]:
                        if j["required_version"] == self.version and at_ms <= j["deadline_ms"]:
                            self.finish_attempt(w, at_ms, "COMPLETED")
                        elif j["required_version"] != self.version:
                            self.finish_attempt(w, at_ms, "STALE_ACTIVE")
                        else:
                            self.finish_attempt(w, at_ms, "DEADLINE_ACTIVE")
                    elif at_ms >= j["deadline_ms"]:
                        self.finish_attempt(w, at_ms, "DEADLINE_ACTIVE")
            for w in self.active_workers():
                if w["state"] == "STARTING" and at_ms >= w["ready_ms"]:
                    self.set_idle(w, at_ms)
                    self.capacity_events.append({"at_ms": at_ms, "kind": "READY",
                                                 "worker_id": w["worker_id"]})
                elif w["state"] == "STOPPING" and at_ms >= w["stop_ms"]:
                    w["state"] = "STOPPED"
                    w["end_ms"] = at_ms
                    self.counters["teardown_ms"] += self.config["teardown_ms"]
                    self.capacity_events.append({"at_ms": at_ms, "kind": "STOPPED",
                                                 "worker_id": w["worker_id"]})
            for jid in self.arrivals_at.get(at_ms, []):
                self.jobs[jid]["status"] = "QUEUED"
                self.queue.append(jid)
            self.reject_queue(at_ms)
            self.scale_out(at_ms)
            self.dispatch(at_ms)
            self.scale_in(at_ms)
            self.peak_workers = max(self.peak_workers, len(self.active_workers()))
            if at_ms == horizon:
                break
            for w in self.active_workers():
                self.counters["worker_ms"] += 1
                if w["state"] == "BUSY":
                    self.counters["busy_ms"] += 1
                else:
                    self.counters["idle_ms"] += 1
        for w in self.active_workers():
            if w["state"] == "BUSY":
                self.finish_attempt(w, horizon, "HORIZON_ACTIVE")
            if w["state"] == "STOPPING" and w["stop_start_ms"] is not None:
                elapsed = max(0, min(horizon, w["stop_ms"]) - w["stop_start_ms"])
                self.counters["teardown_ms"] += elapsed
            w["end_ms"] = horizon
        for jid in self.queue:
            self.jobs[jid]["status"] = "HORIZON_QUEUED"
        self.queue = []
        for job in self.jobs.values():
            if job["status"] in ("PENDING", "QUEUED", "RUNNING"):
                job["status"] = "HORIZON_QUEUED"
        mandatory = [j for j in self.jobs.values() if j["criticality"] == "MANDATORY"]
        outcome = "PASS" if mandatory and all(j["status"] == "COMPLETED" for j in mandatory) else "UNCERTAIN"
        misses = sum(j["criticality"] == "MANDATORY" and j["status"] != "COMPLETED"
                     for j in self.jobs.values())
        waits = [j["wait_ms"] for j in self.jobs.values() if j["wait_ms"] is not None]
        metrics = dict(self.counters)
        metrics.update({
            "completed": sum(j["status"] == "COMPLETED" for j in self.jobs.values()),
            "mandatory_deadline_or_freshness_misses": misses,
            "stale_or_infeasible_before_execution": (
                self.counters["stale_before_start"] + self.counters["infeasible_before_start"]
                + self.counters["deadline_before_start"]),
            "wasted_compute_ms": sum(a["end_ms"] - a["start_ms"] for a in self.attempts
                                     if a["reason"] != "COMPLETED"),
            "peak_workers": self.peak_workers,
            "capacity_changes": len(self.capacity_events),
            "queue_age_max_ms": max(waits, default=0),
            "utilization": (self.counters["busy_ms"] / self.counters["worker_ms"]
                            if self.counters["worker_ms"] else 0.0),
        })
        return {
            "case_id": self.case["case_id"], "policy": self.policy,
            "plan_outcome": outcome,
            "jobs": sorted(self.jobs.values(), key=lambda j: j["job_id"]),
            "attempts": sorted(self.attempts, key=lambda a: (a["start_ms"], a["job_id"])),
            "capacity_events": sorted(self.capacity_events, key=lambda e: (e["at_ms"], e["kind"], e["worker_id"])),
            "workers": sorted(self.workers, key=lambda w: w["worker_id"]),
            "metrics": metrics,
        }


def load_workloads():
    encoded = os.environ.get("WORKLOADS_B64")
    if encoded:
        return json.loads(base64.b64decode(encoded))
    return json.loads(Path(__file__).with_name("workloads.json").read_text(encoding="utf-8"))


def run_all(workloads):
    rows = []
    for case in workloads["cases"]:
        for policy in POLICIES:
            rows.append(Simulation(case, policy, workloads["config"], workloads["verifier"]).run())
    return {
        "schema": SIM_VERSION,
        "workload_sha256": sha256_bytes(canonical(workloads).encode("utf-8")),
        "config": workloads["config"],
        "verifier": workloads["verifier"],
        "cases": rows,
    }


def main():
    workloads = load_workloads()
    raw = run_all(workloads)
    out = Path(os.environ["RAW_OUT"])
    if out.exists():
        raise SystemExit("STOP_OUTPUT_COLLISION")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(canonical(raw) + "\n", encoding="utf-8")
    compact = [{
        "case": r["case_id"], "policy": r["policy"],
        "completed": r["metrics"]["completed"],
        "mandatory_misses": r["metrics"]["mandatory_deadline_or_freshness_misses"],
        "worker_ms": r["metrics"]["worker_ms"], "idle_ms": r["metrics"]["idle_ms"],
        "busy_ms": r["metrics"]["busy_ms"], "stale_pre": r["metrics"]["stale_before_start"],
        "infeasible_pre": r["metrics"]["infeasible_before_start"],
        "wasted_compute_ms": r["metrics"]["wasted_compute_ms"],
        "peak": r["metrics"]["peak_workers"], "outcome": r["plan_outcome"],
    } for r in raw["cases"]]
    print(json.dumps({"raw_path": str(out), "raw_sha256": sha256_bytes(out.read_bytes()),
                      "workload_sha256": raw["workload_sha256"], "rows": compact},
                     sort_keys=True, separators=(",", ":")))


if __name__ == "__main__":
    main()
