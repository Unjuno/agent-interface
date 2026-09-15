from __future__ import annotations
import hashlib,json
from pathlib import Path
H=Path(__file__).resolve().parent
R=json.loads((H/'formal-result.json').read_text())
expected=[
 'exact_binder_process_a_issues_runtime_id_only',
 'exact_binder_control_restart_rejects_forged_id',
 'drifted_binder_restart_admits_second_id_same_terminal',
 'validator_pin_and_nonbinder_sources_unchanged',
 'restored_exact_binder_cannot_remove_forged_pending_id',
]
errors=[]
if R.get('schema')!='authority-binder-byte-pin-gap-v1-formal-result': errors.append('schema')
if R.get('result_id')!='authority-binder-byte-pin-gap-v1-20260916-01': errors.append('result_id')
if R.get('base_commit')!='505d567ff269ecec3ac8ff81e35fc7816a787a6d': errors.append('base_commit')
if R.get('formal_retries')!=0: errors.append('formal_retries')
if R.get('decision')!='RETAIN_BINDER_VERSION_GAP': errors.append('decision')
if R.get('hard_gate_pass') is not True: errors.append('hard_gate')
rows=R.get('rows',[])
if [x.get('case') for x in rows]!=expected: errors.append('case_order')
if len(rows)!=5 or not all(x.get('pass') is True for x in rows): errors.append('row_passes')
by={x['case']:x for x in rows if 'case' in x}
try:
 a=by[expected[0]]['detail'];b=by[expected[1]]['detail'];c=by[expected[2]]['detail'];p=by[expected[3]]['detail'];d=by[expected[4]]['detail']
 if a['token_id']!='runtime-intent-token' or set(a['entries'])!={'runtime-intent-token'}: errors.append('initial_identity')
 if b['type']!='IdentityBindingError' or set(b['entries'])!={'runtime-intent-token'}: errors.append('control_rejection')
 if c['active_binder_sha256']!='e75b6851f37525e6230cde448392a248edf78d10c3e38dc2aeba4a518384ad26': errors.append('drift_hash')
 if c['worker']['token_id']!='caller-forged-id' or set(c['worker']['entries'])!={'runtime-intent-token','caller-forged-id'}: errors.append('drift_second_id')
 if p['control_pin']!=p['treatment_pin'] or p['control_pin']['validator_sha256']!='f16ba93fabef5c395b349d91e2ea9ec4139f6f993a763269879fc8ccd6ee35f9': errors.append('validator_pin_changed')
 if p['nonbinder_before']!=p['nonbinder_during']: errors.append('nonbinder_changed')
 if d['restored_binder_sha256']!='a305c1f70bc7bf849421ad41a7539966d539e1037f7db2fa5116b41af4f5f730': errors.append('restore_hash')
 if d['worker']['status']!='RECOVERED' or d['worker']['token_id']!='caller-forged-id': errors.append('forged_not_recoverable')
except Exception as e: errors.append('detail_shape:'+type(e).__name__)
for name in ['formal_runner.py','process_worker.py','diagnostic_drift_binder.py']:
 actual=hashlib.sha256((H/name).read_bytes()).hexdigest()
 if R.get('source_sha256',{}).get(name)!=actual: errors.append(name+':source_hash')
out={'schema':'authority-binder-byte-pin-gap-v1-audit','pass':not errors,'errors':errors,'result_sha256':hashlib.sha256((H/'formal-result.json').read_bytes()).hexdigest()}
print(json.dumps(out,indent=2,sort_keys=True))
raise SystemExit(0 if not errors else 2)
