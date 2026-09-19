import hashlib
import json
from pathlib import Path

ALLOWED = {
    "SETUP_DOCTOR": "diagnostic",
    "MODEL_ATTEMPT": "model_attempt",
    "OBSERVATION": "observation",
    "GUARDED_DISPATCH": "dispatch",
    "REFUSAL": "refusal",
    "USEFUL_EFFECT": "effect",
    "STALE_INVALIDATION": "invalidation",
    "REPAIR": "repair",
    "TERMINAL_RELEASE": "release",
    "CLEANUP_FAILURE": "runtime_failed",
}

def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()

def translate(row):
    if type(row) is not dict or row.get("state") not in ALLOWED:
        raise ValueError("UNKNOWN_LIFECYCLE_STATE")
    if row.get("authority_granted") is not False:
        raise ValueError("AUTHORITY_NOT_FALSE")
    if row.get("raw_ref") != row.get("raw_sha256"):
        raise ValueError("RAW_REFERENCE_MISMATCH")
    if type(row.get("task_success_distinct")) is not bool:
        raise ValueError("TASK_SUCCESS_FIELD_MISSING")
    return {
        "schema": "agent-interface/golden-v3-cli-adapter-v1",
        "status": ALLOWED[row["state"]],
        "task_success": row.get("task_success"),
        "program_completed": row.get("program_completed"),
        "partial_effects": row.get("partial_effects", []),
        "cleanup_error": row.get("cleanup_error"),
        "raw_ref": row["raw_ref"],
        "raw_sha256": row["raw_sha256"],
        "authority_granted": False,
    }

def replay(fixture):
    raw = json.dumps(fixture, sort_keys=True, separators=(",", ":"))
    raw_sha = hashlib.sha256(raw.encode()).hexdigest()
    if fixture.get("raw_sha256") != raw_sha:
        raise ValueError("FIXTURE_DIGEST_MISMATCH")
    return [translate(row) for row in fixture["rows"]]
