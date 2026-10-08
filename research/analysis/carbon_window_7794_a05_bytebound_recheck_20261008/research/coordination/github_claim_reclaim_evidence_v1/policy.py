#!/usr/bin/env python3
"""Pure fixture policy for evidence-bound claim reclaim."""


def reclaim_decision(register, evidence):
    if evidence.get("kind") == "elapsed_only":
        return "HOLD_UNKNOWN"

    required = ("owner_id", "generation", "claim_id")
    if any(k not in evidence for k in required):
        return "HOLD_UNKNOWN"
    if any(evidence[k] != register[k] for k in required):
        return "HOLD_UNKNOWN"

    if evidence.get("source") == "owner" and evidence.get("terminal_status") == "RELINQUISHED":
        return "ALLOW_RECLAIM"
    if evidence.get("source") == "supervisor" and evidence.get("terminal_status") == "TERMINATED":
        return "ALLOW_RECLAIM"
    return "HOLD_UNKNOWN"


def writer_decision(register, owner_id, generation):
    if owner_id == register["owner_id"] and generation == register["generation"]:
        return "CURRENT_OWNER"
    return "FENCED_STALE"
