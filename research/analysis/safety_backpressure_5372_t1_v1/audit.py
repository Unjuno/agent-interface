#!/usr/bin/env python3
"""Independent event-log auditor for Issue #5372 T1; no candidate imports."""
from __future__ import annotations

import hashlib
import json
import math
import sys
from collections import defaultdict
from pathlib import Path


HERE = Path(__file__).resolve().parent


def digest_config(config: dict) -> str:
    return hashlib.sha256(json.dumps(config, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def p95(values: list[int]) -> int | None:
    if not values:
        return None
    return values[math.ceil(.95 * len(values)) - 1]


def audit(records: list[dict]) -> list[str]:
    errors: list[str] = []
    def fail(message: str) -> None:
        errors.append(message)

    if not records or records[0].get("type") != "freeze":
        return ["missing initial freeze"]
    freeze = records[0]
    config = freeze.get("config", {})
    if digest_config(config) != freeze.get("config_sha256"):
        fail("freeze config digest mismatch")
    expected_scenarios = [f"{mode}-{load}-{speed}-{policy}"
                          for mode_load in config.get("scenario_order", [])
                          for mode, load in [mode_load.split(":", 1)]
                          for speed in config.get("speed_order", [])
                          for policy in config.get("policy_order", [])]
    groups: dict[str, list[dict]] = defaultdict(list)
    for row in records[1:]:
        if row.get("type") == "freeze":
            fail("duplicate freeze record")
        sid = row.get("scenario_id")
        if not sid:
            fail("record missing scenario_id")
        else:
            groups[sid].append(row)
    if list(groups) != expected_scenarios:
        fail("scenario matrix/order mismatch")

    for sid in expected_scenarios:
        rows = groups.get(sid, [])
        if not rows:
            continue
        meta = rows[0]
        if meta.get("type") != "scenario" or meta.get("config_sha256") != freeze.get("config_sha256"):
            fail(f"{sid}: invalid scenario header")
            continue
        mode, load, speed, policy = sid.split("-")
        if (meta.get("mode"), meta.get("offered_load"), meta.get("speed"), meta.get("policy")) != (mode, load, speed, policy):
            fail(f"{sid}: header key mismatch")
        events = rows[:-1]
        summary_rows = [r for r in rows if r.get("type") == "summary"]
        if len(summary_rows) != 1 or rows[-1].get("type") != "summary":
            fail(f"{sid}: missing/duplicate terminal summary")
            continue
        summary = summary_rows[0]
        if [r.get("seq") for r in rows] != list(range(len(rows))):
            fail(f"{sid}: sequence not contiguous")
        if events[0] != meta:
            fail(f"{sid}: event header ordering invalid")

        by_type: dict[str, list[dict]] = defaultdict(list)
        for row in events:
            by_type[row.get("type", "")].append(row)
        offers = {r["task_id"]: r for r in by_type["task_offer"]}
        if len(offers) != len(by_type["task_offer"]):
            fail(f"{sid}: duplicate task offer")
        fixed = mode == "fixed"
        if fixed:
            spec = config["fixed_loads"][load]
            expected_offer_ids = [f"T{i:03d}" for i in range(spec["count"])]
            expected_ticks = [i * spec["arrival_stride"] if load != "high" else i * 4 // 3
                              for i in range(spec["count"])]
            if list(offers) != expected_offer_ids or [offers[k]["tick"] for k in expected_offer_ids] != expected_ticks:
                fail(f"{sid}: fixed source schedule mismatch")
        elif not offers or "C000" not in offers:
            fail(f"{sid}: closed-loop seed missing")
        if any(r.get("task_class") != ("low" if int(r["task_id"][1:]) % 2 == 0 else "high") for r in offers.values()):
            fail(f"{sid}: task class assignment mismatch")
        expected_safety_ticks = list(range(0, config["horizon"], config["safety_stride_ticks"]))
        observed_safety_ticks = [r["tick"] for r in by_type["safety_release"]]
        if observed_safety_ticks != expected_safety_ticks:
            fail(f"{sid}: safety release schedule mismatch")

        starts = by_type["action_start"]
        dones = by_type["action_done"]
        start_map = {(r["task_id"], r["attempt"]): r for r in starts}
        done_map = {(r["task_id"], r["attempt"]): r for r in dones}
        if len(start_map) != len(starts) or len(done_map) != len(dones) or set(start_map) != set(done_map):
            fail(f"{sid}: action start/done cardinality mismatch")
        for key, start in start_map.items():
            done = done_map.get(key)
            if done and (done["tick"] - start["tick"] != config["action_ticks"][speed]
                         or start["local_ticks"] != config["action_ticks"][speed]):
                fail(f"{sid}: local action duration mismatch {key}")
        if any(start["tick"] < offers.get(start["task_id"], {}).get("tick", 10**9)
               for start in starts if start.get("attempt") == 0):
            fail(f"{sid}: primary action precedes task offer")

        enqueues = by_type["verify_enqueue"]
        enqueue_map = {(r["task_id"], r["attempt"]): r for r in enqueues}
        if len(enqueue_map) != len(enqueues) or set(enqueue_map) != set(done_map):
            fail(f"{sid}: action-to-verifier enqueue mismatch")
        starts_v = by_type["verify_start"]
        dones_v = by_type["verify_done"]
        vstart_map = {(r["task_id"], r["attempt"]): r for r in starts_v}
        vdone_map = {(r["task_id"], r["attempt"]): r for r in dones_v}
        if len(vstart_map) != len(starts_v) or len(vdone_map) != len(dones_v):
            fail(f"{sid}: duplicate verifier attempt")
        if set(vstart_map) != set(vdone_map) or set(vstart_map) != set(enqueue_map):
            fail(f"{sid}: verifier queue accounting mismatch")
        if set(vstart_map) != set(enqueue_map):
            pass
        else:
            for key, enq in enqueue_map.items():
                start = vstart_map[key]
                if start["tick"] < enq["tick"] or start["evidence_tick"] != enq["evidence_tick"]:
                    fail(f"{sid}: verifier start precedes enqueue or evidence changed {key}")
        verifier_intervals = sorted([(r["tick"], vdone_map[(r["task_id"], r["attempt"])]["tick"], r["task_id"], r["attempt"])
                                     for r in starts_v if (r["task_id"], r["attempt"]) in vdone_map])
        if any(current[0] < previous[1] for previous, current in zip(verifier_intervals, verifier_intervals[1:])):
            fail(f"{sid}: verifier service intervals overlap")
        for key, start in vstart_map.items():
            done = vdone_map.get(key)
            if not done:
                continue
            age = done["tick"] - done["evidence_tick"]
            fresh = age <= config["freshness_window_ticks"]
            if done["tick"] - start["tick"] != config["normal_verify_ticks"] or start["service_ticks"] != config["normal_verify_ticks"]:
                fail(f"{sid}: verifier service duration mismatch {key}")
            if done.get("evidence_age") != age or done.get("status") != ("verified" if fresh else "stale") or done.get("effect") is not fresh:
                fail(f"{sid}: freshness/effect gate mismatch {key}")

        retries = by_type["retry_request"]
        retry_by_task: dict[str, list[dict]] = defaultdict(list)
        for retry in retries:
            retry_by_task[retry["task_id"]].append(retry)
        if any(len(v) > config["max_retries"] for v in retry_by_task.values()):
            fail(f"{sid}: retry budget exceeded")
        for task, retry_rows in retry_by_task.items():
            if any(r["attempt"] != 1 for r in retry_rows):
                fail(f"{sid}: retry attempt numbering invalid {task}")
            first = vdone_map.get((task, 0))
            if not first or first.get("status") != "stale":
                fail(f"{sid}: retry without stale predecessor {task}")
        retry_attempts = {(r["task_id"], r["attempt"]) for r in retries}
        if retry_attempts - set(start_map):
            fail(f"{sid}: retry not locally acted upon")
        success_by_task: dict[str, list[dict]] = defaultdict(list)
        for r in dones_v:
            if r.get("status") == "verified":
                success_by_task[r["task_id"]].append(r)
        if any(len(v) != 1 for v in success_by_task.values()):
            fail(f"{sid}: duplicate task success")

        unknown_ids = {r["task_id"] for r in by_type["task_unknown"]}
        verified_ids = set(success_by_task)
        pending_ids = set(offers) - verified_ids - unknown_ids
        if verified_ids & unknown_ids or verified_ids | unknown_ids | pending_ids != set(offers):
            fail(f"{sid}: terminal task accounting mismatch")
        if len(offers) != summary.get("offered_tasks"):
            fail(f"{sid}: offered count summary mismatch")
        expected_pending_peak = 0
        normal_intervals = sorted((r["tick"], vdone_map[(r["task_id"], r["attempt"])]["tick"])
                                  for r in enqueues if (r["task_id"], r["attempt"]) in vdone_map)
        safety_done_rows = {r["safety_id"]: r for r in by_type["safety_done"]}
        safety_intervals = sorted((r["tick"], safety_done_rows[r["safety_id"]]["tick"])
                                  for r in by_type["safety_start"] if r["safety_id"] in safety_done_rows)
        for tick in range(max([config["horizon"]] + [b for _, b in normal_intervals + safety_intervals]) + 1):
            pending = sum(1 for a, b in normal_intervals if a <= tick < b)
            expected_pending_peak = max(expected_pending_peak, pending)
        if summary.get("peak_normal_pending") != expected_pending_peak:
            fail(f"{sid}: pending peak mismatch")
        if policy == "backpressure" and expected_pending_peak > (
                config["backpressure_pending_threshold"] + config["telemetry_delay_ticks"]):
            fail(f"{sid}: delayed-telemetry backlog bound exceeded")
        if any(r["observed_tick"] != r["tick"] - config["telemetry_delay_ticks"] or
               r["observed_pending"] < config["backpressure_pending_threshold"] or
               r["actual_pending"] != sum(1 for a, b in normal_intervals if a <= r["tick"] < b) or
               r["observed_pending"] != sum(1 for a, b in normal_intervals if a <= r["observed_tick"] < b)
               for r in by_type["action_deferred"]):
            fail(f"{sid}: backpressure deferral telemetry invalid")

        safety_releases = {r["safety_id"]: r for r in by_type["safety_release"]}
        safety_starts = {r["safety_id"]: r for r in by_type["safety_start"]}
        safety_dones = {r["safety_id"]: r for r in by_type["safety_done"]}
        if set(safety_releases) != set(safety_starts) or set(safety_starts) != set(safety_dones):
            fail(f"{sid}: mandatory safety lane accounting mismatch")
        safety_lats = []
        for safety_id, release in safety_releases.items():
            start, done = safety_starts.get(safety_id), safety_dones.get(safety_id)
            if not start or not done:
                continue
            latency = done["tick"] - release["tick"]
            safety_lats.append(latency)
            if latency > config["safety_latency_bound_ticks"] or done["status"] != "serviced":
                fail(f"{sid}: safety deadline/status violation {safety_id}")
            if done["tick"] - start["tick"] != config["safety_verify_ticks"]:
                fail(f"{sid}: safety service duration mismatch {safety_id}")
            if start["tick"] < release["tick"] or start["release_tick"] != release["tick"]:
                fail(f"{sid}: safety start precedes release or release mismatch {safety_id}")
        if summary.get("safety_events_released") != len(safety_releases) or summary.get("safety_events_serviced") != len(safety_dones):
            fail(f"{sid}: safety summary mismatch")

        horizon = config["horizon"]
        horizon_verified = {task for task, success in success_by_task.items() if success[0]["tick"] <= horizon}
        latencies = sorted(success_by_task[t][0]["tick"] - offers[t]["tick"] for t in horizon_verified)
        stale_count = sum(r.get("status") == "stale" for r in dones_v)
        unknown_count = len(unknown_ids)
        checks = {
            "verified_tasks_total": len(verified_ids), "verified_by_horizon": len(horizon_verified),
            "p95_verified_latency_by_horizon": p95(latencies), "normal_jobs_generated": len(enqueues),
            "stale_attempts": stale_count, "retry_requests": len(retries), "unknown_tasks": unknown_count,
            "pending_tasks_at_drain": len(pending_ids), "safety_max_latency": max(safety_lats, default=0),
        }
        for key, val in checks.items():
            if summary.get(key) != val:
                fail(f"{sid}: summary metric mismatch {key}: {summary.get(key)} != {val}")
        expected_class_counts = {}
        for task_class in ("low", "high"):
            class_tasks = {task_id for task_id, offer in offers.items() if offer["task_class"] == task_class}
            expected_class_counts[task_class] = {
                "offered": len(class_tasks),
                "verified_total": len(class_tasks & verified_ids),
                "verified_by_horizon": len(class_tasks & horizon_verified),
                "unknown": len(class_tasks & unknown_ids),
            }
        if summary.get("class_counts") != expected_class_counts:
            fail(f"{sid}: per-class outcome counts mismatch")

    if not errors and len(expected_scenarios) == 16:
        summaries = {rows[-1]["scenario_id"]: rows[-1] for rows in groups.values() if rows and rows[-1].get("type") == "summary"}
        def cell(mode: str, load: str, speed: str, policy: str) -> dict:
            return summaries[f"{mode}-{load}-{speed}-{policy}"]
        contrasts = [("fixed-near", cell("fixed", "near", "fast", "fifo"), cell("fixed", "near", "fast", "backpressure")),
                     ("fixed-high", cell("fixed", "high", "fast", "fifo"), cell("fixed", "high", "fast", "backpressure")),
                     ("closed", cell("closed", "closed", "fast", "fifo"), cell("closed", "closed", "fast", "backpressure"))]
        inversions = []
        for mode, load in [("fixed", "near"), ("fixed", "high")]:
            base = cell(mode, load, "base", "fifo")
            fast = cell(mode, load, "fast", "fifo")
            p95_worse = (base["p95_verified_latency_by_horizon"] is not None and
                         fast["p95_verified_latency_by_horizon"] is not None and
                         fast["p95_verified_latency_by_horizon"] > base["p95_verified_latency_by_horizon"])
            throughput_worse = fast["verified_by_horizon"] < base["verified_by_horizon"]
            if fast["action_ticks"] < base["action_ticks"] and (p95_worse or throughput_worse):
                bp = cell(mode, load, "fast", "backpressure")
                corresponding_improvement = ((throughput_worse and bp["verified_by_horizon"] > fast["verified_by_horizon"]) or
                                             (p95_worse and bp["p95_verified_latency_by_horizon"] is not None and
                                              fast["p95_verified_latency_by_horizon"] is not None and
                                              bp["p95_verified_latency_by_horizon"] < fast["p95_verified_latency_by_horizon"]))
                if corresponding_improvement and bp["stale_attempts"] < fast["stale_attempts"]:
                    inversions.append((load, base, fast, bp))
        if not inversions:
            fail("no preregistered near/overload fixed cell shows faster local action plus worse horizon metric that backpressure improves with fewer stale attempts")
        for _, fast, bp in contrasts:
            if bp["verified_by_horizon"] < fast["verified_by_horizon"]:
                fail("backpressure worsens horizon throughput in fast high/closed contrast")
        for sid, summary in summaries.items():
            if summary["safety_events_released"] != summary["safety_events_serviced"]:
                fail(f"{sid}: not all safety obligations serviced")
    return errors


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def main() -> int:
    path = Path(sys.argv[1]) if len(sys.argv) > 1 else HERE / "candidate.jsonl"
    issues = audit(read_jsonl(path))
    if issues:
        print("FAIL_INDEPENDENT_AUDIT")
        for issue in issues:
            print(f"- {issue}")
        return 1
    print("PASS_INDEPENDENT_AUDIT cells=16 safety_all_serviced=true")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
