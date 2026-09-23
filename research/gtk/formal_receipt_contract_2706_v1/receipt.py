REQUIRED = (
    "session_id", "window_id", "observation_revision", "binding_revision",
    "input_ledger", "effect_receipt", "cleanup", "authority_grants",
    "replay_count", "raw_event_sha256", "scorer_source_sha256",
)

def validate(receipt):
    missing = [key for key in REQUIRED if key not in receipt]
    if missing:
        return {"status": "HOLD_LIVE_RECEIPT_EMISSION_INCOMPLETE", "missing": missing}
    if receipt["replay_count"] != 0:
        return {"status": "FAIL_REPLAY_COUNT", "missing": []}
    if not receipt["session_id"] or not receipt["window_id"]:
        return {"status": "FAIL_IDENTITY_EMPTY", "missing": []}
    return {"status": "PASS_RECEIPT_SCHEMA_SCOPED", "missing": []}
