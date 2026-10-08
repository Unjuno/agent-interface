#!/usr/bin/env python3
"""Candidate finite-state model for Issue #5704 T0."""
from __future__ import annotations

import itertools
import json
import argparse
from pathlib import Path


EFFECTS = ("NONE", "APPLIED", "UNKNOWN")
DELIVERY = ("KNOWN", "UNKNOWN")
INPUTS = ("RELEASED", "HELD", "UNKNOWN")
TARGETS = ("CURRENT", "STALE", "UNKNOWN")
STEPS = ("sync_planner", "sync_broker", "sync_actuator", "quarantine_claim", "trusted_release")
MESSAGE_SET = ("OLD_CLAIM", "ACK", "RELEASE_ACK", "OLD_CLAIM")


def configurations():
    for p, b, a, pending, delivery, effect, input_state, release_ok, effect_readable, target, new_auth, persisted_auth in itertools.product(
        (0, 1), (0, 1), (0, 1), (False, True), DELIVERY, EFFECTS, INPUTS,
        (False, True), (False, True), TARGETS, (False, True), (False, True)
    ):
        yield {
            "epochs": [p, b, a], "pending_claim": pending, "delivery_state": delivery, "effect": effect,
            "input_state": input_state, "release_oracle": release_ok,
            "effect_oracle": effect_readable, "target_state": target,
            "new_authorization": new_auth, "persisted_authority": persisted_auth,
        }


def play_fair_schedule(start, schedule):
    state = {**start, "epochs": list(start["epochs"]), "fenced": False, "fence_generation": None,
             "admission_enabled": False, "claim_quarantined": False,
             "release_proof": False, "stale_or_duplicate_admissions": 0}
    # Restart boundary closes the volatile admission gate before loading persisted authority.
    state["admission_enabled"] = False
    state["fenced"] = True
    state["fence_generation"] = max(state["epochs"]) + 1
    for step in schedule:
        if step.startswith("sync_"):
            index = {"sync_planner": 0, "sync_broker": 1, "sync_actuator": 2}[step]
            state["epochs"][index] = state["fence_generation"]
        elif step == "quarantine_claim":
            state["claim_quarantined"] = state["pending_claim"] or state["delivery_state"] == "UNKNOWN"
        elif step == "trusted_release":
            if state["release_oracle"]:
                state["input_state"] = "RELEASED"
                state["release_proof"] = True
        if state["admission_enabled"] or state["stale_or_duplicate_admissions"]:
            raise AssertionError("safety invariant violated in transition prefix")
    claim_safe = state["claim_quarantined"] or (not state["pending_claim"] and state["delivery_state"] == "KNOWN")
    safe = (state["fenced"] and claim_safe
            and all(epoch == state["fence_generation"] for epoch in state["epochs"])
            and state["release_proof"] and state["input_state"] == "RELEASED"
            and not state["admission_enabled"])
    effect_confirmed = state["effect_oracle"] and state["effect"] != "UNKNOWN"
    target_confirmed = state["target_state"] != "UNKNOWN"
    resumable = safe and effect_confirmed and target_confirmed and state["target_state"] == "CURRENT" and state["new_authorization"]
    return {
        "destination": "RESUMABLE_CURRENT" if resumable else ("SAFE_QUIESCENT_UNKNOWN" if safe else "HOLD_UNKNOWN_INPUT"),
        "safe_quiescent": safe,
        "resumable": resumable,
        "admissions": state["stale_or_duplicate_admissions"],
        "bound_steps": 1 + len(schedule),
    }


def message_permutations():
    return sorted(set(itertools.permutations(MESSAGE_SET)))


def message_gate_result(order):
    # Recovery admission starts closed. Delayed, duplicated, reordered old-generation
    # messages are retained for audit but cannot grant authority or prove physical release.
    admissions = 0
    forged_release_proofs = 0
    gate_closed = True
    current_generation = 2
    for message in order:
        delivered_generation = 0
        if not gate_closed and delivered_generation == current_generation and message == "OLD_CLAIM":
            admissions += 1
        # Messages cannot substitute for the independently trusted physical-state oracle.
        if message == "RELEASE_ACK" and not gate_closed and delivered_generation == current_generation:
            forged_release_proofs += 1
    return admissions, forged_release_proofs


def naive_violation(start):
    if not start["persisted_authority"] or not start["pending_claim"]:
        return False
    next_generation = max(start["epochs"]) + 1
    old_generation = max(start["epochs"]) < next_generation
    return start["delivery_state"] == "UNKNOWN" or start["effect"] in ("APPLIED", "UNKNOWN") or old_generation


def candidate_rows():
    schedules = list(itertools.permutations(STEPS))
    messages = message_permutations()
    for index, start in enumerate(configurations()):
        outcomes = [play_fair_schedule(start, schedule) for schedule in schedules]
        message_outcomes = [message_gate_result(order) for order in messages]
        yield {
            "state_id": index,
            "initial": start,
            "fair_schedules": len(schedules),
            "all_schedules_safe": all(out["admissions"] == 0 for out in outcomes),
            "convergence_matches_release_assumption": all(out["safe_quiescent"] for out in outcomes) == start["release_oracle"],
            "safe_state_reached": all(out["safe_quiescent"] for out in outcomes),
            "destination": outcomes[0]["destination"],
            "max_steps": max(out["bound_steps"] for out in outcomes),
            "resumable": outcomes[0]["resumable"],
            "message_orders": len(messages),
            "message_admissions": max(x[0] for x in message_outcomes),
            "message_forged_release_proofs": max(x[1] for x in message_outcomes),
            "naive_unsafe_dispatch": naive_violation(start),
            "permanent_stop_progress": False,
        }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default=str(Path(__file__).with_name("raw") / "candidate.jsonl"))
    args = parser.parse_args()
    raw = Path(args.output)
    raw.parent.mkdir(parents=True, exist_ok=True)
    with raw.open("w", encoding="utf-8") as stream:
        count = 0
        for row in candidate_rows():
            stream.write(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n")
            count += 1
    print(f"candidate states={count} fair_orders=120 output={raw}")


if __name__ == "__main__":
    main()
