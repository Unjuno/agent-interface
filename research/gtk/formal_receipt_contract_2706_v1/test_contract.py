from receipt import validate

base = {
    "session_id": "s1", "window_id": "w1", "observation_revision": 1,
    "binding_revision": 1, "input_ledger": [], "effect_receipt": {},
    "cleanup": {"status": "neutral"}, "authority_grants": [],
    "replay_count": 0, "raw_event_sha256": "a"*64,
    "scorer_source_sha256": "b"*64,
}
assert validate(base)["status"] == "PASS_RECEIPT_SCHEMA_SCOPED"
assert validate({**base, "effect_receipt": None})["status"] == "PASS_RECEIPT_SCHEMA_SCOPED"
assert validate({k:v for k,v in base.items() if k != "window_id"})["status"] == "HOLD_LIVE_RECEIPT_EMISSION_INCOMPLETE"
assert validate({**base, "replay_count": 1})["status"] == "FAIL_REPLAY_COUNT"
print("PASS receipt contract 4 cases; live runner emission not tested")
