#!/usr/bin/env python3
"""Pure classifier for bounded claim outcome recovery.

No network I/O and no write authority. Missing/partial readback is UNKNOWN.
"""
FIELDS = ("owner_nonce", "task_id", "scope", "successor", "question_key")


def canonical(claim):
    return tuple(claim.get(k) for k in FIELDS)


def classify_first(observation):
    status = observation.get("status")
    if status in {"UNAVAILABLE", "AMBIGUOUS"}:
        return {"classification": "UNKNOWN_READBACK", "write": False}
    raise ValueError(f"unexpected first observation status: {status!r}")


def classify_full(candidate, register):
    claims = register.get("claims")
    if not isinstance(claims, list):
        return {"classification": "UNKNOWN_READBACK", "write": False}

    exact = [c for c in claims if canonical(c) == canonical(candidate)]
    if len(exact) == 1:
        return {"classification": "ALREADY_REGISTERED_SELF", "write": False}
    if len(exact) > 1:
        return {"classification": "UNKNOWN_READBACK", "write": False}

    same_owner = [c for c in claims if c.get("owner_nonce") == candidate.get("owner_nonce")]
    if same_owner:
        return {"classification": "CONFLICT_CONTENT_MISMATCH", "write": False}

    semantic = [
        c for c in claims
        if c.get("successor") == candidate.get("successor")
        and c.get("question_key") == candidate.get("question_key")
    ]
    if semantic:
        return {"classification": "CONFLICT_OTHER_OWNER", "write": False}

    return {"classification": "CLAIM_ABSENT", "write": False}
