from ledger import validate

base = dict(session_id="s1", app="calc", window_id=1, pid=10, display=":1",
            surface_generation=1, observation_hash="a", capability_generation=1,
            invalidation_reason="focus", recovery_mode="observe_only",
            authority_grants=[], input_receipt={}, effect_receipt={}, cleanup={"status":"neutral"})
rows=[{**base,"transition_seq":i} for i in range(4)]
assert validate(rows) == "PASS_LEDGER_CONTRACT_SCOPED"
assert validate([]) == "HOLD_NO_INTEGRATED_TRACE"
assert validate([{**rows[0],"transition_seq":2}, *rows[1:]]) == "FAIL_TRANSITION_ORDER"
assert validate([{**rows[0],"authority_grants":["g"]}, *rows[1:]]) == "FAIL_AUTHORITY_LEAK"
assert validate([{k:v for k,v in rows[0].items() if k!="effect_receipt"}, *rows[1:]]) .startswith("HOLD_LEDGER_FIELDS_MISSING")
print("PASS ledger contract 5 cases; no live session executed")
