"""Frozen finite schedule and identity rules for Issue #5846 successor T0."""

from __future__ import annotations

import hashlib
import json


def identity(fingerprint: str, target: str, label: str) -> str:
    """Bind semantic target as well as display label and fingerprint."""
    parts = (fingerprint, target, label)
    if any(not isinstance(part, str) or not part for part in parts):
        raise ValueError("identity fields must be non-empty strings")
    payload = json.dumps(parts, ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


CASES = (
    {"case": "pre_write", "policy": "A", "cut": "before_suppress"},
    {"case": "pre_write", "policy": "B", "cut": "before_suppress"},
    {"case": "pre_write", "policy": "C", "cut": "before_suppress"},
    {"case": "partial_split_write", "policy": "B", "cut": "after_candidate_write"},
    {"case": "pre_commit", "policy": "C", "cut": "before_commit"},
    {"case": "post_commit_pre_ack", "policy": "C", "cut": "after_commit_before_ack"},
    {"case": "acknowledged_restart", "policy": "A", "cut": "after_ack"},
    {"case": "acknowledged_restart", "policy": "B", "cut": "after_ack"},
    {"case": "acknowledged_restart", "policy": "C", "cut": "after_ack"},
    {"case": "new_generation_same_fingerprint", "policy": "C", "cut": "new_generation"},
    {"case": "changed_target_same_label", "policy": "C", "cut": "changed_target"},
    {"case": "reactivation", "policy": "C", "cut": "reactivation"},
    {"case": "expiry_gc_tombstone", "policy": "C", "cut": "expiry_gc_tombstone"},
    {"case": "malformed_record", "policy": "C", "cut": "malformed"},
    {"case": "repeated_restart", "policy": "C", "cut": "restart_twice"},
)


def schedule_sha256() -> str:
    data = json.dumps(CASES, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(data).hexdigest()
