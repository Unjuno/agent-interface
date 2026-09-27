from __future__ import annotations
import json, hashlib

def canon(obj):
    return json.dumps(obj, sort_keys=True, separators=(",", ":")) + "\n"

def digest_members(members):
    payload = canon({"members": sorted(members)}).encode()
    return hashlib.sha256(payload).hexdigest()

def valid_transition(state, expected_digest, expected_generation):
    return state["membership_digest"] == expected_digest and state["active_generation"] == expected_generation
