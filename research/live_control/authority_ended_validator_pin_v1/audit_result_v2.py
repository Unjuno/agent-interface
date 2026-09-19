from __future__ import annotations
import hashlib,json
from pathlib import Path
H=Path(__file__).resolve().parent
r=json.loads((H/'formal-result-v2.json').read_text())
assert r['schema']=='authority-ended-validator-source-pin-v2-formal'
assert r['result_id']=='authority-ended-validator-source-pin-v2-20260916-01'
assert r['formal_retries']==0 and r['hard_gate_pass'] is True
assert r['decision']=='RETAIN_SOURCE_PIN_CANDIDATE'
rows={x['case']:x for x in r['rows']}
assert len(rows)==15 and all(x['pass'] is True for x in rows.values())
base=rows['baseline_unpinned_drift_reproduced']['detail']
assert base['schema']=='authority-ended-durable-token-state-v2'
assert set(base['entries'])=={'baseline-v1','baseline-v2'}
shape=rows['token_state_shape_unchanged']['detail']
assert set(shape)=={'schema','entries'} and shape['schema']=='authority-ended-durable-token-state-v2'
pin=rows['sidecar_records_actual_source_hash']['detail']
assert set(pin)=={'schema','validator_id','validator_sha256','function_name'}
assert pin['schema']=='authority-ended-validator-source-pin-v2'
assert pin['validator_id']=='bridge-v2-two-capture'
assert pin['validator_sha256']==r['source_sha256']['bridge_v2_semantic_snapshot.py']
assert pin['function_name']=='to_caller_execution_decision'
for k in ['validator_id_downgrade_rejected','same_label_wrong_source_rejected','same_source_wrong_function_rejected','v1_to_v2_reopen_rejected']:
    assert rows[k]['detail']['error']=='validator pin mismatch',k
assert rows['state_without_sidecar_rejected']['detail']['error']=='existing token state missing validator pin'
assert rows['corrupt_sidecar_rejected']['detail']['error']=='unreadable validator pin'
assert rows['duplicate_rejected']['detail']['error']=='authority_end_id already exists'
assert rows['consume_restart_remains_consumed']['detail']['entry']['status']=='consumed'
assert rows['consume_restart_remains_consumed']['detail']['reject']['error']=='authority_end_id already consumed'
cr=rows['sidecar_only_crash_recovers_same_source_only']['detail']
assert cr['crash']['type']=='InjectedInitCrash' and cr['mismatch']['error']=='validator pin mismatch' and cr['state_exists'] is True
expected_deps={
'durable_token_state_v2.py':'72a3481653cf9c41ec1a03f4c7a7bf1c482ff69468b5d92986bad8cf814950b4',
'authority_ended_bridge_v1.py':'2c9684d8f731b36469df06532fc2ce566716c0380002d18da1f317814f7acb1e'}
assert r['dependency_sha256']==expected_deps
for n,h in r['source_sha256'].items():
    assert hashlib.sha256((H/n).read_bytes()).hexdigest()==h,(n,h)
print('PASS independent source-pinned validator audit')
