#!/usr/bin/env python3
"""Pure policy for the scoped GitHub claim-generation fencing fixture."""


def classify_actor(current, actor):
    if actor["generation"] != current["generation"]:
        return {"disposition": "FENCED_STALE", "write": False}
    if actor["owner_id"] != current["owner_id"]:
        return {"disposition": "NOT_CURRENT_OWNER", "write": False}
    return {"disposition": "CURRENT_OWNER", "write": True}


def validate_reclaim(current, replacement, fixture_authorized):
    if not fixture_authorized:
        return False
    return replacement["generation"] == current["generation"] + 1
