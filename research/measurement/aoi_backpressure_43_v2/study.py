#!/usr/bin/env python3
"""Frozen deterministic AoI / critical-retention toy study for Issue #5494."""
import hashlib
import json
import platform
import random
import sys

SEED = 43001
TRIALS = 1000
HORIZON = 200
CAPACITY = 4
SERVICE_PER_TICK = 1
CRITICAL_PROBABILITY = 0.08
STATE_SESSION = "s0"

def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)

def streams():
    rng = random.Random(SEED)
    for trial in range(TRIALS):
        events = []
        for tick in range(HORIZON):
            draw = rng.random()
            arrivals = 0 if draw < 0.20 else (1 if draw < 0.55 else 3)
            for slot in range(arrivals):
                kind = "critical" if rng.random() < CRITICAL_PROBABILITY else "state"
                events.append({"id": f"{trial:04d}-{tick:03d}-{slot}", "tick": tick,
                               "kind": kind, "session": STATE_SESSION})
        yield trial, events

def simulate(events, policy):
    queue = []
    disposition = {}
    counters = {"dropped_critical": 0, "dropped_state": 0, "evicted_state": 0,
                "coalesced_state": 0, "delivered_critical": 0, "delivered_state": 0,
                "pending_critical": 0, "pending_state": 0, "policy_operation_count": 0}
    age_hist = [0] * (HORIZON + 1)
    last_state_tick = None

    for tick in range(HORIZON):
        incoming = [event for event in events if event["tick"] == tick]
        counters["policy_operation_count"] += 1  # one service-slot inspection per tick
        for event in incoming:
            counters["policy_operation_count"] += 1  # arrival inspection
            if policy == "priority" and event["kind"] == "state":
                counters["policy_operation_count"] += len(queue)  # same-session lookup comparisons
                same = next((i for i, old in enumerate(queue)
                             if old["kind"] == "state" and old["session"] == event["session"]), None)
                if same is not None:
                    old = queue.pop(same)
                    counters["policy_operation_count"] += 1  # queue removal
                    disposition[old["id"]] = "coalesced_state"
                    counters["coalesced_state"] += 1

            if len(queue) >= CAPACITY and policy == "priority" and event["kind"] == "critical":
                counters["policy_operation_count"] += len(queue)  # replacement lookup comparisons
                replaceable = next((i for i, old in enumerate(queue)
                                    if old["kind"] == "state"), None)
                if replaceable is not None and event["kind"] == "critical":
                    old = queue.pop(replaceable)
                    counters["policy_operation_count"] += 1  # queue removal
                    disposition[old["id"]] = "evicted_state"
                    counters["evicted_state"] += 1

            if len(queue) >= CAPACITY:
                result = "dropped_critical" if event["kind"] == "critical" else "dropped_state"
                counters["policy_operation_count"] += 1  # rejected admission
                disposition[event["id"]] = result
                counters[result] += 1
            else:
                counters["policy_operation_count"] += 1  # accepted admission
                queue.append(event)

        for _ in range(SERVICE_PER_TICK):
            if queue:
                counters["policy_operation_count"] += 1  # service removal
                event = queue.pop(0)
                disposition[event["id"]] = "delivered_" + event["kind"]
                counters["delivered_" + event["kind"]] += 1
                if event["kind"] == "state":
                    last_state_tick = event["tick"]

        age = tick + 1 if last_state_tick is None else tick - last_state_tick
        age_hist[age] += 1

    for event in queue:
        disposition[event["id"]] = "pending_" + event["kind"]
        counters["pending_" + event["kind"]] += 1

    ordered = [[event["id"], disposition[event["id"]]] for event in events]
    return counters, age_hist, hashlib.sha256(canonical(ordered).encode("ascii")).hexdigest()

def control_checks():
    all_critical = [{"id": f"a{i}", "tick": 0, "kind": "critical", "session": STATE_SESSION}
                    for i in range(4)]
    all_critical += [{"id": "a4", "tick": 1, "kind": "critical", "session": STATE_SESSION},
                     {"id": "a5", "tick": 1, "kind": "critical", "session": STATE_SESSION}]
    base, _, _ = simulate(all_critical, "fifo")
    candidate, _, _ = simulate(all_critical, "priority")
    assert base["dropped_critical"] == candidate["dropped_critical"] == 1

    mixed = [{"id": f"m{i}", "tick": 0, "kind": kind, "session": STATE_SESSION}
             for i, kind in enumerate(("critical", "critical", "state", "critical"))]
    mixed += [{"id": "m4", "tick": 1, "kind": "critical", "session": STATE_SESSION},
              {"id": "m5", "tick": 1, "kind": "critical", "session": STATE_SESSION}]
    base, _, _ = simulate(mixed, "fifo")
    candidate, _, _ = simulate(mixed, "priority")
    assert base["dropped_critical"] == 1
    assert candidate["dropped_critical"] == 0
    assert candidate["evicted_state"] == 1
    return {"all_critical_full_counted": True, "mixed_full_evicts_state": True}

def run(study_sha):
    controls = control_checks()
    totals = {name: {"dropped_critical": 0, "dropped_state": 0, "evicted_state": 0,
                     "coalesced_state": 0, "delivered_critical": 0, "delivered_state": 0,
                     "pending_critical": 0, "pending_state": 0, "age_histogram": [0] * (HORIZON + 1), "policy_operation_count": 0}
              for name in ("fifo_drop_new", "critical_preserving_coalesce")}
    trial_critical_drops = []
    offered_critical = offered_state = 0
    stream_hash = hashlib.sha256()
    outcome_hashes = {key: hashlib.sha256() for key in totals}

    for trial, events in streams():
        stream_hash.update(canonical(events).encode("ascii"))
        stream_hash.update(b"\\n")
        offered_critical += sum(event["kind"] == "critical" for event in events)
        offered_state += sum(event["kind"] == "state" for event in events)
        per_trial_drops = []
        for name, policy in (("fifo_drop_new", "fifo"), ("critical_preserving_coalesce", "priority")):
            counters, age_hist, outcome_digest = simulate(events, policy)
            arm = totals[name]
            for key in counters:
                arm[key] += counters[key]
            for i, value in enumerate(age_hist):
                arm["age_histogram"][i] += value
            outcome_hashes[name].update(f"{trial}:{outcome_digest}\\n".encode("ascii"))
            per_trial_drops.append(counters["dropped_critical"])
        trial_critical_drops.append(tuple(per_trial_drops))

    for arm in totals.values():
        arm["critical_drop_fraction"] = arm["dropped_critical"] / offered_critical
        samples = sum(arm["age_histogram"])
        arm["query_age_mean_ticks"] = sum(i * n for i, n in enumerate(arm["age_histogram"])) / samples
        rank = (95 * samples + 99) // 100
        seen = 0
        arm["query_age_p95_ticks"] = 0
        for age, count in enumerate(arm["age_histogram"]):
            seen += count
            if seen >= rank:
                arm["query_age_p95_ticks"] = age
                break

    better = sum(candidate < fifo for fifo, candidate in trial_critical_drops)
    equal = sum(candidate == fifo for fifo, candidate in trial_critical_drops)
    worse = sum(candidate > fifo for fifo, candidate in trial_critical_drops)
    result = {
        "status": "RUNNER_COMPLETE",
        "study_source_sha256": study_sha,
        "python": platform.python_version(), "implementation": sys.implementation.name, "platform_system": platform.system(),
        "seed": SEED, "trials": TRIALS, "horizon_ticks": HORIZON,
        "queue_capacity": CAPACITY, "service_per_tick": SERVICE_PER_TICK,
        "critical_probability": CRITICAL_PROBABILITY,
        "arrival_rule": "per tick: 0 if draw<0.20; 1 if draw<0.55; otherwise 3",
        "offered_events": offered_critical + offered_state,
        "offered_critical": offered_critical, "offered_state": offered_state,
        "offered_stream_sha256": stream_hash.hexdigest(),
        "arms": totals,
        "outcome_sha256": {key: value.hexdigest() for key, value in outcome_hashes.items()},
        "paired_critical_drop_trials": {"candidate_better": better, "equal": equal, "candidate_worse": worse},
        "controls": controls,
        "scope": "deterministic synthetic queue construction only; no runtime or user-task evidence"
    }
    print(canonical(result))

if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("usage: study.py EXPECTED_STUDY_SHA256")
    run(sys.argv[1])
