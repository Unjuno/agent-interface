#!/usr/bin/env python3
"""Deterministic discrete-event candidate for Issue #5372 T1.

The candidate is intentionally a small authored queue model, not a runtime.
It emits event-sourced JSONL; audit.py does not import this module.
"""
from __future__ import annotations

import hashlib
import json
import sys


ALLOCATION = "SAFETY-BACKPRESSURE-ENDOGENOUS-DEMAND-5372-T1-20261001-01"
CONFIG = {
    "schema": "safety-backpressure-5372-t1-v1",
    "horizon": 48,
    "drain_deadline": 160,
    "fixed_loads": {"low": {"count": 12, "arrival_stride": 4},
                    "near": {"count": 24, "arrival_stride": 2},
                    "high": {"count": 36, "arrival_rule": "floor(i*4/3)"}},
    "closed_loop_task_cap": 36,
    "action_ticks": {"base": 2, "fast": 1},
    "normal_verify_ticks": 2,
    "freshness_window_ticks": 4,
    "max_retries": 1,
    "backpressure_pending_threshold": 2,
    "telemetry_delay_ticks": 2,
    "safety_stride_ticks": 8,
    "safety_verify_ticks": 1,
    "safety_latency_bound_ticks": 3,
    "scenario_order": ["fixed:low", "fixed:near", "fixed:high", "closed:closed"],
    "speed_order": ["base", "fast"],
    "policy_order": ["fifo", "backpressure"],
    "class_rule": "alternating-low-high-by-task-id; first=low",
}
CONFIG_SHA256 = hashlib.sha256(json.dumps(CONFIG, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def _fixed_offers(load: str) -> list[dict]:
    spec = CONFIG["fixed_loads"][load]
    result = []
    for task_id in range(spec["count"]):
        tick = task_id * spec["arrival_stride"] if load != "high" else task_id * 4 // 3
        result.append({"task_id": f"T{task_id:03d}", "arrival_tick": tick,
                       "task_class": "low" if task_id % 2 == 0 else "high", "origin": "fixed"})
    return result


def _scenario_tasks(mode: str, load: str) -> list[dict]:
    if mode == "fixed":
        return _fixed_offers(load)
    return []


def run_scenario(mode: str, load: str, speed: str, policy: str) -> list[dict]:
    sid = f"{mode}-{load}-{speed}-{policy}"
    action_ticks = CONFIG["action_ticks"][speed]
    horizon = CONFIG["horizon"]
    rows: list[dict] = []
    seq = 0

    def emit(kind: str, **fields) -> None:
        nonlocal seq
        rows.append({"type": kind, "scenario_id": sid, "seq": seq, **fields})
        seq += 1

    emit("scenario", allocation=ALLOCATION, config_sha256=CONFIG_SHA256,
         mode=mode, offered_load=load, speed=speed, policy=policy,
         horizon=horizon, action_ticks=action_ticks)

    local_queue: list[dict] = []
    normal_queue: list[dict] = []
    safety_queue: list[dict] = []
    active_action: dict | None = None
    active_verify: dict | None = None
    action_done_at: int | None = None
    verify_done_at: int | None = None
    pending_history: dict[int, int] = {}
    task_state: dict[str, dict] = {}
    offers = _scenario_tasks(mode, load)
    offer_cursor = 0
    closed_next_id = 0
    safety_id = 0
    peak_normal_pending = 0

    def offer_task(task_id: str, tick: int, task_class: str, origin: str) -> None:
        task = {"task_id": task_id, "arrival_tick": tick, "task_class": task_class,
                "origin": origin, "attempt": 0, "retry": False}
        task_state.setdefault(task_id, {"arrival_tick": tick, "task_class": task_class,
                                        "verified_tick": None, "unknown": False})
        local_queue.append(task)
        emit("task_offer", task_id=task_id, tick=tick, task_class=task_class, origin=origin)

    if mode == "closed":
        offer_task("C000", 0, "low", "closed-loop")
        closed_next_id = 1

    def pending_normal() -> int:
        return len(normal_queue) + int(active_verify is not None and active_verify["lane"] == "normal")

    for tick in range(CONFIG["drain_deadline"] + 1):
        # Complete action before adding this tick's offers. This makes each action
        # completion the causal trigger for the next closed-loop request.
        if active_action is not None and action_done_at == tick:
            finished = active_action
            active_action = None
            action_done_at = None
            emit("action_done", task_id=finished["task_id"], tick=tick,
                 task_class=finished["task_class"], attempt=finished["attempt"],
                 local_ticks=action_ticks, retry=finished["retry"])
            normal = {"task_id": finished["task_id"], "task_class": finished["task_class"],
                      "attempt": finished["attempt"], "evidence_tick": tick,
                      "enqueue_tick": tick, "retry": finished["retry"]}
            normal_queue.append(normal)
            emit("verify_enqueue", task_id=normal["task_id"], task_class=normal["task_class"],
                 attempt=normal["attempt"], evidence_tick=tick, tick=tick, retry=normal["retry"])
            if mode == "closed" and tick < horizon and closed_next_id < CONFIG["closed_loop_task_cap"]:
                task_id = f"C{closed_next_id:03d}"
                cls = "low" if closed_next_id % 2 == 0 else "high"
                closed_next_id += 1
                offer_task(task_id, tick, cls, "closed-loop")

        # Complete the verifier; priority is applied only when selecting next work.
        if active_verify is not None and verify_done_at == tick:
            finished = active_verify
            active_verify = None
            verify_done_at = None
            if finished["lane"] == "safety":
                emit("safety_done", safety_id=finished["safety_id"], release_tick=finished["release_tick"],
                     start_tick=finished["start_tick"], tick=tick, status="serviced")
            else:
                age = tick - finished["evidence_tick"]
                fresh = age <= CONFIG["freshness_window_ticks"]
                emit("verify_done", task_id=finished["task_id"], task_class=finished["task_class"],
                     attempt=finished["attempt"], evidence_tick=finished["evidence_tick"],
                     start_tick=finished["start_tick"], tick=tick, evidence_age=age,
                     status="verified" if fresh else "stale", effect=bool(fresh), retry=finished["retry"])
                if fresh:
                    state = task_state[finished["task_id"]]
                    if state["verified_tick"] is None:
                        state["verified_tick"] = tick
                elif finished["attempt"] < CONFIG["max_retries"]:
                    retry = {"task_id": finished["task_id"], "arrival_tick": tick,
                             "task_class": finished["task_class"], "origin": "retry",
                             "attempt": finished["attempt"] + 1, "retry": True}
                    local_queue.insert(0, retry)
                    emit("retry_request", task_id=retry["task_id"], task_class=retry["task_class"],
                         attempt=retry["attempt"], tick=tick)
                else:
                    task_state[finished["task_id"]]["unknown"] = True
                    emit("task_unknown", task_id=finished["task_id"], tick=tick,
                         reason="stale_after_retry_limit")

        # External fixed offers arrive on a frozen schedule.
        while offer_cursor < len(offers) and offers[offer_cursor]["arrival_tick"] == tick:
            task = offers[offer_cursor]
            offer_task(task["task_id"], tick, task["task_class"], task["origin"])
            offer_cursor += 1

        # Mandatory safety actions enter the verifier's reserved-priority lane.
        if tick < horizon and tick % CONFIG["safety_stride_ticks"] == 0:
            safety = {"safety_id": f"S{safety_id:03d}", "release_tick": tick}
            safety_id += 1
            safety_queue.append(safety)
            emit("safety_release", safety_id=safety["safety_id"], tick=tick)

        # Start at most one verifier item; mandatory safety is strict priority.
        if active_verify is None:
            if safety_queue:
                item = safety_queue.pop(0)
                active_verify = {**item, "lane": "safety", "start_tick": tick}
                verify_done_at = tick + CONFIG["safety_verify_ticks"]
                emit("safety_start", safety_id=item["safety_id"], release_tick=item["release_tick"],
                     tick=tick, service_ticks=CONFIG["safety_verify_ticks"])
            elif normal_queue:
                item = normal_queue.pop(0)
                active_verify = {**item, "lane": "normal", "start_tick": tick}
                verify_done_at = tick + CONFIG["normal_verify_ticks"]
                emit("verify_start", task_id=item["task_id"], task_class=item["task_class"],
                     attempt=item["attempt"], evidence_tick=item["evidence_tick"], tick=tick,
                     service_ticks=CONFIG["normal_verify_ticks"], retry=item["retry"])

        # Start one local action if the policy's delayed queue signal permits it.
        if active_action is None and local_queue:
            observed_tick = tick - CONFIG["telemetry_delay_ticks"]
            observed = pending_history.get(observed_tick, 0) if observed_tick >= 0 else 0
            if policy == "backpressure" and observed >= CONFIG["backpressure_pending_threshold"]:
                emit("action_deferred", task_id=local_queue[0]["task_id"], tick=tick,
                     observed_tick=observed_tick, observed_pending=observed,
                     actual_pending=pending_normal())
            else:
                item = local_queue.pop(0)
                active_action = item
                action_done_at = tick + action_ticks
                emit("action_start", task_id=item["task_id"], task_class=item["task_class"],
                     attempt=item["attempt"], tick=tick, local_ticks=action_ticks, retry=item["retry"])

        pending_history[tick] = pending_normal()
        peak_normal_pending = max(peak_normal_pending, pending_history[tick])

        # Stop early only after the finite source and all work have drained.
        no_future_fixed = offer_cursor >= len(offers)
        no_future_closed = mode != "closed" or (tick >= horizon or closed_next_id >= CONFIG["closed_loop_task_cap"])
        if (tick >= horizon and no_future_fixed and no_future_closed and not local_queue and
                active_action is None and not normal_queue and not safety_queue and active_verify is None):
            break

    tasks = list(task_state.items())
    verified = [(task_id, state) for task_id, state in tasks if state["verified_tick"] is not None]
    by_horizon = [(task_id, state) for task_id, state in verified if state["verified_tick"] <= horizon]
    latencies = sorted(state["verified_tick"] - state["arrival_tick"] for _, state in by_horizon)
    def percentile95(values: list[int]) -> int | None:
        return None if not values else values[max(0, (95 * len(values) + 99) // 100 - 1)]

    safety_done = [row for row in rows if row["type"] == "safety_done"]
    safety_latencies = [row["tick"] - row["release_tick"] for row in safety_done]
    class_counts = {}
    for task_class in ("low", "high"):
        selected = [(task_id, state) for task_id, state in tasks if state["task_class"] == task_class]
        class_counts[task_class] = {
            "offered": len(selected),
            "verified_total": sum(state["verified_tick"] is not None for _, state in selected),
            "verified_by_horizon": sum(state["verified_tick"] is not None and state["verified_tick"] <= horizon
                                        for _, state in selected),
            "unknown": sum(state["unknown"] for _, state in selected),
        }
    summary = {
        "scenario_id": sid,
        "mode": mode,
        "offered_load": load,
        "speed": speed,
        "policy": policy,
        "action_ticks": action_ticks,
        "offered_tasks": len(task_state),
        "verified_tasks_total": len(verified),
        "verified_by_horizon": len(by_horizon),
        "p95_verified_latency_by_horizon": percentile95(latencies),
        "normal_jobs_generated": sum(row["type"] == "verify_enqueue" for row in rows),
        "stale_attempts": sum(row["type"] == "verify_done" and row["status"] == "stale" for row in rows),
        "retry_requests": sum(row["type"] == "retry_request" for row in rows),
        "unknown_tasks": sum(state["unknown"] for _, state in tasks),
        "pending_tasks_at_drain": sum(state["verified_tick"] is None and not state["unknown"] for _, state in tasks),
        "peak_normal_pending": peak_normal_pending,
        "class_counts": class_counts,
        "safety_events_released": sum(row["type"] == "safety_release" for row in rows),
        "safety_events_serviced": len(safety_done),
        "safety_max_latency": max(safety_latencies, default=0),
        "drain_tick": rows[-1]["tick"] if rows and "tick" in rows[-1] else horizon,
    }
    emit("summary", **summary)
    return rows


def all_records() -> list[dict]:
    records: list[dict] = [{"type": "freeze", "allocation": ALLOCATION,
                            "config": CONFIG, "config_sha256": CONFIG_SHA256}]
    for scenario in CONFIG["scenario_order"]:
        mode, load = scenario.split(":", 1)
        for speed in CONFIG["speed_order"]:
            for policy in CONFIG["policy_order"]:
                records.extend(run_scenario(mode, load, speed, policy))
    return records


def main() -> None:
    for record in all_records():
        print(json.dumps(record, sort_keys=True, separators=(",", ":")))


if __name__ == "__main__":
    main()
