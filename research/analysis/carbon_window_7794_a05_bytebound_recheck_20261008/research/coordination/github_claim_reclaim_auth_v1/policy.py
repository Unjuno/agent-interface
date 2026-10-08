import base64
import hashlib
import hmac
import json

_SHA256_DIGESTINFO_PREFIX = bytes.fromhex("3031300d060960864801650304020105000420")

def canonical_record(record):
    return json.dumps(record, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("ascii")

def _rsa_pkcs1v15_sha256_verify(record, signature_b64, key):
    try:
        sig = base64.b64decode(signature_b64, validate=True)
        n = int(key["n_hex"], 16)
        e = int(key["e"])
        k = (n.bit_length() + 7) // 8
        if len(sig) != k:
            return False
        s = int.from_bytes(sig, "big")
        if s >= n:
            return False
        em = pow(s, e, n).to_bytes(k, "big")
        digest = hashlib.sha256(canonical_record(record)).digest()
        t = _SHA256_DIGESTINFO_PREFIX + digest
        ps_len = k - len(t) - 3
        if ps_len < 8:
            return False
        expected = b"\x00\x01" + (b"\xff" * ps_len) + b"\x00" + t
        return hmac.compare_digest(em, expected)
    except (KeyError, TypeError, ValueError):
        return False

def authorize_reclaim(current, evidence, trust):
    keys = {k["key_id"]: k for k in trust["keys"]}
    key = keys.get(evidence.get("key_id"))
    if key is None:
        return {"decision": "HOLD_UNKNOWN", "reason": "UNKNOWN_KEY", "write": False}

    record = evidence.get("record")
    if not isinstance(record, dict):
        return {"decision": "HOLD_UNKNOWN", "reason": "MALFORMED_RECORD", "write": False}

    if key.get("role") != record.get("issuer_role"):
        return {"decision": "HOLD_UNKNOWN", "reason": "ROLE_KEY_MISMATCH", "write": False}

    if not _rsa_pkcs1v15_sha256_verify(record, evidence.get("signature_b64", ""), key):
        return {"decision": "HOLD_UNKNOWN", "reason": "AUTH_FAILED", "write": False}

    exact = (
        record.get("owner_id") == current.get("owner_id")
        and record.get("generation") == current.get("generation")
        and record.get("claim_id") == current.get("claim_id")
    )
    if not exact:
        return {"decision": "HOLD_UNKNOWN", "reason": "BINDING_MISMATCH", "write": False}

    role = record.get("issuer_role")
    event = record.get("event")
    allowed = (role == "OWNER" and event == "RELINQUISHED") or (
        role == "SUPERVISOR" and event == "TERMINATED"
    )
    if not allowed:
        return {"decision": "HOLD_UNKNOWN", "reason": "EVENT_NOT_AUTHORIZED", "write": False}

    return {"decision": "ALLOW_RECLAIM", "reason": "AUTHENTIC_EXACT_TERMINAL", "write": True}

def fence(current, writer_owner_id, writer_generation):
    if (
        current.get("owner_id") == writer_owner_id
        and current.get("generation") == writer_generation
    ):
        return "CURRENT_OWNER"
    return "FENCED_STALE"
