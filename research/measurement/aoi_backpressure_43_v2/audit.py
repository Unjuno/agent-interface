#!/usr/bin/env python3
"""Independent replay auditor for the frozen Issue #5494 toy study."""
import copy
import hashlib
import json
import random
import sys

SEED, TRIALS, HORIZON, CAPACITY, SERVICE_PER_TICK = 43001, 1000, 200, 4, 1
SESSION = "s0"
def canon(x):
    return json.dumps(x, sort_keys=True, separators=(",", ":"), ensure_ascii=True)

def source_stream():
    r = random.Random(SEED)
    for trial in range(TRIALS):
        events = []
        for t in range(HORIZON):
            x = r.random()
            n = 0 if x < .20 else 1 if x < .55 else 3
            for j in range(n):
                events.append({"id": f"{trial:04d}-{t:03d}-{j}", "tick": t,
                               "kind": "critical" if r.random() < .08 else "state",
                               "session": SESSION})
        yield trial, events

def replay(events, priority):
    q, outcome = [], {}
    policy_operations = 0
    age = [0] * (HORIZON + 1)
    last_state = None
    for tick in range(HORIZON):
        policy_operations += 1  # fixed service-slot inspection
        for e in (v for v in events if v["tick"] == tick):
            policy_operations += 1  # arrival inspection
            if priority and e["kind"] == "state":
                policy_operations += len(q)  # same-session lookup comparisons
                old_index = next((k for k, v in enumerate(q)
                                 if v["kind"] == "state" and v["session"] == e["session"]), -1)
                if old_index >= 0:
                    old = q.pop(old_index)
                    policy_operations += 1
                    outcome[old["id"]] = "coalesced_state"
            if priority and len(q) == CAPACITY and e["kind"] == "critical":
                policy_operations += len(q)  # replacement lookup comparisons
                old_index = next((k for k, v in enumerate(q) if v["kind"] == "state"), -1)
                if old_index >= 0:
                    old = q.pop(old_index)
                    policy_operations += 1
                    outcome[old["id"]] = "evicted_state"
            if len(q) == CAPACITY:
                policy_operations += 1
                outcome[e["id"]] = "dropped_" + e["kind"]
            else:
                policy_operations += 1
                q.append(e)
        for _ in range(SERVICE_PER_TICK):
            if q:
                policy_operations += 1
                e = q.pop(0)
                outcome[e["id"]] = "delivered_" + e["kind"]
                if e["kind"] == "state":
                    last_state = e["tick"]
        age[tick + 1 if last_state is None else tick - last_state] += 1
    for e in q:
        outcome[e["id"]] = "pending_" + e["kind"]

    counts = {name: 0 for name in ("dropped_critical", "dropped_state", "evicted_state",
             "coalesced_state", "delivered_critical", "delivered_state",
             "pending_critical", "pending_state")}
    for event_id, status in outcome.items():
        if status.startswith("dropped_") or status.startswith("delivered_") or status.startswith("pending_"):
            key = status
            counts[key] += 1
        elif status == "evicted_state":
            counts[status] += 1
        elif status == "coalesced_state":
            counts[status] += 1
    digest_rows = [[e["id"], outcome[e["id"]]] for e in events]
    counts["policy_operation_count"] = policy_operations
    return counts, age, hashlib.sha256(canon(digest_rows).encode("ascii")).hexdigest()

def expected(doc):
    stream_digest = hashlib.sha256()
    outcome_digests = {k: hashlib.sha256() for k in ("fifo_drop_new", "critical_preserving_coalesce")}
    arms = {k: {name: 0 for name in ("dropped_critical", "dropped_state", "evicted_state",
            "coalesced_state", "delivered_critical", "delivered_state",
            "pending_critical", "pending_state", "policy_operation_count")} | {"age_histogram": [0] * (HORIZON + 1)}
            for k in outcome_digests}
    critical_offered = state_offered = 0
    paired = [0, 0, 0]
    for trial, events in source_stream():
        stream_digest.update(canon(events).encode("ascii"))
        stream_digest.update(b"\\n")
        critical_offered += sum(e["kind"] == "critical" for e in events)
        state_offered += sum(e["kind"] == "state" for e in events)
        drops = []
        for name, priority in (("fifo_drop_new", False), ("critical_preserving_coalesce", True)):
            counts, ages, digest = replay(events, priority)
            for key, value in counts.items():
                arms[name][key] += value
            for i, value in enumerate(ages):
                arms[name]["age_histogram"][i] += value
            outcome_digests[name].update(f"{trial}:{digest}\\n".encode("ascii"))
            drops.append(counts["dropped_critical"])
        paired[0 if drops[1] < drops[0] else 1 if drops[1] == drops[0] else 2] += 1

    total_samples = TRIALS * HORIZON
    for arm in arms.values():
        arm["critical_drop_fraction"] = arm["dropped_critical"] / critical_offered
        arm["query_age_mean_ticks"] = sum(i * n for i, n in enumerate(arm["age_histogram"])) / total_samples
        rank, cumul = (95 * total_samples + 99) // 100, 0
        for i, n in enumerate(arm["age_histogram"]):
            cumul += n
            if cumul >= rank:
                arm["query_age_p95_ticks"] = i
                break
    return {
        "seed": SEED, "trials": TRIALS, "horizon_ticks": HORIZON,
        "queue_capacity": CAPACITY, "service_per_tick": SERVICE_PER_TICK,
        "critical_probability": .08,
        "arrival_rule": "per tick: 0 if draw<0.20; 1 if draw<0.55; otherwise 3",
        "offered_events": critical_offered + state_offered,
        "offered_critical": critical_offered, "offered_state": state_offered,
        "offered_stream_sha256": stream_digest.hexdigest(),
        "arms": arms,
        "outcome_sha256": {k: v.hexdigest() for k, v in outcome_digests.items()},
        "paired_critical_drop_trials": {"candidate_better": paired[0], "equal": paired[1], "candidate_worse": paired[2]}
    }

def verify(doc, expected_study, expected_audit):
    if doc.get("status") != "RUNNER_COMPLETE":
        return False
    if doc.get("study_source_sha256") != expected_study:
        return False
    if doc.get("audit_source_sha256") != expected_audit:
        return False
    if doc.get("controls") != {"all_critical_full_counted": True, "mixed_full_evicts_state": True}:
        return False
    if doc.get("python") != "3.11.9" or doc.get("implementation") != "cpython" or doc.get("platform_system") != "Windows" or doc.get("scope") != "deterministic synthetic queue construction only; no runtime or user-task evidence":
        return False
    calc = expected(doc)
    return all(doc.get(k) == v for k, v in calc.items())

def main():
    expected_study, expected_audit = sys.argv[1:3]
    doc = json.load(sys.stdin)
    ok = verify(doc, expected_study, expected_audit)
    mutations = []
    for mutate in (
        lambda x: x["arms"]["fifo_drop_new"].__setitem__("dropped_critical", x["arms"]["fifo_drop_new"]["dropped_critical"] + 1),
        lambda x: x["arms"]["critical_preserving_coalesce"]["age_histogram"].__setitem__(0, x["arms"]["critical_preserving_coalesce"]["age_histogram"][0] + 1),
        lambda x: x["offered_critical"].__setitem__("bad", 1) if isinstance(x["offered_critical"], dict) else x.__setitem__("offered_critical", x["offered_critical"] + 1),
        lambda x: x["outcome_sha256"].__setitem__("fifo_drop_new", "0" * 64),
    ):
        changed = copy.deepcopy(doc)
        mutate(changed)
        mutations.append(not verify(changed, expected_study, expected_audit))
    report = {"status": "PASS_AOI_RETENTION_HOST_ONLY" if ok and all(mutations) else "FAIL_AOI_RETENTION_AUDIT",
              "runner_replay_exact": ok, "mutation_controls_rejected": sum(mutations),
              "mutation_controls_total": len(mutations)}
    print(canon(report))
    raise SystemExit(0 if report["status"].startswith("PASS_") else 1)

if __name__ == "__main__":
    main()
