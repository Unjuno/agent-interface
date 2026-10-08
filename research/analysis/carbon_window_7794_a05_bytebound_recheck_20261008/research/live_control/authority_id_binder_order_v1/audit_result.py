from __future__ import annotations
import hashlib,json
from pathlib import Path
H=Path(__file__).resolve().parent
R=json.loads((H/'formal-result.json').read_text())
expected_cases=[
 'direct_ledger_persists_forged_nonempty_id',
 'prebind_rejects_forged_id',
 'prebind_missing_id_uses_runtime_token',
 'restart_recovers_prebound_runtime_token',
 'post_issue_binding_is_too_late',
 'prebind_release_interruption_mismatch_rejects_before_state',
]
errors=[]
if R.get('schema')!='authority-id-binder-order-v1-formal-result': errors.append('schema')
if R.get('result_id')!='authority-id-binder-order-v1-20260916-01': errors.append('result_id')
if R.get('formal_retries')!=0: errors.append('formal_retries')
if R.get('decision')!='RETAIN_BINDER_BEFORE_LEDGER_ORDER': errors.append('decision')
if R.get('hard_gate_pass') is not True: errors.append('hard_gate_pass')
rows=R.get('rows',[])
if [x.get('case') for x in rows]!=expected_cases: errors.append('case_order')
if len(rows)!=6 or not all(x.get('pass') is True for x in rows): errors.append('row_passes')
by={x['case']:x for x in rows if 'case' in x}
try:
 if by[expected_cases[0]]['detail']['token']!='caller-forged-id': errors.append('forged_token')
 if by[expected_cases[0]]['detail']['entry']!={'post_sequence':11,'status':'pending'}: errors.append('forged_persist')
 if by[expected_cases[1]]['detail']['error']!='caller authority_end_id mismatch': errors.append('prebind_forged_reject')
 if by[expected_cases[2]]['detail']['bound_id']!='runtime-intent-token' or by[expected_cases[2]]['detail']['token_id']!='runtime-intent-token': errors.append('runtime_bind')
 if by[expected_cases[3]]['detail']!={'id':'runtime-intent-token','seq':11}: errors.append('restart_runtime')
 if by[expected_cases[4]]['detail']['persisted']!={'post_sequence':11,'status':'pending'}: errors.append('post_bind_too_late')
 if by[expected_cases[5]]['detail']['state_exists'] is not False: errors.append('prebind_no_state')
except Exception as e: errors.append('detail_shape:'+type(e).__name__)
expected_deps={
 'authority_end_identity_binding_snapshot.py':'a305c1f70bc7bf849421ad41a7539966d539e1037f7db2fa5116b41af4f5f730',
 'validator_byte_pinned_ledger_v3.py':'a0744260a48b3575a451c63139fdb2fde898e0493317d1edd1d731ce3d227be5',
 'bridge_v2_semantic_snapshot.py':'f16ba93fabef5c395b349d91e2ea9ec4139f6f993a763269879fc8ccd6ee35f9',
 'durable_token_state_v2.py':'72a3481653cf9c41ec1a03f4c7a7bf1c482ff69468b5d92986bad8cf814950b4',
 'authority_ended_bridge_v1.py':'2c9684d8f731b36469df06532fc2ce566716c0380002d18da1f317814f7acb1e',
}
if R.get('dependency_sha256')!=expected_deps: errors.append('dependency_hashes')
runner_hash=hashlib.sha256((H/'formal_runner.py').read_bytes()).hexdigest()
if R.get('source_sha256',{}).get('formal_runner.py')!=runner_hash: errors.append('runner_hash')
binder_hash=hashlib.sha256((H/'authority_end_identity_binding_snapshot.py').read_bytes()).hexdigest()
if R.get('source_sha256',{}).get('authority_end_identity_binding_snapshot.py')!=binder_hash: errors.append('binder_hash')
out={'schema':'authority-id-binder-order-v1-audit','result_sha256':hashlib.sha256((H/'formal-result.json').read_bytes()).hexdigest(),'pass':not errors,'errors':errors}
print(json.dumps(out,indent=2,sort_keys=True))
raise SystemExit(0 if not errors else 2)
