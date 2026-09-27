import hashlib
import json


def fingerprint(payload):
    return hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def decide(state, request):
    receipts = state["receipts"]
    rid = request["request_id"]
    fp = fingerprint(request["payload"])
    if rid in receipts:
        prior = receipts[rid]
        if prior["fingerprint"] == fp:
            return {"decision": "REPLAY_APPLIED", "write": False, "new_effects": 0}
        return {"decision": "CONFLICT", "write": False, "new_effects": 0}
    if state["policy"] == "generation_fenced" and request["generation"] != state["accepted_generation"]:
        return {"decision": "FENCED_STALE", "write": False, "new_effects": 0}
    return {"decision": "APPLY", "write": True, "new_effects": 1, "fingerprint": fp}
