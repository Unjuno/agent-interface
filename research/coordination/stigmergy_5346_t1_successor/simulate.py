#!/usr/bin/env python3
"""Frozen finite schedule model for Issue #5346 T1; stdlib only."""
from __future__ import annotations

import argparse
import itertools
import json
from pathlib import Path

ARMS = ("NONE", "CENTRAL_CLAIMS", "LOCAL_MARKERS")
MARKER_CONDITIONS = ("clean", "lost", "duplicated", "stale", "forged")
OWNER_OUTCOMES = ("complete", "crash")
LEASE_TTL = 3
TASK_DURATION = 2
RETRY_TICK = 1


def scenarios():
    for workers in (2, 3, 4):
        for order in itertools.permutations(range(workers)):
            for delay in (0, 1, 2):
                for marker_condition in MARKER_CONDITIONS:
                    for owner_outcome in OWNER_OUTCOMES:
                        yield {
                            "workers": workers,
                            "order": list(order),
                            "observation_delay": delay,
                            "marker_condition": marker_condition,
                            "owner_outcome": owner_outcome,
                        }


def marker_visible(scenario, arm, worker, first_owner, publish_tick):
    condition = scenario["marker_condition"]
    if arm == "NONE" or worker == first_owner:
        return False, "absent"
    tick = order_tick(scenario, worker)
    if arm == "CENTRAL_CLAIMS":
        # Central announcements are reliable but still obey observation delay.
        return (tick >= publish_tick + scenario["observation_delay"]), "central_claim"
    if condition in ("lost", "forged"):
        return False, condition
    if condition == "stale":
        return False, "stale"
    if tick < publish_tick + scenario["observation_delay"]:
        return False, "not_yet_visible"
    if tick >= publish_tick + LEASE_TTL:
        return False, "expired"
    # A duplicate is still one advisory state after idempotent local reduction.
    return True, "duplicated_reduced" if condition == "duplicated" else "local_marker"


def order_tick(scenario, worker):
    return scenario["order"].index(worker)


def run_arm(scenario, arm):
    order = scenario["order"]
    workers = scenario["workers"]
    first_owner = order[0]
    crash = scenario["owner_outcome"] == "crash"
    expiry = LEASE_TTL
    completion_tick = None if crash else TASK_DURATION
    release_tick = expiry if crash else completion_tick
    trace = []
    state = {"lease_owner": None, "generation": 0, "completed": False}
    counts = {"proposals": 0, "blocked_admissions": 0,
              "coordination_messages": 0, "completed_tasks": 0,
              "recoveries": 0, "unsafe_admissions": 0}

    def propose(worker, tick, reason):
        nonlocal release_tick, completion_tick
        counts["proposals"] += 1
        admitted = False
        # This is the only admission authority, shared by every arm.
        if state["completed"]:
            verdict = "already_complete"
        elif tick >= release_tick:
            if not crash and completion_tick is not None and tick >= completion_tick:
                trace.append({"event": "lease_release", "worker": first_owner,
                              "tick": completion_tick, "generation": 1,
                              "cause": "task_complete"})
                state["completed"] = True
                state["lease_owner"] = None
                trace.append({"event": "effect", "worker": first_owner,
                              "tick": completion_tick,
                              "generation": 1})
                trace.append({"event": "task_complete", "worker": first_owner,
                              "tick": completion_tick,
                              "generation": 1})
                counts["completed_tasks"] = 1
                verdict = "already_complete"
                trace.append({"event": "proposal", "worker": worker, "tick": tick,
                              "reason": reason, "verdict": verdict,
                              "admitted": False, "generation": state["generation"]})
                return False
            if state["lease_owner"] is not None:
                trace.append({"event": "lease_release", "worker": state["lease_owner"],
                              "tick": release_tick,
                              "generation": state["generation"],
                              "cause": "lease_expired" if crash else "task_complete"})
            state["lease_owner"] = None
            state["generation"] += 1
            state["lease_owner"] = worker
            admitted = True
            verdict = "admitted_atomic_lease"
            if crash or worker != first_owner:
                counts["recoveries"] += 1
            completion_tick = tick + TASK_DURATION
            release_tick = completion_tick
        elif state["lease_owner"] is None:
            state["generation"] += 1
            state["lease_owner"] = worker
            admitted = True
            verdict = "admitted_atomic_lease"
            completion_tick = tick + TASK_DURATION
            release_tick = completion_tick
        else:
            verdict = "blocked_busy"
            counts["blocked_admissions"] += 1
        trace.append({"event": "proposal", "worker": worker, "tick": tick,
                      "reason": reason, "verdict": verdict,
                      "admitted": admitted, "generation": state["generation"]})
        return admitted

    # The first scheduled worker obtains the lease. This arm-invariant first
    # transition is retained in the trace and audited rather than assumed.
    first_tick = 0
    if not propose(first_owner, first_tick, "initial"):
        raise AssertionError("first atomic admission unexpectedly refused")
    trace.append({"event": "marker_publish", "owner": first_owner,
                  "tick": first_tick, "ttl": LEASE_TTL,
                  "authority": False})
    if arm == "CENTRAL_CLAIMS":
        counts["coordination_messages"] += workers - 1
    if crash:
        trace.append({"event": "owner_crash", "owner": first_owner, "tick": 1})

    # Remaining workers have one staggered initial opportunity. Visible
    # advisory markers suppress only a proposal; invisible markers do not.
    for rank, worker in enumerate(order[1:], start=1):
        tick = rank
        visible, marker_state = marker_visible(scenario, arm, worker, first_owner, first_tick)
        if arm == "LOCAL_MARKERS" and visible:
            trace.append({"event": "marker_observed", "worker": worker,
                          "tick": tick, "state": marker_state,
                          "authority": False})
        if arm == "LOCAL_MARKERS" and scenario["marker_condition"] in ("stale", "forged"):
            trace.append({"event": "marker_rejected", "worker": worker,
                          "tick": tick, "state": marker_state,
                          "authority": False})
        if visible and tick < release_tick:
            trace.append({"event": "proposal_suppressed", "worker": worker,
                          "tick": tick, "cause": "advisory_marker",
                          "authority": False})
        else:
            propose(worker, tick, "initial")

    # Complete only after the last initial opportunity; this preserves the
    # frozen event order where a proposal at the same tick precedes completion.
    if not crash and not state["completed"]:
        trace.append({"event": "lease_release", "worker": first_owner,
                      "tick": completion_tick, "generation": 1,
                      "cause": "task_complete"})
        trace.append({"event": "effect", "worker": first_owner,
                      "tick": completion_tick,
                      "generation": 1})
        trace.append({"event": "task_complete", "worker": first_owner,
                      "tick": completion_tick,
                      "generation": 1})
        state["completed"] = True
        state["lease_owner"] = None
        counts["completed_tasks"] += 1
    if crash and not state["completed"] and state["lease_owner"] not in (None, first_owner):
        trace.append({"event": "lease_release", "worker": state["lease_owner"],
                      "tick": completion_tick, "generation": state["generation"],
                      "cause": "task_complete"})
        trace.append({"event": "effect", "worker": state["lease_owner"],
                      "tick": completion_tick,
                      "generation": state["generation"]})
        trace.append({"event": "task_complete", "worker": state["lease_owner"],
                      "tick": completion_tick,
                      "generation": state["generation"]})
        state["completed"] = True
        state["lease_owner"] = None
        counts["completed_tasks"] += 1
    if crash and not state["completed"]:
        # Any worker suppressed by a fresh marker wakes after the crashed
        # owner's lease expiry; a denied admission receives the same retry time.
        retry_tick = expiry + RETRY_TICK
        for worker in order[1:]:
            if state["completed"]:
                break
            admitted = propose(worker, retry_tick, "post_expiry_retry")
            if admitted:
                trace.append({"event": "lease_release", "worker": worker,
                              "tick": completion_tick,
                              "generation": state["generation"],
                              "cause": "task_complete"})
                trace.append({"event": "effect", "worker": worker,
                              "tick": completion_tick,
                              "generation": state["generation"]})
                trace.append({"event": "task_complete", "worker": worker,
                              "tick": completion_tick,
                              "generation": state["generation"]})
                state["completed"] = True
                state["lease_owner"] = None
                counts["completed_tasks"] += 1

    return {
        "schema": "stigmergy-5346-t1-raw-v1",
        "scenario": scenario,
        "arm": arm,
        "counts": counts,
        "final": {"completed": state["completed"],
                  "lease_owner": state["lease_owner"],
                  "generation": state["generation"]},
        "trace": trace,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    n = 0
    with out.open("w", encoding="utf-8", newline="\n") as stream:
        for scenario in scenarios():
            for arm in ARMS:
                stream.write(json.dumps(run_arm(scenario, arm), sort_keys=True,
                                        separators=(",", ":")) + "\n")
                n += 1
    print(json.dumps({"scenario_count": n // len(ARMS),
                      "arm_rows": n, "output": str(out)}, sort_keys=True))


if __name__ == "__main__":
    main()
