"""Finite two-worker stigmergic coordination model for Issue #5346 T0."""

from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any


POLICIES = ("NO_COORDINATION", "CENTRAL_CLAIMS", "LOCAL_MARKERS")
TARGETS = ("A", "B")


@dataclass(frozen=True)
class Scenario:
    name: str
    worker1_start: int = 1
    marker_visibility_delay: int = 0
    marker_dropped: bool = False
    forged_marker: bool = False
    stale_generation: bool = False
    duplicate_marker: bool = False
    worker0_crashes: bool = False
    external_mutation: bool = False
    worker1_prefers_b: bool = False


SCENARIOS = (
    Scenario("visible_contention"),
    Scenario("delayed_observation", marker_visibility_delay=2),
    Scenario("marker_loss", marker_dropped=True),
    Scenario("forged_marker", forged_marker=True),
    Scenario("stale_generation", stale_generation=True),
    Scenario("duplicate_delivery", duplicate_marker=True),
    Scenario("owner_crash", worker0_crashes=True),
    Scenario("external_mutation", external_mutation=True),
    Scenario("no_contention", worker1_prefers_b=True),
)


def run_case(scenario: Scenario, policy: str) -> dict[str, Any]:
    if policy not in POLICIES:
        raise ValueError(f"unknown policy: {policy}")

    events: list[dict[str, Any]] = []
    completed: set[str] = set()
    owner0_finish = 5 if scenario.external_mutation else 3
    owner0_lock_expiry = 4 if scenario.worker0_crashes or scenario.external_mutation else owner0_finish
    current_generation = {"A": 2 if scenario.external_mutation else 1, "B": 1}
    marker_generation = 0 if scenario.stale_generation else 1
    marker_authentic = not scenario.forged_marker
    marker_valid = (
        policy == "LOCAL_MARKERS"
        and not scenario.marker_dropped
        and marker_authentic
        and marker_generation == current_generation["A"]
        and scenario.worker1_start >= scenario.marker_visibility_delay
        and scenario.worker1_start < 4
    )
    coordination_events = 0
    if policy == "LOCAL_MARKERS":
        # Worker 0 publishes a non-authoritative hint. Duplicate delivery is
        # deduplicated by trace identity and does not add another effective write.
        if not scenario.marker_dropped:
            events.append({"tick": 0, "kind": "MARKER_PUBLISH", "worker": 0,
                           "target": "A", "generation": 1, "trace_id": "t0-A-1"})
            coordination_events += 1
            if scenario.duplicate_marker:
                events.append({"tick": 0, "kind": "MARKER_DUPLICATE_IGNORED", "worker": 0,
                               "target": "A", "generation": 1, "trace_id": "t0-A-1"})
        if scenario.forged_marker:
            events.append({"tick": 0, "kind": "FORGED_MARKER_IGNORED", "worker": 1,
                           "target": "A", "generation": 1, "trace_id": "forged"})
        if scenario.stale_generation:
            events.append({"tick": 0, "kind": "STALE_MARKER_IGNORED", "worker": 1,
                           "target": "A", "generation": 0, "trace_id": "stale"})

    # Worker 0 takes A under the ordinary authoritative lease gate. The trace
    # itself is never consulted by this admission.
    events.append({"tick": 0, "kind": "LEASE_GRANTED", "worker": 0, "target": "A",
                   "generation": 1, "basis": "authoritative_lease"})
    coordination_events += 2 if policy == "CENTRAL_CLAIMS" else 0
    if policy == "CENTRAL_CLAIMS":
        events.extend([
            {"tick": 0, "kind": "CENTRAL_CLAIM_REQUEST", "worker": 0, "target": "A"},
            {"tick": 0, "kind": "CENTRAL_CLAIM_GRANT", "worker": 0, "target": "A"},
        ])

    if scenario.external_mutation:
        events.append({"tick": 1, "kind": "EXTERNAL_GENERATION_CHANGE", "worker": None,
                       "target": "A", "from_generation": 1, "to_generation": 2})

    proposed = "B" if scenario.worker1_prefers_b else "A"
    if policy == "CENTRAL_CLAIMS":
        events.extend([
            {"tick": scenario.worker1_start, "kind": "CENTRAL_CLAIM_REQUEST", "worker": 1,
             "target": proposed},
            {"tick": scenario.worker1_start, "kind": "CENTRAL_CLAIM_GRANT", "worker": 1,
             "target": "B"},
        ])
        coordination_events += 2
        proposed = "B"
    elif marker_valid:
        events.append({"tick": scenario.worker1_start, "kind": "MARKER_OBSERVED", "worker": 1,
                       "target": "A", "generation": 1, "trace_id": "t0-A-1"})
        coordination_events += 1
        if proposed == "A":
            proposed = "B"

    collisions = 0
    duplicate_proposals = 0
    retries = 0
    recovery_latency = 0
    worker1_finish = scenario.worker1_start + 3

    if proposed == "A" and not scenario.worker1_prefers_b:
        # The shared authoritative lock catches missing/late hints. The worker
        # waits and refreshes before trying again; it never replays a stale action.
        collisions = 1
        duplicate_proposals = 1
        retries = 1
        retry_at = max(scenario.worker1_start, owner0_lock_expiry)
        worker1_finish = retry_at + 3
        events.append({"tick": scenario.worker1_start, "kind": "LEASE_CONFLICT", "worker": 1,
                       "target": "A", "basis": "authoritative_lease"})
        events.append({"tick": retry_at, "kind": "FRESH_REOBSERVATION", "worker": 1,
                       "target": "A", "generation": current_generation["A"]})
        recovery_latency = max(0, retry_at - scenario.worker1_start) if scenario.worker0_crashes else 0
        proposed = "A"

    if scenario.worker0_crashes:
        events.append({"tick": 1, "kind": "OWNER_CRASH", "worker": 0, "target": "A"})
        events.append({"tick": owner0_lock_expiry, "kind": "LEASE_EXPIRED", "worker": 0,
                       "target": "A", "basis": "authoritative_lease_ttl"})
        if proposed != "A":
            recovery_latency = max(0, owner0_lock_expiry - scenario.worker1_start)
        if proposed == "A":
            events.append({"tick": owner0_lock_expiry, "kind": "LEASE_GRANTED", "worker": 1,
                           "target": "A", "generation": current_generation["A"],
                           "basis": "authoritative_lease"})
            completed.add("A")
            worker1_finish = owner0_lock_expiry + 3
        else:
            completed.add(proposed)
        # The surviving worker performs the remaining unit after re-observation.
        remaining = next((t for t in TARGETS if t not in completed), None)
        if remaining:
            recovery_start = max(worker1_finish, owner0_lock_expiry)
            events.append({"tick": recovery_start, "kind": "FRESH_REOBSERVATION", "worker": 1,
                           "target": remaining, "generation": current_generation[remaining]})
            events.append({"tick": recovery_start, "kind": "LEASE_GRANTED", "worker": 1,
                           "target": remaining, "generation": current_generation[remaining],
                           "basis": "authoritative_lease"})
            completed.add(remaining)
            worker1_finish = recovery_start + 3
    elif scenario.external_mutation:
        # Worker 0's stale generation is refused before effect, then it obtains
        # fresh evidence and retries only after re-observation. Worker 1 remains
        # serialized by the same lease gate.
        events.append({"tick": 2, "kind": "STALE_GENERATION_REFUSED", "worker": 0,
                       "target": "A", "observed": 1, "current": 2})
        events.append({"tick": 2, "kind": "FRESH_REOBSERVATION", "worker": 0,
                       "target": "A", "generation": 2})
        events.append({"tick": 2, "kind": "LEASE_GRANTED", "worker": 0, "target": "A",
                       "generation": 2, "basis": "authoritative_lease"})
        completed.add("A")
        if proposed == "A":
            events.append({"tick": owner0_finish, "kind": "LEASE_GRANTED", "worker": 1, "target": "B",
                           "generation": 1, "basis": "authoritative_lease"})
            completed.add("B")
            worker1_finish = owner0_finish + 3
        else:
            events.append({"tick": scenario.worker1_start, "kind": "LEASE_GRANTED", "worker": 1,
                           "target": "B", "generation": 1, "basis": "authoritative_lease"})
            completed.add("B")
            worker1_finish = max(scenario.worker1_start + 3, 5)
    else:
        completed.add("A")
        if proposed == "B":
            events.append({"tick": scenario.worker1_start, "kind": "LEASE_GRANTED", "worker": 1,
                           "target": "B", "generation": current_generation["B"],
                           "basis": "authoritative_lease"})
            completed.add("B")
        elif policy != "CENTRAL_CLAIMS":
            events.append({"tick": owner0_finish,
                           "kind": "DUPLICATE_EFFECT_SUPPRESSED",
                           "worker": 1, "target": "A", "basis": "authoritative_effect_check"})
            events.append({"tick": owner0_finish, "kind": "LEASE_GRANTED", "worker": 1,
                           "target": "B", "generation": current_generation["B"],
                           "basis": "authoritative_lease"})
            completed.add("B")

    if scenario.worker0_crashes:
        events.append({"tick": 1, "kind": "TASK_EFFECT", "worker": 0,
                       "target": "A", "result": "absent"})
    for target in sorted(completed):
        events.append({"tick": owner0_finish if target == "A" and not scenario.worker0_crashes
                       else worker1_finish, "kind": "EFFECT_CONFIRMED", "worker": None,
                       "target": target, "basis": "independent_effect_oracle"})
    if scenario.forged_marker and policy == "LOCAL_MARKERS":
        # Explicit assertion-bearing event: forged advice did not grant anything.
        events.append({"tick": scenario.worker1_start, "kind": "MARKER_AUTHORITY_GRANTS",
                       "worker": 1, "target": "A", "count": 0})

    # A marker can change a route, never lease/effect status. Every action grant
    # in the event log carries an independent lease/effect basis.
    grants = [e for e in events if e["kind"] == "LEASE_GRANTED"]
    unsafe_admissions = sum(e.get("basis") != "authoritative_lease" for e in grants)
    outcomes = {
        "scenario": scenario.name,
        "policy": policy,
        "completed_targets": sorted(completed),
        "completion_count": len(completed),
        "collision_retries": collisions,
        "duplicate_proposals": duplicate_proposals,
        "coordination_events": coordination_events,
        "recovery_latency_ticks": recovery_latency,
        "unsafe_admissions": unsafe_admissions,
        "all_effects_have_authoritative_gate": unsafe_admissions == 0,
        "events": events,
    }
    return outcomes


def run_all() -> dict[str, Any]:
    cells = [run_case(s, p) for s in SCENARIOS for p in POLICIES]
    return {
        "schema": "stigmergic_coordination_5346_t0_raw_v1",
        "source_issue": 5346,
        "frozen_main": "afb7a91983a782f06ae12ebfbe8f802376f69d22",
        "policies": list(POLICIES),
        "scenario_count": len(SCENARIOS),
        "cell_count": len(cells),
        "scenarios": [asdict(s) for s in SCENARIOS],
        "cells": cells,
    }


if __name__ == "__main__":
    import json
    print(json.dumps(run_all(), sort_keys=True, separators=(",", ":")))
