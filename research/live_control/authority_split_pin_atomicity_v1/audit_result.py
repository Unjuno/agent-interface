from __future__ import annotations
import hashlib,json
from pathlib import Path
H=Path(__file__).resolve().parent
R=json.loads((H/'formal-result.json').read_text())
expected=[
 'baseline_exact_init_issue',
 'binder_sidecar_crash_leaves_no_validator_or_state',
 'pre_state_unpinned_validator_can_become_initial_choice',
 'validator_sidecar_crash_leaves_both_pins_no_state',
 'both_pins_binder_drift_rejects_without_mutation',
 'both_pins_validator_drift_rejects_without_mutation',
 'complete_state_binder_drift_rejects_without_mutation',
 'complete_state_validator_drift_rejects_without_mutation',
 'existing_state_missing_binder_pin_rejects_without_mutation',
 'existing_state_missing_validator_pin_rejects_without_mutation',
]
errors=[]
if R.get('schema')!='authority-split-pin-atomicity-v1-formal-result':errors.append('schema')
if R.get('result_id')!='authority-split-pin-atomicity-v1-20260916-01':errors.append('result_id')
if R.get('base_commit')!='71dea2279dd4b8fb5a1d6f64e7c773a756feeb5b':errors.append('base_commit')
if R.get('formal_retries')!=0:errors.append('formal_retries')
if R.get('decision')!='HOLD_COMPOSITE_MANIFEST_NO_STATE_REINTERPRETATION':errors.append('decision')
if R.get('hard_gate_pass') is not True:errors.append('hard_gate')
rows=R.get('rows',[])
if [x.get('case') for x in rows]!=expected:errors.append('case_order')
if len(rows)!=10 or not all(x.get('pass') is True for x in rows):errors.append('row_passes')
by={x['case']:x for x in rows if 'case'in x}
try:
 if by[expected[0]]['detail']['token_id']!='runtime-intent-token':errors.append('baseline_identity')
 g2=by[expected[1]]['detail']
 if g2['state_exists'] is not False or g2['validator_pin_exists'] is not False or g2['binder_pin_exists'] is not True:errors.append('binder_only_window')
 g3=by[expected[2]]['detail']
 if g3['classification']!='pre_state_initialization_choice' or g3['worker']['validator_sha256']!='1f40ea48def2e99823c8e254dc1f95927d9c5600bfb3fc420185e76ca5f71a81':errors.append('pre_state_classification')
 g4=by[expected[3]]['detail']
 if g4['state_exists'] is not False or g4['binder_pin_exists'] is not True or g4['validator_pin_exists'] is not True:errors.append('both_pins_window')
 if by[expected[4]]['detail']['type']!='BinderPinError':errors.append('both_pins_binder_drift')
 if by[expected[5]]['detail']['type']!='ValidatorPinError':errors.append('both_pins_validator_drift')
 if by[expected[6]]['detail']['restart']['type']!='BinderPinError':errors.append('state_binder_drift')
 if by[expected[7]]['detail']['type']!='ValidatorPinError':errors.append('state_validator_drift')
 if by[expected[8]]['detail']['restart']['error']!='existing token state missing binder pin':errors.append('missing_binder_pin')
 if by[expected[9]]['detail']['restart']['error']!='existing token state missing validator pin':errors.append('missing_validator_pin')
except Exception as e:errors.append('detail_shape:'+type(e).__name__)
expected_sources={
 'diagnostic_validator_byte_drift.py':'1f40ea48def2e99823c8e254dc1f95927d9c5600bfb3fc420185e76ca5f71a81',
 'formal_runner.py':'d942dc75c19bb993b35ff919a944db84b3c0461ea53e96c970b64f218ff5defa',
 'process_worker.py':'1ad0ca3937e361f1e4e2fd98921649a50b03361157709228fd650f9faf81834b',
}
if R.get('source_sha256')!=expected_sources:errors.append('source_map')
for n,h in expected_sources.items():
 if hashlib.sha256((H/n).read_bytes()).hexdigest()!=h:errors.append(n+':source_hash')
out={'schema':'authority-split-pin-atomicity-v1-audit','pass':not errors,'errors':errors,'result_sha256':hashlib.sha256((H/'formal-result.json').read_bytes()).hexdigest()}
print(json.dumps(out,indent=2,sort_keys=True))
raise SystemExit(0 if not errors else 2)
