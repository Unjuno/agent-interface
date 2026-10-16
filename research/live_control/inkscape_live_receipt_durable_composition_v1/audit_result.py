from __future__ import annotations
import hashlib,json
from pathlib import Path
H=Path(__file__).resolve().parent
R=json.loads((H/'formal-result.json').read_text())
EXPECTED_RESULT='48f884b7dce2bca727706faeb5f69ced60eb208497de3ff5a7cde81f8ceb228c'
EXPECTED_RUNNER='6e6ae05eaacb8e39b1dacd072f33186d225255f0ac776988ac1ac7a0dc7f830d'
EXPECTED_INPUT='402f6320f7a87acd0540b9aab1cd2eee610fab73c9937c72a682b77f11e0e9f3'
RID='901e6ed15b87454fdbef7909c1e0f026'
expected_cases=[
'exact_live_input_and_dependency_identities',
'issue_exact_runtime_identity_without_caller_mutation',
'sidecars_pin_exact_live_policy_bytes',
'fresh_reopen_recovers_exact_pending_live_token',
'duplicate_live_receipt_rejects_without_mutation',
'forged_live_identity_rejects_before_mutation',
'consume_restart_preserves_consumed_live_identity',
]
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
errors=[]
if sha(H/'formal-result.json')!=EXPECTED_RESULT: errors.append('formal_result_hash')
if sha(H/'formal_runner.py')!=EXPECTED_RUNNER: errors.append('formal_runner_hash')
if R.get('schema')!='inkscape-live-receipt-durable-composition-v1-formal-result': errors.append('schema')
if R.get('result_id')!='inkscape-live-receipt-durable-composition-v1-20260916-01': errors.append('result_id')
if R.get('base_commit')!='0792fe8bbacb53073b7f818244b0bf52f9c20fe6': errors.append('base_commit')
if R.get('input_result_sha256')!=EXPECTED_INPUT: errors.append('input_result_hash')
if R.get('formal_retries')!=0 or R.get('hard_gate_pass') is not True: errors.append('formal_gate')
if R.get('decision')!='RETAIN_LIVE_RECEIPT_DURABLE_IDENTITY_COMPOSITION': errors.append('decision')
rows=R.get('rows',[])
if [x.get('case') for x in rows]!=expected_cases: errors.append('case_order')
if len(rows)!=7 or not all(x.get('pass') is True for x in rows): errors.append('row_passes')
by={x['case']:x for x in rows if 'case' in x}
try:
    g1=by[expected_cases[0]]['detail'];g2=by[expected_cases[1]]['detail'];g3=by[expected_cases[2]]['detail'];g4=by[expected_cases[3]]['detail'];g5=by[expected_cases[4]]['detail'];g6=by[expected_cases[5]]['detail'];g7=by[expected_cases[6]]['detail']
    if g1['authority_end_id']!=RID or g1['sequence']!=3: errors.append('live_input_identity')
    if g2['token_id']!=RID or g2['post_sequence']!=3 or not g2['receipt_unchanged'] or not g2['terminal_unchanged']: errors.append('issue_identity')
    if g3['binder_pin']['binder_sha256']!='a305c1f70bc7bf849421ad41a7539966d539e1037f7db2fa5116b41af4f5f730': errors.append('binder_pin')
    if g3['validator_pin']['validator_sha256']!='37e544086fe70087c0a2e6c03ce8c42c1c5dd71989f7fe541eb9055b3551eb52': errors.append('validator_pin')
    if g4['token_id']!=RID or g4['post_sequence']!=3 or g4['entries'][RID]['status']!='pending': errors.append('restart_pending')
    if g5['rejection']['type']!='DuplicateReceipt' or g5['entries'][RID]['status']!='pending': errors.append('duplicate')
    if g6['rejection']['type']!='IdentityBindingError' or g6['rejection']['error']!='caller authority_end_id mismatch' or g6['entries'][RID]['status']!='pending': errors.append('forged')
    if g7['rejection']['type']!='TokenConsumed' or g7['entries'][RID]!={'post_sequence':3,'status':'consumed'}: errors.append('consumed')
except Exception as e: errors.append('detail_shape:'+type(e).__name__)
out={'schema':'inkscape-live-receipt-durable-composition-v1-audit','pass':not errors,'errors':errors,'formal_result_sha256':sha(H/'formal-result.json'),'formal_runner_sha256':sha(H/'formal_runner.py')}
print(json.dumps(out,indent=2,sort_keys=True))
raise SystemExit(0 if not errors else 2)
