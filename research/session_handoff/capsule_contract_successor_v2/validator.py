"""Pure validator; it never transfers or grants live authority."""
from __future__ import annotations
from typing import Any, Mapping

MAX_TTL = 300
REQUIRED = ("session_id", "task_id", "observed_at", "expires_at", "uncertainty", "replay_prohibited", "authority_status", "fresh_authority_required")

def validate_capsule(capsule: Mapping[str, Any], *, now: int) -> tuple[bool, str]:
    if not isinstance(capsule, Mapping): return False, "not_mapping"
    if any(k not in capsule for k in REQUIRED): return False, "missing_field"
    if not all(isinstance(capsule[k], str) and capsule[k] for k in ("session_id", "task_id", "uncertainty", "authority_status")): return False, "identity_or_status"
    if type(capsule["observed_at"]) is not int or type(capsule["expires_at"]) is not int: return False, "time_type"
    if capsule["expires_at"] < capsule["observed_at"] or capsule["expires_at"] - capsule["observed_at"] > MAX_TTL: return False, "ttl"
    if not (capsule["observed_at"] <= now <= capsule["expires_at"]): return False, "stale"
    if capsule["uncertainty"] == "" or capsule["replay_prohibited"] is not True: return False, "unsafe_replay_or_uncertainty"
    if capsule["authority_status"] != "NONE" or capsule["fresh_authority_required"] is not True: return False, "authority"
    if any(k in capsule for k in ("authority_token", "lease", "input_grant")): return False, "live_authority_present"
    return True, "accepted_advisory_only"
