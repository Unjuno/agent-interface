from __future__ import annotations
import hashlib,json
from pathlib import Path
H=Path(__file__).resolve().parent
R=json.loads((H/'formal-result.json').read_text())
expected=[
 'exact_init_pins_binder_and_issues_runtime_id',
 'post_constructor_source_replacement_does_not_change_loaded_binder',
 'fresh_restart_under_drift_rejects_pin_mismatch_without_mutation',
 'restore_exact_binder_reopens_and_recovers_pending',
 'binder_sidecar_crash_exact_retry_completes',
 'binder_sidecar_crash_then_drift_rejects_before_inner_state',
 'existing_state_missing_binder_pin_fails_closed',
 'delegated_after_replace_fsync_crash_recovers_runtime_pending',
]
errors=[]
if R.get('schema')!='authority-binder-byte-pin-v1-formal-result': errors.append('schema')
if R.get('result_id')!='authority-binder-byte-pin-v1-20260916-01': errors.append('result_id')
if R.get('base_commit')!='7bea48e69cfb62b2993e7d7ea18a1688d527b70b': errors.append('base_commit')
if R.get('formal_retries')!=0: errors.append('formal_retries')
if R.get('decision')!='RETAIN_BINDER_BYTE_PIN_V1': errors.append('decision')
if R.get('hard_gate_pass') is not True: errors.append('hard_gate')
rows=R.get('rows',[])
if [x.get('case') for x in rows]!=expected: errors.append('case_order')
if len(rows)!=8 or not all(x.get('pass') is True for x in rows): errors.append('row_passes')
by={x['case']:x for x in rows if 'case' in x}
try:
 g1=by[expected[0]]['detail'];g2=by[expected[1]]['detail'];g3=by[expected[2]]['detail'];g4=by[expected[3]]['detail']
 g5=by[expected[4]]['detail'];g6=by[expected[5]]['detail'];g7=by[expected[6]]['detail'];g8=by[expected[7]]['detail']
 exact='a305c1f70bc7bf849421ad41a7539966d539e1037f7db2fa5116b41af4f5f730'
 if g1['binder_pin']['binder_sha256']!=exact or g1['token_id']!='runtime-intent-token': errors.append('gate1_identity')
 if g2['type']!='IdentityBindingError' or g2['error']!='caller authority_end_id mismatch': errors.append('gate2_loaded_behavior')
 if g3['type']!='BinderPinError' or g3['error']!='binder pin mismatch': errors.append('gate3_restart_pin')
 if g4['status']!='RECOVERED' or g4['token_id']!='runtime-intent-token': errors.append('gate4_restore')
 if g5['crash']['state_exists'] is not False or g5['crash']['validator_pin_exists'] is not False or g5['retry']['status']!='ISSUED': errors.append('gate5_crash_retry')
 if g6['drift_retry']['type']!='BinderPinError' or g6['drift_retry']['state_exists'] is not False or g6['drift_retry']['validator_pin_exists'] is not False: errors.append('gate6_drift_after_crash')
 if g7['missing_pin_restart']['type']!='BinderPinError' or g7['missing_pin_restart']['error']!='existing token state missing binder pin': errors.append('gate7_missing_pin')
 if g8['crash']['type']!='InjectedCrash' or g8['restart']['status']!='RECOVERED' or g8['restart']['token_id']!='runtime-intent-token': errors.append('gate8_durable_crash')
except Exception as e: errors.append('detail_shape:'+type(e).__name__)
expected_sources={
 'binder_byte_pinned_bound_issue_v1.py':'c725ca222920acf7dde9e5e0950a7178da92dbac41b49f65452acd0939241060',
 'process_worker.py':'0cdc84b6089779096b51d0e983be9cf724bb9640d13b7b48aa7bce39b3cb8fee',
 'formal_runner.py':'54596e8a8412321f473696626bfd114592126cee2ef412e1c41642772f663243',
}
if R.get('source_sha256')!=expected_sources: errors.append('source_sha_map')
for name,expected_sha in expected_sources.items():
 if hashlib.sha256((H/name).read_bytes()).hexdigest()!=expected_sha: errors.append(name+':source_hash')
out={'schema':'authority-binder-byte-pin-v1-audit','pass':not errors,'errors':errors,'result_sha256':hashlib.sha256((H/'formal-result.json').read_bytes()).hexdigest()}
print(json.dumps(out,indent=2,sort_keys=True))
raise SystemExit(0 if not errors else 2)
