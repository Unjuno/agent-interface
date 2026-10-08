#!/usr/bin/env python3
"""Frozen Issue #5346 T2 TTL-boundary schedule model; stdlib only."""
from __future__ import annotations

import argparse
import itertools
import json
from pathlib import Path

ARMS = ("NONE", "CENTRAL_CLAIMS", "LOCAL_MARKERS")
CONDITIONS = ("clean", "lost", "duplicated", "stale", "forged")
OUTCOMES = ("complete", "crash")
LEASE_TTL = 3
TASK_DURATION = 2
CRASH_TICK = 1
RETRY_TICK = 4


def scenarios():
    for workers in (2, 3, 4):
        for order in itertools.permutations(range(workers)):
            for delay in range(5):
                for condition in CONDITIONS:
                    for outcome in OUTCOMES:
                        yield {"workers": workers, "order": list(order),
                               "observation_delay": delay,
                               "marker_condition": condition,
                               "owner_outcome": outcome}


def marker_observation(scenario, arm, worker, first_owner, tick):
    if arm == "NONE" or worker == first_owner:
        return False, "absent", 0
    condition = scenario["marker_condition"]
    if arm == "LOCAL_MARKERS" and condition in ("lost", "stale", "forged"):
        return False, condition, 0
    delay = scenario["observation_delay"]
    age = tick
    if delay > tick or age >= LEASE_TTL:
        return False, "not_visible_or_expired", 0
    copies = 2 if arm == "LOCAL_MARKERS" and condition == "duplicated" else 1
    state = "duplicated_reduced" if copies == 2 else (
        "central_claim" if arm == "CENTRAL_CLAIMS" else "local_marker")
    return True, state, copies


def run_arm(scenario, arm):
    order = scenario["order"]
    first_owner = order[0]
    crashed = scenario["owner_outcome"] == "crash"
    initial_until = LEASE_TTL if crashed else TASK_DURATION
    trace = []
    counts = {"proposals": 0, "blocked_admissions": 0,
              "coordination_messages": 0, "completed_tasks": 0,
              "recoveries": 0, "unsafe_admissions": 0}
    state = {"owner": None, "generation": 0, "lease_until": None,
             "complete": False, "completion_due": None}

    def grant(worker, tick, reason, duration):
        if state["complete"]:
            counts["proposals"] += 1
            trace.append({"event": "proposal", "worker": worker, "tick": tick,
                          "reason": reason, "verdict": "already_complete",
                          "admitted": False})
            return False
        if state["owner"] is not None and tick < state["lease_until"]:
            counts["blocked_admissions"] += 1
            counts["proposals"] += 1
            trace.append({"event": "proposal", "worker": worker, "tick": tick,
                          "reason": reason, "verdict": "blocked_busy"})
            return False
        if state["owner"] is not None:
            trace.append({"event": "lease_release", "worker": state["owner"],
                          "generation": state["generation"],
                          "tick": state["lease_until"], "cause": "lease_expired"})
            state["owner"] = None
            state["lease_until"] = None
        state["generation"] += 1
        state["owner"] = worker
        state["lease_until"] = tick + duration
        owner_crashed_before_effect = crashed and worker == first_owner and reason == "initial"
        state["completion_due"] = None if owner_crashed_before_effect else tick + TASK_DURATION
        counts["proposals"] += 1
        if worker != first_owner:
            counts["recoveries"] += 1
        trace.append({"event": "proposal", "worker": worker, "tick": tick,
                      "reason": reason, "verdict": "admitted_atomic_lease",
                      "admitted": True})
        trace.append({"event": "lease_grant", "worker": worker,
                      "generation": state["generation"], "tick": tick,
                      "until": state["lease_until"], "reason": reason})
        return True

    def finish_if_due(tick):
        if (not state["complete"] and state["owner"] is not None
                and state["completion_due"] is not None
                and tick >= state["completion_due"]):
            owner, generation = state["owner"], state["generation"]
            due = state["completion_due"]
            trace.append({"event": "lease_release", "worker": owner,
                          "generation": generation, "tick": due,
                          "cause": "task_complete"})
            trace.append({"event": "effect", "worker": owner,
                          "generation": generation, "tick": due})
            trace.append({"event": "task_complete", "worker": owner,
                          "generation": generation, "tick": due})
            state.update(owner=None, lease_until=None, complete=True)
            counts["completed_tasks"] += 1

    grant(first_owner, 0, "initial", initial_until)
    trace.append({"event": "marker_publish", "owner": first_owner,
                  "tick": 0, "ttl": LEASE_TTL, "authority": False})
    if arm == "CENTRAL_CLAIMS":
        counts["coordination_messages"] = len(order) - 1
    if crashed:
        trace.append({"event": "owner_crash", "owner": first_owner,
                      "tick": CRASH_TICK})

    for rank, worker in enumerate(order[1:], start=1):
        tick = rank
        finish_if_due(tick)
        visible, marker_state, copies = marker_observation(
            scenario, arm, worker, first_owner, tick)
        if arm == "LOCAL_MARKERS" and scenario["marker_condition"] in ("stale", "forged"):
            trace.append({"event": "marker_rejected", "worker": worker,
                          "tick": tick, "state": marker_state, "authority": False})
        if visible:
            trace.append({"event": "marker_observed", "worker": worker,
                          "tick": tick, "state": marker_state,
                          "copies": copies, "authority": False})
        if visible and state["lease_until"] is not None and tick < state["lease_until"]:
            trace.append({"event": "proposal_suppressed", "worker": worker,
                          "tick": tick, "cause": "advisory_marker",
                          "authority": False})
        else:
            grant(worker, tick, "initial", TASK_DURATION)

    finish_if_due(max(len(order), TASK_DURATION, LEASE_TTL))
    if crashed and not state["complete"]:
        # Every non-owner worker gets one post-expiry retry in stable order.
        for worker in order[1:]:
            finish_if_due(RETRY_TICK)
            if state["complete"]:
                break
            if worker == state["owner"]:
                continue
            grant(worker, RETRY_TICK, "post_expiry_retry", TASK_DURATION)
        finish_if_due(RETRY_TICK + TASK_DURATION)

    return {"schema": "stigmergy-5346-t2-raw-v1",
            "contract": {"lease_ttl": LEASE_TTL,
                         "task_duration": TASK_DURATION,
                         "crash_tick": CRASH_TICK},
            "scenario": scenario, "arm": arm, "counts": counts,
            "final": {"complete": state["complete"],
                      "owner": state["owner"],
                      "generation": state["generation"]},
            "trace": trace}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", required=True)
    out = Path(parser.parse_args().out)
    out.parent.mkdir(parents=True, exist_ok=True)
    n = 0
    with out.open("w", encoding="utf-8", newline="\n") as stream:
        for scenario in scenarios():
            for arm in ARMS:
                stream.write(json.dumps(run_arm(scenario, arm), sort_keys=True,
                                        separators=(",", ":")) + "\n")
                n += 1
    print(json.dumps({"scenario_count": n // len(ARMS), "arm_rows": n,
                      "output": str(out)}, sort_keys=True))


if __name__ == "__main__":
    main()
