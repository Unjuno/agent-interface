"""Candidate merge and operation classification for Issue #5547 T0."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class State:
    evidence: frozenset[str] = frozenset()
    admitted_claims: frozenset[str] = frozenset()
    revoked_claims: frozenset[str] = frozenset()
    authority_epoch: int = 0
    quota_reservations: frozenset[str] = frozenset()
    effect_committed: bool = False


def join(left: State, right: State) -> State:
    return State(
        evidence=left.evidence | right.evidence,
        admitted_claims=left.admitted_claims | right.admitted_claims,
        revoked_claims=left.revoked_claims | right.revoked_claims,
        authority_epoch=max(left.authority_epoch, right.authority_epoch),
        quota_reservations=left.quota_reservations | right.quota_reservations,
        effect_committed=left.effect_committed or right.effect_committed,
    )


def invariant(state: State) -> bool:
    return (
        len(state.quota_reservations) <= 1
        and not (state.admitted_claims & state.revoked_claims)
        and (not state.effect_committed or (state.authority_epoch == 1 and "e0" in state.evidence))
    )


LABELS = {
    "ADD_EVIDENCE": "monotone_safe",
    "REVOKE_CLAIM": "monotone_safe",
    "RECORD_IDEMPOTENT_RECEIPT": "monotone_safe",
    "REFRESH_EPOCH": "coordination_required",
    "RESERVE_QUOTA": "coordination_required",
    "COMMIT_EFFECT": "coordination_required",
}


def classify(operation: str) -> str:
    return LABELS.get(operation, "coordination_required")


def delta(operation: str, value: str | None = None) -> State:
    if operation == "ADD_EVIDENCE":
        return State(evidence=frozenset({str(value)}))
    if operation == "REVOKE_CLAIM":
        return State(revoked_claims=frozenset({str(value)}))
    if operation == "RECORD_IDEMPOTENT_RECEIPT":
        return State(evidence=frozenset({f"receipt:{value}"}))
    if operation == "REFRESH_EPOCH":
        return State(authority_epoch=1)
    if operation == "RESERVE_QUOTA":
        return State(quota_reservations=frozenset({f"{value}"}))
    if operation == "COMMIT_EFFECT":
        return State(effect_committed=True)
    raise ValueError(f"unknown operation: {operation}")
