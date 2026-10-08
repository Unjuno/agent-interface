#!/usr/bin/env python3
"""Supplemental independent raw-only audit of marker visibility timing/faults."""
from __future__ import annotations

import copy
import hashlib
import itertools
import json
import sys
from pathlib import Path

ARMS = {"NONE", "CENTRAL_CLAIMS", "LOCAL_MARKERS"}
CONDS = {"clean", "lost", "duplicated", "stale", "forged"}


def check(rows):
    errors = []
    by_key = {}
    for ix, row in enumerate(rows):
        if row.get("schema") != "stigmergy-5346-t2-raw-v1":
            errors.append(f"row {ix}: schema")
            continue
        scenario = row.get("scenario", {})
        key = json.dumps(scenario, sort_keys=True)
        arm = row.get("arm")
        by_key.setdefault(key, {})[arm] = row
        workers = scenario.get("workers")
        order = scenario.get("order", [])
        delay = scenario.get("observation_delay")
        condition = scenario.get("marker_condition")
        if arm not in ARMS or workers not in (2, 3, 4):
            errors.append(f"row {ix}: identity")
            continue
        if sorted(order) != list(range(workers)) or delay not in range(5) or condition not in CONDS:
            errors.append(f"row {ix}: scenario contract")
            continue
        rank = {worker: pos for pos, worker in enumerate(order)}
        expected_observations = {}
        for worker in order[1:]:
            t = rank[worker]
            if arm == "CENTRAL_CLAIMS":
                visible = delay <= t < 3
                state, copies = "central_claim", 1
            elif arm == "LOCAL_MARKERS" and condition in ("clean", "duplicated"):
                visible = delay <= t < 3
                copies = 2 if condition == "duplicated" else 1
                state = "duplicated_reduced" if copies == 2 else "local_marker"
            else:
                visible, state, copies = False, condition, 0
            if visible:
                expected_observations[(worker, t)] = (state, copies)

        observations = {}
        rejected = []
        suppressed = []
        expected_suppressed = set()
        active_until = None
        active_owner = None
        for event in row.get("trace", []):
            kind = event.get("event")
            if kind == "marker_publish":
                if event.get("ttl") != 3 or event.get("tick") != 0 or event.get("authority") is not False:
                    errors.append(f"row {ix}: marker publication contract")
            elif kind == "marker_observed":
                worker, tick = event.get("worker"), event.get("tick")
                observations[(worker, tick)] = (event.get("state"), event.get("copies"))
                if event.get("authority") is not False:
                    errors.append(f"row {ix}: observed marker authority")
                if tick < delay:
                    errors.append(f"row {ix}: observation preceded configured delay")
                if tick >= 3:
                    errors.append(f"row {ix}: expired marker observed")
                if active_owner is not None and tick < (active_until or -1):
                    expected_suppressed.add((worker, tick))
            elif kind == "marker_rejected":
                rejected.append(event)
                if event.get("authority") is not False:
                    errors.append(f"row {ix}: rejected marker authority")
            elif kind == "lease_grant":
                if active_owner is not None:
                    errors.append(f"row {ix}: grant while another lease active")
                active_owner = event.get("worker")
                active_until = event.get("until")
            elif kind == "lease_release":
                if active_owner != event.get("worker") or active_until != event.get("tick"):
                    errors.append(f"row {ix}: release timing/owner")
                active_owner, active_until = None, None
            elif kind == "proposal_suppressed":
                suppressed.append(event)
                key_obs = (event.get("worker"), event.get("tick"))
                if key_obs not in observations:
                    errors.append(f"row {ix}: suppression without prior observation")
                if active_owner is None or event.get("tick", -1) >= (active_until or -1):
                    errors.append(f"row {ix}: suppression without active lease")
                if event.get("tick", -1) >= 3:
                    errors.append(f"row {ix}: suppression at/after expiry")
                if event.get("authority") is not False:
                    errors.append(f"row {ix}: suppression authority")
        if observations != expected_observations:
            errors.append(f"row {ix}: observed-marker set differs from delay/fault contract")
        if {(e.get("worker"), e.get("tick")) for e in suppressed} != expected_suppressed:
            errors.append(f"row {ix}: advisory suppression differs from lease/visibility state")
        expected_rejects = workers - 1 if arm == "LOCAL_MARKERS" and condition in ("stale", "forged") else 0
        if len(rejected) != expected_rejects:
            errors.append(f"row {ix}: stale/forged rejection count")
        if any(e.get("state") != condition for e in rejected):
            errors.append(f"row {ix}: stale/forged rejection label")
        if active_owner is not None:
            errors.append(f"row {ix}: unreleased lease")
        if any((e.get("worker"), e.get("tick")) not in expected_observations for e in suppressed):
            errors.append(f"row {ix}: suppression lacked a valid marker")

    expected = 0
    for workers in (2, 3, 4):
        for order in itertools.permutations(range(workers)):
            for delay in range(5):
                for condition in sorted(CONDS):
                    for outcome in ("complete", "crash"):
                        scenario = {"workers": workers, "order": list(order),
                                    "observation_delay": delay,
                                    "marker_condition": condition,
                                    "owner_outcome": outcome}
                        arm_rows = by_key.get(json.dumps(scenario, sort_keys=True), {})
                        if set(arm_rows) != ARMS:
                            errors.append("incomplete scenario-arm matrix")
                        else:
                            expected += 1
    return errors, expected


def main(path):
    raw = Path(path).read_bytes()
    rows = [json.loads(line) for line in raw.splitlines()]
    errors, scenarios = check(rows)
    timing_rows = copy.deepcopy(rows)
    delay_mutated = False
    for row in timing_rows:
        if row.get("arm") == "LOCAL_MARKERS" and row.get("scenario", {}).get("observation_delay") == 1:
            for event in row.get("trace", []):
                if event.get("event") == "marker_observed":
                    event["tick"] = 0
                    delay_mutated = True
                    break
            if delay_mutated:
                break
    timing_mutation_rejected = delay_mutated and bool(check(timing_rows)[0])
    gates = {"complete_matrix": scenarios == 1600 and len(rows) == 4800,
             "delay_expiry_and_fault_contract": not errors,
             "early_observation_mutation_rejected": bool(timing_mutation_rejected)}
    status = "PASS" if all(gates.values()) else "FAIL"
    print(json.dumps({"status": status,
                      "raw_sha256": hashlib.sha256(raw).hexdigest(),
                      "rows": len(rows), "scenarios": scenarios,
                      "errors": errors,
                      "mutation_controls": {"early_observation_mutation_rejected": bool(timing_mutation_rejected)},
                      "gates": gates}, sort_keys=True, indent=2))
    return 0 if status == "PASS" else 1


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("usage: audit_v2.py RAW.jsonl")
    raise SystemExit(main(sys.argv[1]))
