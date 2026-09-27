"""Pure handoff capsule validator; no authority or side effects."""
from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Mapping

@dataclass(frozen=True)
class CapsuleDecision:
    usable: bool
    reason: str
    requires_fresh_authority: bool = True

def validate_capsule(
    capsule: Mapping[str, Any],
    *,
    session_id: str,
    task_id: str,
    now_epoch: int,
) -> CapsuleDecision:
    if not isinstance(capsule, Mapping):
        return CapsuleDecision(False, "malformed")
    if capsule.get("session_id") != session_id:
        return CapsuleDecision(False, "session_mismatch")
    if capsule.get("task_id") != task_id:
        return CapsuleDecision(False, "task_mismatch")
    if capsule.get("capsule_id") in (None, ""):
        return CapsuleDecision(False, "missing_capsule_id")
    if not isinstance(capsule.get("uncertainty"), list):
        return CapsuleDecision(False, "missing_uncertainty")
    if capsule.get("replay_prohibited") is not True:
        return CapsuleDecision(False, "replay_not_prohibited")
    if capsule.get("authority_transfer") is not False:
        return CapsuleDecision(False, "authority_transfer_forbidden")
    if capsule.get("authority_status") != "REQUIRE_FRESH":
        return CapsuleDecision(False, "fresh_authority_required")
    if not isinstance(capsule.get("expires_at"), int):
        return CapsuleDecision(False, "missing_expiry")
    if capsule["expires_at"] <= now_epoch:
        return CapsuleDecision(False, "expired")
    if capsule.get("contradictory") is True:
        return CapsuleDecision(False, "contradictory")
    if capsule.get("semantic_status") not in {"IN_PROGRESS", "PARTIAL", "UNKNOWN"}:
        return CapsuleDecision(False, "invalid_semantic_status")
    return CapsuleDecision(True, "advisory_context_only")
