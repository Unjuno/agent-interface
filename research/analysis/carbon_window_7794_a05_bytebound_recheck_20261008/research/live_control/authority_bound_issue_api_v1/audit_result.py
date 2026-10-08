from __future__ import annotations
import hashlib,json
from pathlib import Path
H=Path(__file__).resolve().parent
R=json.loads((H/'formal-result.json').read_text())
expected=[
 'valid_missing_id_binds_without_mutating_caller',
 'forged_id_rejects_without_entry_mutation',
 'release_token_mismatch_rejects_without_entry_mutation',
 'postbind_validator_failure_rejects_without_entry_mutation',
 'restart_recovers_same_pending_runtime_token',
 'duplicate_rejects_preserving_single_pending_entry',
 'consume_restart_remains_consumed',
 'after_temp_fsync_crash_leaves_no_issued_entry',
 'after_replace_fsync_crash_recovers_durable_runtime_id',
]
errors=[]
if R.get('schema')!='authority-bound-issue-api-v1-formal-result': errors.append('schema')
if R.get('result_id')!='authority-bound-issue-api-v1-20260916-01': errors.append('result_id')
if R.get('base_commit')!='71ab480b5a9b74e54ebae06a70913bb94ea432ef': errors.append('base_commit')
if R.get('formal_retries')!=0: errors.append('formal_retries')
if R.get('decision')!='RETAIN_BOUND_ISSUE_API_V1': errors.append('decision')
if R.get('hard_gate_pass') is not True: errors.append('hard_gate')
rows=R.get('rows',[])
if [r.get('case') for r in rows]!=expected: errors.append('case_order')
if len(rows)!=9 or not all(r.get('pass') is True for r in rows): errors.append('row_passes')
by={r['case']:r for r in rows if 'case' in r}
try:
 if by[expected[0]]['detail']['caller_has_id'] is not False: errors.append('caller_mutated')
 if by[expected[0]]['detail']['token_id']!='runtime-intent-token': errors.append('runtime_id')
 for c in expected[1:4]:
  if by[c]['detail']['entries']!={}: errors.append(c+':entry_mutation')
 if by[expected[4]]['detail']['entry']!={'post_sequence':11,'status':'pending'}: errors.append('restart_pending')
 if by[expected[5]]['detail']['entries']!={'runtime-intent-token':{'post_sequence':11,'status':'pending'}}: errors.append('duplicate_state')
 if by[expected[6]]['detail']['entries']!={'runtime-intent-token':{'post_sequence':11,'status':'consumed'}}: errors.append('consumed_state')
 if by[expected[7]]['detail']['entries_after_restart']!={}: errors.append('temp_crash_state')
 if by[expected[8]]['detail']['entries_after_restart']!={'runtime-intent-token':{'post_sequence':11,'status':'pending'}}: errors.append('replace_crash_state')
except Exception as e: errors.append('detail_shape:'+type(e).__name__)
expected_hashes={
 'authority_end_identity_binding_v1.py':'a305c1f70bc7bf849421ad41a7539966d539e1037f7db2fa5116b41af4f5f730',
 'authority_ended_bridge_v1.py':'2c9684d8f731b36469df06532fc2ce566716c0380002d18da1f317814f7acb1e',
 'bound_authority_issue_v1.py':'2f812a678b72f09985e24d003b2e7030508a49e4475e9d3aef5533b1a07f2ba2',
 'bridge_v2_semantic_snapshot.py':'f16ba93fabef5c395b349d91e2ea9ec4139f6f993a763269879fc8ccd6ee35f9',
 'durable_token_state_v2.py':'72a3481653cf9c41ec1a03f4c7a7bf1c482ff69468b5d92986bad8cf814950b4',
 'validator_byte_pinned_ledger_v3.py':'a0744260a48b3575a451c63139fdb2fde898e0493317d1edd1d731ce3d227be5',
}
if R.get('dependency_sha256')!=expected_hashes: errors.append('dependency_hashes')
for name in ['bound_authority_issue_v1.py','formal_runner.py']:
 actual=hashlib.sha256((H/name).read_bytes()).hexdigest()
 if R.get('source_sha256',{}).get(name)!=actual: errors.append(name+':source_hash')
out={'schema':'authority-bound-issue-api-v1-audit','pass':not errors,'errors':errors,'result_sha256':hashlib.sha256((H/'formal-result.json').read_bytes()).hexdigest()}
print(json.dumps(out,indent=2,sort_keys=True))
raise SystemExit(0 if not errors else 2)
