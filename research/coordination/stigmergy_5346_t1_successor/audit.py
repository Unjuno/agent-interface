#!/usr/bin/env python3
"""Independent raw-only audit for the Issue #5346 T1 schedule corpus."""
from __future__ import annotations

import hashlib
import itertools
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

ARMS = {"NONE", "CENTRAL_CLAIMS", "LOCAL_MARKERS"}
CONDITIONS = {"clean", "lost", "duplicated", "stale", "forged"}
OUTCOMES = {"complete", "crash"}


def fail(errors, message):
    errors.append(message)


def audit(path):
    raw = Path(path).read_bytes()
    rows = [json.loads(line) for line in raw.splitlines()]
    errors = []
    groups = defaultdict(dict)
    aggregate = Counter()
    for i, row in enumerate(rows):
        if row.get("schema") != "stigmergy-5346-t1-raw-v1":
            fail(errors, f"row {i}: wrong schema")
            continue
        scenario = row.get("scenario", {})
        workers = scenario.get("workers")
        order = scenario.get("order")
        if workers not in (2, 3, 4) or sorted(order or []) != list(range(workers or 0)):
            fail(errors, f"row {i}: invalid worker schedule")
        if scenario.get("observation_delay") not in (0, 1, 2):
            fail(errors, f"row {i}: invalid delay")
        if scenario.get("marker_condition") not in CONDITIONS:
            fail(errors, f"row {i}: invalid marker condition")
        if scenario.get("owner_outcome") not in OUTCOMES:
            fail(errors, f"row {i}: invalid owner outcome")
        arm = row.get("arm")
        if arm not in ARMS:
            fail(errors, f"row {i}: invalid arm")
            continue
        key = json.dumps(scenario, sort_keys=True)
        if arm in groups[key]:
            fail(errors, f"row {i}: duplicate scenario-arm")
        groups[key][arm] = row
        counts = row.get("counts", {})
        for field in ("proposals", "blocked_admissions", "coordination_messages",
                      "completed_tasks", "recoveries", "unsafe_admissions"):
            if not isinstance(counts.get(field), int) or counts[field] < 0:
                fail(errors, f"row {i}: invalid count {field}")
        trace = row.get("trace", [])
        owners = set()
        completed = []
        effects = []
        active = None
        for event in trace:
            if event.get("event") == "proposal" and event.get("admitted"):
                owner_key = (event.get("worker"), event.get("generation"))
                owners.add(owner_key)
                if active is not None:
                    fail(errors, f"row {i}: overlapping lease admission")
                active = owner_key
            elif event.get("event") == "lease_release":
                release_key = (event.get("worker"), event.get("generation"))
                if active != release_key:
                    fail(errors, f"row {i}: lease release has no matching active owner")
                active = None
            elif event.get("event") == "effect":
                effects.append((event.get("worker"), event.get("generation")))
            elif event.get("event") == "task_complete":
                completed.append((event.get("worker"), event.get("generation")))
            if event.get("event") in ("marker_publish", "marker_observed",
                                       "proposal_suppressed", "marker_rejected") and event.get("authority") is not False:
                fail(errors, f"row {i}: marker has authority")
            if event.get("event") == "proposal" and event.get("verdict") == "admitted_atomic_lease":
                if not event.get("admitted"):
                    fail(errors, f"row {i}: gate contradiction")
        if counts.get("unsafe_admissions") != 0:
            fail(errors, f"row {i}: unsafe admission count nonzero")
        if counts.get("completed_tasks") != len(completed) or len(completed) > 1:
            fail(errors, f"row {i}: completion count mismatch")
        if any(item not in owners for item in completed) or set(completed) != set(effects):
            fail(errors, f"row {i}: completion missing admitted lease/effect")
        if len({gen for _, gen in owners}) != len(owners):
            fail(errors, f"row {i}: admitted generations not unique")
        if active is not None:
            fail(errors, f"row {i}: lease left active")
        if counts.get("completed_tasks") != 1:
            fail(errors, f"row {i}: scenario did not complete exactly once")
        if counts.get("recoveries", 0) > 1:
            fail(errors, f"row {i}: recovery count exceeds one task")
        if arm == "LOCAL_MARKERS" and scenario.get("marker_condition") in ("stale", "forged"):
            rejected = [e for e in trace if e.get("event") == "marker_rejected"]
            if len(rejected) != workers - 1:
                fail(errors, f"row {i}: stale/forged marker control missing")
            if any(e.get("state") != scenario.get("marker_condition") for e in rejected):
                fail(errors, f"row {i}: stale/forged marker mislabeled")
        if arm == "LOCAL_MARKERS" and scenario.get("marker_condition") == "duplicated":
            observed = [e for e in trace if e.get("event") == "marker_observed"]
            if any(e.get("state") != "duplicated_reduced" for e in observed):
                fail(errors, f"row {i}: duplicate marker reduction missing")
        for field in counts:
            aggregate[f"{arm}.{field}"] += counts[field]

    scenario_count = 0
    blocked_by_delay = defaultdict(Counter)
    crash_rows_recovered = True
    for workers in (2, 3, 4):
        for order in itertools.permutations(range(workers)):
            for delay in (0, 1, 2):
                for condition in sorted(CONDITIONS):
                    for outcome in sorted(OUTCOMES):
                        scenario = {"workers": workers, "order": list(order),
                                    "observation_delay": delay,
                                    "marker_condition": condition,
                                    "owner_outcome": outcome}
                        key = json.dumps(scenario, sort_keys=True)
                        arms = groups.get(key, {})
                        if set(arms) != ARMS:
                            fail(errors, f"missing arms for {key}")
                            continue
                        scenario_count += 1
                        for arm in ARMS:
                            counts = arms[arm]["counts"]
                            blocked_by_delay[delay][arm] += counts["blocked_admissions"]
                            if outcome == "crash" and counts["completed_tasks"] != 1:
                                crash_rows_recovered = False
                        # Every policy has the exact same atomic admission trace
                        # after removing advisory-only events.
                        authority_traces = []
                        for arm in sorted(ARMS):
                            trace = arms[arm]["trace"]
                            authority_traces.append([
                                e for e in trace
                                if ((e.get("event") == "proposal" and e.get("admitted"))
                                    or e.get("event") in ("effect", "task_complete", "owner_crash", "lease_release"))
                            ])
                        if not (authority_traces[0] == authority_traces[1] == authority_traces[2]):
                            fail(errors, f"authority trace differs across arms: {key}")

    raw_hash = hashlib.sha256(raw).hexdigest()
    delayed_gain = any(
        blocked_by_delay[delay]["LOCAL_MARKERS"] < blocked_by_delay[delay]["NONE"]
        for delay in (1, 2)
    )
    messages_noninferior = aggregate["LOCAL_MARKERS.coordination_messages"] <= aggregate["CENTRAL_CLAIMS.coordination_messages"]
    gates = {
        "raw_and_invariant_audit": not errors,
        "all_owner_crashes_recovered": crash_rows_recovered,
        "local_markers_reduce_blocked_proposals_at_delay_1_or_2": delayed_gain,
        "local_markers_use_no_more_explicit_messages_than_central": messages_noninferior,
    }
    scientific_pass = all(gates.values())
    result = {"status": "PASS" if scientific_pass else "FAIL",
              "raw_sha256": raw_hash, "rows": len(rows),
              "scenarios": scenario_count, "errors": errors,
              "aggregates": dict(sorted(aggregate.items())),
              "blocked_by_delay": {str(delay): dict(counts)
                                   for delay, counts in sorted(blocked_by_delay.items())},
              "gates": gates}
    print(json.dumps(result, sort_keys=True, indent=2))
    return 0 if not errors else 1


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("usage: audit.py RAW.jsonl")
    raise SystemExit(audit(sys.argv[1]))
