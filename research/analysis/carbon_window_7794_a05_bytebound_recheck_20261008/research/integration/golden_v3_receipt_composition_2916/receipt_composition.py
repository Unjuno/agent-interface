"""Additive receipt composition boundary for golden-v3.

This module is deliberately authority-neutral: it validates provenance and
freshness before a caller invokes the existing native dispatcher, and it treats
the independent effect score as evidence rather than authority.
"""
from __future__ import annotations
from hashlib import sha256
from typing import Any, Mapping

SCHEMA = "golden-v3-receipt-composition-v1"
_HEX64 = set("0123456789abcdef")

def _digest(value: Any) -> str:
    import json
    raw = json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    return sha256(raw).hexdigest()

def compose(
    *,
    admission: Mapping[str, Any],
    source: Mapping[str, Any],
    dispatch: Mapping[str, Any] | None,
    effect: Mapping[str, Any] | None,
    current: Mapping[str, Any],
) -> dict[str, Any]:
    """Return a typed decision; never emits input or grants authority."""
    reasons: list[str] = []
    if admission.get("schema") != "visual-target-admission-v1":
        reasons.append("ADMISSION_SCHEMA")
    if admission.get("disposition") != "TARGET_REFERENCE_ONLY":
        reasons.append("ADMISSION_NOT_ACCEPTED")
    if source.get("schema") != "source-identity-v1":
        reasons.append("SOURCE_SCHEMA")
    digest = source.get("source_sha256")
    if not isinstance(digest, str) or len(digest) != 64 or any(c not in _HEX64 for c in digest.lower()):
        reasons.append("SOURCE_DIGEST")
    for key in ("session_id", "target_id", "observation_seq", "binding_revision"):
        if admission.get(key) != current.get(key):
            reasons.append("ADMISSION_STALE_" + key.upper())
    if source.get("session_id") != current.get("session_id"):
        reasons.append("SOURCE_SESSION")
    if dispatch is not None and dispatch.get("authority_granted") is True:
        reasons.append("AUTHORITY_CONTRADICTION")
    if dispatch is not None and dispatch.get("status") in {"refused", "invalid_request"}:
        reasons.append("DISPATCH_REFUSED")
    if effect is None:
        reasons.append("EFFECT_RECEIPT_MISSING")
    else:
        for key in ("session_id", "target_id", "intent_id"):
            if effect.get(key) != current.get(key):
                reasons.append("EFFECT_SCOPE_" + key.upper())
        if type(effect.get("task_success")) is not bool:
            reasons.append("EFFECT_SCORE_MISSING")
    accepted = not reasons
    return {
        "schema": SCHEMA,
        "decision": "ACCEPT_FOR_ORDINARY_ADMISSION" if accepted else "REFUSE",
        "authority_granted": False,
        "effect_score": effect.get("task_success") if accepted and effect else None,
        "reasons": reasons,
        "receipt_digest": _digest({"admission": dict(admission), "source": dict(source),
                                   "dispatch": dispatch, "effect": effect, "current": dict(current)}),
    }
