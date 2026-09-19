import base64
import hashlib
import hmac
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PREFIX = bytes.fromhex("3031300d060960864801650304020105000420")

def load(name):
    return json.loads((ROOT / name).read_text())

def canonical(record):
    return json.dumps(record, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("ascii")

def verify(record, signature_b64, key):
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
        digest = hashlib.sha256(canonical(record)).digest()
        t = PREFIX + digest
        ps = b"\xff" * (k - len(t) - 3)
        expected = b"\x00\x01" + ps + b"\x00" + t
        return hmac.compare_digest(em, expected)
    except (KeyError, TypeError, ValueError):
        return False

keys_doc = load("keys.json")
evidence = load("evidence.json")["cases"]
result = load("result.json")
keys = {k["key_id"]: k for k in keys_doc["keys"]}

allowed_key_fields = {"key_id", "role", "algorithm", "n_hex", "e"}
assert all(set(k) == allowed_key_fields for k in keys_doc["keys"])
assert set(keys) == {"owner-key-009", "supervisor-key-009"}

assert verify(evidence["authenticated_owner_exact"]["record"], evidence["authenticated_owner_exact"]["signature_b64"], keys["owner-key-009"])
assert verify(evidence["authenticated_supervisor_exact"]["record"], evidence["authenticated_supervisor_exact"]["signature_b64"], keys["supervisor-key-009"])
assert not verify(evidence["forged_owner_signature"]["record"], evidence["forged_owner_signature"]["signature_b64"], keys["owner-key-009"])
assert not verify(evidence["tampered_generation_replay"]["record"], evidence["tampered_generation_replay"]["signature_b64"], keys["owner-key-009"])
assert evidence["unknown_key"]["key_id"] not in keys

owner = load("register_owner.json")
supervisor = load("register_supervisor.json")
forged = load("register_forged.json")
replay = load("register_replay.json")
unknown = load("register_unknown_key.json")

assert (owner["owner_id"], owner["generation"], owner["state"], owner["revision"]) == ("owner-B-009", 2, "ACTIVE", 1)
assert (supervisor["owner_id"], supervisor["generation"], supervisor["state"], supervisor["revision"]) == ("owner-C-009", 2, "ACTIVE", 1)
for reg in (forged, replay, unknown):
    assert (reg["owner_id"], reg["generation"], reg["state"], reg["revision"]) == ("owner-A-009", 1, "UNKNOWN", 0)

assert result["decision"] == "PASS_AUTHENTICATED_RECLAIM_SCOPED"
assert result["totals"] == {
    "fresh_sha_retries_by_fenced_writers": 0,
    "late_old_generation_attempts": 2,
    "negative_case_writes": 0,
    "post_reclaim_readbacks": 2,
    "stale_sha_409s": 2,
    "successful_reclaim_commits": 2,
}
assert result["cases"]["forged_owner_signature"]["auth_reason"] == "AUTH_FAILED"
assert result["cases"]["tampered_generation_replay"]["auth_reason"] == "AUTH_FAILED"
assert result["cases"]["unknown_key"]["auth_reason"] == "UNKNOWN_KEY"

print(json.dumps({
    "ok": True,
    "decision": result["decision"],
    "verified_valid_signatures": 2,
    "rejected_invalid_auth_controls": 3,
    "negative_case_writes": 0,
    "stale_sha_409s": 2,
    "fresh_sha_retries": 0
}, sort_keys=True))
