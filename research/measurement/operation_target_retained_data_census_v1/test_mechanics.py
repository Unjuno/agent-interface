from census import load_fixture,evaluate
f=load_fixture(); r=evaluate(f)
assert r['decision']=='BLOCKED_DATA'
assert r['checks']['caller_visible_rows_present']
assert r['checks']['final_effect_oracle_present']
assert not r['checks']['operation_target_oracle']
assert not r['checks']['semantic_negative_rows']
assert not r['observed']['stale_binding_negative_is_operation_label']
print('MECHANICS_PASS')
