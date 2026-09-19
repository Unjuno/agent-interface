from __future__ import annotations
import hashlib,json
from pathlib import Path
H=Path(__file__).resolve().parent
r=json.loads((H/'formal-result-v3.json').read_text())
assert r['schema']=='authority-ended-validator-byte-binding-v3-formal'
assert r['result_id']=='authority-ended-validator-byte-binding-v3-20260916-02'
assert r['formal_retries']==0 and r['hard_gate_pass'] is True
assert r['decision']=='RETAIN_BYTE_BOUND_VALIDATOR_V3'
rows={x['case']:x for x in r['rows']}
assert len(rows)==17 and all(x['pass'] is True for x in rows.values())
v2=rows['v2_hash_to_load_toctou_reproduced']['detail']
assert v2['outcome']=={'status':'ISSUED'} and v2['pin_sha']==v2['A_sha'] and v2['final_file_sha']==v2['B_sha'] and v2['A_sha']!=v2['B_sha']
v3=rows['v3_executes_exact_hashed_bytes_under_same_replacement']['detail']
assert v3['outcome']['type']=='ValueError' and v3['outcome']['error']=='A rejects'
assert v3['pin_sha']==v3['A_sha'] and v3['final_file_sha']==v3['B_sha'] and v3['A_sha']!=v3['B_sha']
shape=rows['token_state_shape_unchanged']['detail'];assert set(shape)=={'schema','entries'} and shape['schema']=='authority-ended-durable-token-state-v2'
pin=rows['v3_sidecar_binds_actual_hash_and_function']['detail'];assert pin['schema']=='authority-ended-validator-byte-pin-v3' and pin['function_name']=='to_caller_execution_decision' and pin['validator_sha256']==r['source_sha256']['bridge_v2_semantic_snapshot.py']
for k in ['v3_changed_source_reopen_rejected','v3_wrong_function_rejected','v3_v1_to_v2_reopen_rejected']:
 assert rows[k]['detail']['error']=='validator pin mismatch',k
assert rows['v3_syntax_error_rejected']['detail']['error']=='validator source execution failed'
assert rows['v3_missing_function_rejected']['detail']['error']=='validator callable missing'
assert rows['v3_state_without_sidecar_rejected']['detail']['error']=='existing token state missing validator pin'
assert rows['v3_corrupt_sidecar_rejected']['detail']['error']=='unreadable validator pin'
assert rows['v3_duplicate_rejected']['detail']['error']=='authority_end_id already exists'
assert rows['v3_consume_restart_remains_consumed']['detail']['entry']['status']=='consumed'
cr=rows['v3_sidecar_only_crash_same_bytes_only']['detail'];assert cr['crash']['type']=='InjectedInitCrash' and cr['mismatch']['error']=='validator pin mismatch' and cr['state_exists'] is True
for n,h in r['source_sha256'].items():assert hashlib.sha256((H/n).read_bytes()).hexdigest()==h,(n,h)
expected={'validator_source_pinned_ledger_v2.py':'189bd81dd884b7840b31ef01e453e62a6d850f5c14dbe925bce8fb4b016558d2','durable_token_state_v2.py':'72a3481653cf9c41ec1a03f4c7a7bf1c482ff69468b5d92986bad8cf814950b4','authority_ended_bridge_v1.py':'2c9684d8f731b36469df06532fc2ce566716c0380002d18da1f317814f7acb1e'}
assert r['dependency_sha256']==expected
print('PASS independent byte-bound validator v3 audit')
