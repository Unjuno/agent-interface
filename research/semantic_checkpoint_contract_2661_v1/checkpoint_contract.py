"""Pure interruption-safe semantic checkpoint validator; never grants authority."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

STATUSES = {"CONFIRMED", "PROVISIONAL", "UNKNOWN"}
INVALIDATIONS = {"stale", "contradicted", "session_changed", "task_changed", "effect_changed"}

@dataclass(frozen=True)
class Decision:
    accepted: bool
    disposition: str
    reason: str
    fresh_authority_required: bool = True

def validate(value: Any, *, session_id: str, task_id: str, current_epoch: int,
             invalidations: set[str] | None = None) -> Decision:
    if type(value) is not dict:
        return Decision(False, "REFUSED", "checkpoint_object_required")
    required = {"session_id", "task_id", "epoch", "status", "evidence_ref", "resume_policy"}
    if set(value) != required:
        return Decision(False, "REFUSED", "exact_checkpoint_fields_required")
    if value["session_id"] != session_id or value["task_id"] != task_id:
        return Decision(False, "REFUSED", "binding_mismatch")
    if type(value["epoch"]) is not int or value["epoch"] < 0 or value["epoch"] > current_epoch:
        return Decision(False, "REFUSED", "non_monotonic_epoch")
    if value["status"] not in STATUSES:
        return Decision(False, "REFUSED", "unknown_status")
    if type(value["evidence_ref"]) is not str or not 1 <= len(value["evidence_ref"]) <= 256:
        return Decision(False, "REFUSED", "evidence_ref_required")
    policy = value["resume_policy"]
    if type(policy) is not dict or set(policy) != {"allowed", "requires_fresh_authority"}:
        return Decision(False, "REFUSED", "invalid_resume_policy")
    if policy["requires_fresh_authority"] is not True or policy["allowed"] is not True:
        return Decision(False, "REFUSED", "fresh_authority_policy_required")
    active = set(invalidations or ())
    if active & INVALIDATIONS:
        return Decision(False, "REFUSED", "checkpoint_invalidated")
    if value["status"] == "UNKNOWN":
        return Decision(True, "YIELD", "effect_unknown")
    if value["status"] == "PROVISIONAL":
        return Decision(True, "YIELD", "effect_provisional")
    return Decision(True, "ADMITTED_FOR_REVIEW", "effect_confirmed")
