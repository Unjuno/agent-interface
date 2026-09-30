#!/usr/bin/env python3
"""Independent raw-only T2 audit, including contract timing and mutation gates."""
from __future__ import annotations

import copy
import hashlib
import itertools
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

ARMS = {"NONE", "CENTRAL_CLAIMS", "LOCAL_MARKERS"}
CONDITIONS = {"clean", "lost", "duplicated", "stale", "forged"}
OUTCOMES = {"complete", "crash"}
EXPECTED_CONTRACT = {"lease_ttl": 3, "task_duration": 2, "crash_tick": 1}


def expected_scenarios():
    for workers in (2, 3, 4):
        for order in itertools.permutations(range(workers)):
            for delay in range(5):
                for condition in sorted(CONDITIONS):
                    for outcome in sorted(OUTCOMES):
                        yield {"workers": workers, "order": list(order),
                               "observation_delay": delay,
                               "marker_condition": condition,
                               "owner_outcome": outcome}


def validate(rows):
    errors = []
    groups = defaultdict(dict)
    aggregate = Counter()
    blocked_fresh = defaultdict(Counter)
    all_crashes_recovered = True
    for row_index, row in enumerate(rows):
        if row.get("schema") != "stigmergy-5346-t2-raw-v1":
            errors.append(f"row {row_index}: wrong schema")
            continue
        if row.get("contract") != EXPECTED_CONTRACT:
            errors.append(f"row {row_index}: contract mismatch")
        scenario = row.get("scenario", {})
        workers = scenario.get("workers")
        order = scenario.get("order")
        if workers not in (2, 3, 4) or sorted(order or []) != list(range(workers or 0)):
            errors.append(f"row {row_index}: invalid worker ordering")
        if scenario.get("observation_delay") not in range(5):
            errors.append(f"row {row_index}: invalid observation delay")
        if scenario.get("marker_condition") not in CONDITIONS:
            errors.append(f"row {row_index}: invalid marker condition")
        if scenario.get("owner_outcome") not in OUTCOMES:
            errors.append(f"row {row_index}: invalid owner outcome")
        arm = row.get("arm")
        if arm not in ARMS:
            errors.append(f"row {row_index}: invalid arm")
            continue
        key = json.dumps(scenario, sort_keys=True)
        if arm in groups[key]:
            errors.append(f"row {row_index}: duplicate scenario/arm")
        groups[key][arm] = row
        counts = row.get("counts", {})
        required_counts = ("proposals", "blocked_admissions", "coordination_messages",
                           "completed_tasks", "recoveries", "unsafe_admissions")
        if any(not isinstance(counts.get(k), int) or counts[k] < 0 for k in required_counts):
            errors.append(f"row {row_index}: malformed counters")
        trace = row.get("trace", [])
        active = None
        grants = {}
        effects = []
        completions = []
        blocked = 0
        proposals = 0
        recoveries = 0
        admitted_proposals = Counter()
        grant_proposals = Counter()
        for event in trace:
            kind = event.get("event")
            if kind == "proposal":
                proposals += 1
                if event.get("verdict") == "blocked_busy":
                    blocked += 1
            if kind in ("marker_publish", "marker_observed", "proposal_suppressed", "marker_rejected"):
                if event.get("authority") is not False:
                    errors.append(f"row {row_index}: marker carried authority")
            if kind == "proposal_suppressed" and event.get("tick", -1) >= EXPECTED_CONTRACT["lease_ttl"]:
                errors.append(f"row {row_index}: expired marker suppressed a proposal")
            if kind == "marker_observed" and event.get("state") == "duplicated_reduced":
                if event.get("copies") != 2:
                    errors.append(f"row {row_index}: duplicate marker control malformed")
            if kind == "proposal" and event.get("admitted"):
                if event.get("verdict") != "admitted_atomic_lease":
                    errors.append(f"row {row_index}: admission verdict mismatch")
                admitted_proposals[(event.get("worker"), event.get("tick"))] += 1
            elif kind == "lease_grant":
                owner_key = (event.get("worker"), event.get("generation"))
                grant_proposals[(event.get("worker"), event.get("tick"))] += 1
                if grant_proposals[(event.get("worker"), event.get("tick"))] > admitted_proposals[(event.get("worker"), event.get("tick"))]:
                    errors.append(f"row {row_index}: lease grant lacks admitted proposal")
                if active is not None:
                    errors.append(f"row {row_index}: overlapping lease grants")
                if active is not None and event.get("tick", -1) < active["until"]:
                    errors.append(f"row {row_index}: new grant before prior expiry")
                generation = event.get("generation")
                reason = event.get("reason")
                expected_duration = (
                    EXPECTED_CONTRACT["lease_ttl"]
                    if generation == 1 and scenario.get("owner_outcome") == "crash"
                    else EXPECTED_CONTRACT["task_duration"]
                )
                if event.get("until") != event.get("tick") + expected_duration:
                    errors.append(f"row {row_index}: lease grant duration violates frozen contract")
                if generation > 1:
                    recoveries += 1
                active = {"owner": owner_key[0], "generation": generation,
                          "until": event.get("until")}
                grants[owner_key] = event
            elif kind == "lease_release":
                release_key = (event.get("worker"), event.get("generation"))
                if active is None or release_key != (active["owner"], active["generation"]):
                    errors.append(f"row {row_index}: release without matching active lease")
                if active is not None and event.get("tick") != active["until"]:
                    errors.append(f"row {row_index}: release timestamp differs from lease boundary")
                active = None
            elif kind == "effect":
                effects.append((event.get("worker"), event.get("generation"), event.get("tick")))
            elif kind == "task_complete":
                completions.append((event.get("worker"), event.get("generation"), event.get("tick")))
        if active is not None:
            errors.append(f"row {row_index}: lease remains active")
        if proposals != counts.get("proposals") or blocked != counts.get("blocked_admissions"):
            errors.append(f"row {row_index}: proposal counters do not reconstruct")
        if admitted_proposals != grant_proposals:
            errors.append(f"row {row_index}: proposal/grant ledger differs")
        if recoveries != counts.get("recoveries"):
            errors.append(f"row {row_index}: recovery counter does not reconstruct")
        if counts.get("unsafe_admissions") != 0:
            errors.append(f"row {row_index}: unsafe admission counter nonzero")
        expected_messages = workers - 1 if arm == "CENTRAL_CLAIMS" else 0
        if counts.get("coordination_messages") != expected_messages:
            errors.append(f"row {row_index}: coordination message counter mismatch")
        if len(completions) != 1 or counts.get("completed_tasks") != 1:
            errors.append(f"row {row_index}: task did not complete exactly once")
        if effects != completions:
            errors.append(f"row {row_index}: effect/completion mismatch")
        if any((w, g) not in grants for w, g, _ in completions):
            errors.append(f"row {row_index}: completion lacks admitted lease")
        if scenario.get("owner_outcome") == "crash" and recoveries != 1:
            all_crashes_recovered = False
        for field in counts:
            aggregate[f"{arm}.{field}"] += counts[field]
        if scenario.get("marker_condition") in ("clean", "duplicated"):
            blocked_fresh[scenario.get("observation_delay")][arm] += blocked

    authority_traces_equal = True
    scenario_count = 0
    for scenario in expected_scenarios():
        key = json.dumps(scenario, sort_keys=True)
        arms = groups.get(key, {})
        if set(arms) != ARMS:
            errors.append(f"missing arm(s) for {key}")
            continue
        scenario_count += 1
        authority = []
        for arm in sorted(ARMS):
            authority.append([
                event for event in arms[arm]["trace"]
                if event.get("event") in ("lease_grant", "lease_release", "effect",
                                           "task_complete", "owner_crash")
            ])
        if not authority[0] == authority[1] == authority[2]:
            authority_traces_equal = False
            errors.append(f"admission/effect trace differs across arms: {key}")

    delayed_fresh_gain = any(
        blocked_fresh[delay]["LOCAL_MARKERS"] < blocked_fresh[delay]["NONE"]
        for delay in (1, 2)
    )
    return errors, {
        "aggregates": dict(sorted(aggregate.items())),
        "blocked_fresh_by_delay": {str(d): dict(c)
                                   for d, c in sorted(blocked_fresh.items())},
        "scenarios": scenario_count,
        "authority_traces_equal": authority_traces_equal,
        "all_crashes_recovered_once": all_crashes_recovered,
        "delayed_fresh_reduction": delayed_fresh_gain,
        "messages_noninferior": aggregate["LOCAL_MARKERS.coordination_messages"]
            <= aggregate["CENTRAL_CLAIMS.coordination_messages"],
    }


def mutation_controls(rows):
    ttl_rows = copy.deepcopy(rows)
    changed = False
    for row in ttl_rows:
        if row.get("scenario", {}).get("owner_outcome") == "crash":
            for event in row.get("trace", []):
                if event.get("event") == "lease_release" and event.get("cause") == "lease_expired":
                    event["tick"] += 1
                    changed = True
                    break
            if changed:
                break
    ttl_rejected = changed and bool(validate(ttl_rows)[0])

    authority_rows = copy.deepcopy(rows)
    changed = False
    for row in authority_rows:
        if row.get("arm") == "LOCAL_MARKERS":
            for event in row.get("trace", []):
                if event.get("event") == "marker_observed":
                    event["authority"] = True
                    changed = True
                    break
            if changed:
                break
    authority_rejected = changed and bool(validate(authority_rows)[0])
    return {"ttl_release_time_mutation_rejected": bool(ttl_rejected),
            "marker_authority_mutation_rejected": bool(authority_rejected)}


def main(path):
    raw = Path(path).read_bytes()
    rows = [json.loads(line) for line in raw.splitlines()]
    errors, facts = validate(rows)
    controls = mutation_controls(rows)
    complete_matrix = facts["scenarios"] == 1600 and len(rows) == 4800
    gates = {
        "complete_matrix": complete_matrix,
        "raw_contract_and_lease_audit": not errors,
        "same_authority_trace_across_arms": facts["authority_traces_equal"],
        "all_crashes_recovered_once": facts["all_crashes_recovered_once"],
        "fresh_delayed_markers_reduce_blocked_attempts": facts["delayed_fresh_reduction"],
        "local_markers_use_no_more_explicit_messages_than_central": facts["messages_noninferior"],
        "ttl_mutation_control": controls["ttl_release_time_mutation_rejected"],
        "authority_mutation_control": controls["marker_authority_mutation_rejected"],
    }
    status = "PASS" if all(gates.values()) else "FAIL"
    print(json.dumps({"status": status,
                      "raw_sha256": hashlib.sha256(raw).hexdigest(),
                      "rows": len(rows), "errors": errors,
                      **facts, "mutation_controls": controls, "gates": gates},
                     sort_keys=True, indent=2))
    return 0 if status == "PASS" else 1


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("usage: audit.py RAW.jsonl")
    raise SystemExit(main(sys.argv[1]))
