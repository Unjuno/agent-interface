#!/usr/bin/env python3
"""Finite interruption-resumption policy comparison for Issue #5404."""

from __future__ import annotations

import itertools
import json
from pathlib import Path

INTERRUPTIONS = (
    "before_action",
    "during_observation",
    "after_timeout",
    "after_authority_change",
    "after_handoff",
)
FAULTS = ("none", "stale_evidence", "authority_revoked", "geometry_changed", "duplicate_receipt")
IDEMPOTENCY = (False, True)
POLICIES = ("OPAQUE_SUMMARY", "FULL_REPLAY", "TYPED_PACKET")


def make_scenario(interruption, fault, idempotent):
    action_status = {
        "before_action": "NOT_EMITTED",
        "during_observation": "NOT_EMITTED",
        "after_timeout": "UNKNOWN",
        "after_authority_change": "NOT_EMITTED",
        "after_handoff": "NOT_EMITTED",
    }[interruption]
    committed = interruption == "after_timeout" or fault == "duplicate_receipt"
    authority_generation = 8 if interruption == "after_authority_change" else 7
    execution_generation = 5 if interruption == "after_handoff" else 4
    return {
        "interruption": interruption,
        "fault": fault,
        "idempotent": idempotent,
        "packet_execution_generation": 4,
        "current_execution_generation": execution_generation,
        "packet_authority_generation": 7,
        "current_authority_generation": authority_generation,
        "authority_active": interruption != "after_authority_change" and fault != "authority_revoked",
        "handoff_accepted": interruption != "after_handoff",
        "packet_evidence_generation": 12,
        "current_evidence_generation": 13 if fault == "stale_evidence" else 12,
        "observation_complete": interruption != "during_observation",
        "packet_geometry_generation": 2,
        "current_geometry_generation": 3 if fault == "geometry_changed" else 2,
        "action_status": "COMMITTED" if committed and action_status != "UNKNOWN" else action_status,
        "effect_committed": committed,
        "action_id": "effect-17",
    }


def current_gates(s):
    return {
        "authority": s["authority_active"] and s["current_authority_generation"] == s["packet_authority_generation"],
        "handoff": s["handoff_accepted"] and s["current_execution_generation"] == s["packet_execution_generation"],
        "evidence": s["observation_complete"] and s["current_evidence_generation"] == s["packet_evidence_generation"],
        "geometry": s["current_geometry_generation"] == s["packet_geometry_generation"],
    }


def typed_packet(s):
    gates = current_gates(s)
    detected = not all(gates.values()) or s["effect_committed"]
    if not gates["authority"] or not gates["handoff"]:
        return {"decision": "ABSTAIN", "attempts": 0, "new_effects": 0, "unsafe": False, "steps": 1, "detected": detected}
    if s["effect_committed"]:
        return {"decision": "RECONCILE_RECEIPT", "attempts": 0, "new_effects": 0, "unsafe": False, "steps": 2 if s["action_status"] == "UNKNOWN" else 1, "detected": detected}
    steps = 1
    decision = "RESUME"
    if not gates["evidence"]:
        steps += 1
        decision = "REOBSERVE_THEN_RESUME"
    if not gates["geometry"]:
        steps += 1
        decision = "REGROUND_THEN_RESUME"
    return {"decision": decision, "attempts": 1, "new_effects": 1, "unsafe": False, "steps": steps + 1, "detected": detected}


def full_replay(s):
    gates = current_gates(s)
    steps = 6
    if not gates["authority"] or not gates["handoff"]:
        return {"decision": "ABSTAIN_AFTER_REPLAY", "attempts": 0, "new_effects": 0, "unsafe": False, "steps": steps + 1, "detected": True}
    if s["effect_committed"]:
        return {"decision": "RECONCILE_RECEIPT_AFTER_REPLAY", "attempts": 0, "new_effects": 0, "unsafe": False, "steps": steps + 1, "detected": True}
    if not gates["evidence"]:
        steps += 1
    if not gates["geometry"]:
        steps += 2
    return {"decision": "RESUME_AFTER_REPLAY", "attempts": 1, "new_effects": 1, "unsafe": False, "steps": steps + 1, "detected": True}


def opaque_summary(s):
    gates = current_gates(s)
    attempts = 1
    unsafe = not all(gates.values()) or (s["effect_committed"] and not s["idempotent"])
    new_effects = 0 if s["effect_committed"] and s["idempotent"] else attempts
    return {"decision": "RESUME_FROM_SUMMARY", "attempts": attempts, "new_effects": new_effects, "unsafe": unsafe, "steps": 1, "detected": False}


def outcome(policy, scenario):
    return {
        "OPAQUE_SUMMARY": opaque_summary,
        "FULL_REPLAY": full_replay,
        "TYPED_PACKET": typed_packet,
    }[policy](scenario)


def scenarios():
    for interruption, fault, idempotent in itertools.product(INTERRUPTIONS, FAULTS, IDEMPOTENCY):
        yield make_scenario(interruption, fault, idempotent)


def main():
    rows = []
    packet_unsafe = 0
    opaque_unsafe = 0
    benign_packet_steps = []
    benign_replay_steps = []
    detected = 0
    for index, scenario in enumerate(scenarios()):
        results = {policy: outcome(policy, scenario) for policy in POLICIES}
        packet_unsafe += int(results["TYPED_PACKET"]["unsafe"])
        opaque_unsafe += int(results["OPAQUE_SUMMARY"]["unsafe"])
        if scenario["interruption"] == "before_action" and scenario["fault"] == "none":
            benign_packet_steps.append(results["TYPED_PACKET"]["steps"])
            benign_replay_steps.append(results["FULL_REPLAY"]["steps"])
        detected += int(results["TYPED_PACKET"]["detected"])
        rows.append({"kind": "scenario", "scenario_id": index, "context": scenario, "outcomes": results})
    header = {
        "kind": "header",
        "allocation": "typed-resumption-5404-t0-orbstack-20260930-01",
        "interruptions": list(INTERRUPTIONS),
        "faults": list(FAULTS),
        "idempotency": list(IDEMPOTENCY),
        "policies": list(POLICIES),
        "scenario_count": len(rows),
        "policy_outcome_count": len(rows) * len(POLICIES),
        "packet_unsafe_admissions": packet_unsafe,
        "opaque_unsafe_admissions": opaque_unsafe,
        "packet_invalidation_detections": detected,
        "packet_invalidation_denominator": len(rows) - 2,
        "benign_packet_steps_mean": sum(benign_packet_steps) / len(benign_packet_steps),
        "benign_full_replay_steps_mean": sum(benign_replay_steps) / len(benign_replay_steps),
        "formal_invocations": 1,
    }
    out = Path("/out/formal.jsonl")
    out.write_text("".join(json.dumps(r, sort_keys=True, separators=(",", ":")) + "\n" for r in [header] + rows), encoding="utf-8")
    print(json.dumps({k: header[k] for k in (
        "scenario_count", "policy_outcome_count", "packet_unsafe_admissions",
        "opaque_unsafe_admissions", "packet_invalidation_detections",
        "benign_packet_steps_mean", "benign_full_replay_steps_mean", "formal_invocations",
    )}, sort_keys=True))


if __name__ == "__main__":
    main()
