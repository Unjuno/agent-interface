from __future__ import annotations
import hashlib,json
from pathlib import Path
P=Path(__file__).resolve().parent; C=json.loads((P/'conditions.json').read_text(encoding='utf-8'))
t=json.loads((P/'task_raw.json').read_text(encoding='utf-8'))
pre=json.loads((P/'preflight.json').read_text(encoding='utf-8'))
ph=json.loads((P/'phases.json').read_text(encoding='utf-8'))
run=P/'run'/'phase2_task'
oracle=json.loads((run/'oracle-evidence.json').read_text(encoding='utf-8')) if (run/'oracle-evidence.json').exists() else {}
effect=json.loads((run/'effect.json').read_text(encoding='utf-8')) if (run/'effect.json').exists() else None
steps=t.get('steps') or []
def named(name): return [x for x in steps if x.get('name')==name]
dispatch=named('dispatch')
report=(dispatch[-1].get('parsed') or {}) if dispatch else {}
action=report.get('action') if isinstance(report.get('action'),dict) else report.get('result') if isinstance(report.get('result'),dict) else {}
if action.get('status')!='completed':
    for group in named('read_only_results'):
        for row in group.get('polls',[]):
            a=(row.get('parsed') or {}).get('action')
            if isinstance(a,dict) and a.get('status')=='completed': action=a
receipt=((oracle.get('task_effect') or {}).get('receipt') or {})
expected=C['task']['expected_effect']; fg=t.get('foreground_activation') or {}
releases=((action.get('result') or {}).get('execution') or {}).get('releases') or []
neutral=bool(releases) and all(r.get('verified') is True and r.get('keys_down')==[] and r.get('buttons_down')==[] and r.get('keys_unknown')==[] and r.get('buttons_unknown')==[] for r in releases)
witness=any(bool(r.get('state_query_witnesses')) for r in releases)
close=named('server_close'); closebody=(close[-1].get('parsed') or {}) if close else {}
old=json.loads((P.parent/'win32_supervised_standard_caller_20261024_r42'/'raw.json').read_text(encoding='utf-8'))
oldgen=((old.get('public_observation') or {}).get('raw_report') or {}).get('target_generation')
checks=[]
def check(n,ok,e): checks.append({'name':n,'passed':bool(ok),'evidence':e})
check('input_free_preflight_and_custody',pre.get('status')=='PASS' and pre.get('native_input_sent') is False,pre.get('checks'))
check('phase2_cua_activation_and_foreground_match',fg.get('activated') is True and fg.get('screenshot_inspected') is True and fg.get('fixture_hwnd')==t.get('fixture_hwnd') and fg.get('observed_foreground_hwnd')==t.get('fixture_hwnd') and bool(fg.get('cua_window_id')) and bool(fg.get('activation_result')),fg)
check('fresh_generation_differs_from_release_predecessor',isinstance(t.get('target_generation'),str) and len(t['target_generation'])==64 and t['target_generation']!=oldgen,{'prior_generation':oldgen,'new_generation':t.get('target_generation')})
check('exactly_one_dispatch_and_oracle_attempt',len(dispatch)==1 and len(named('task_oracle'))==1 and t.get('status')=='PASS_SCOPED',{'dispatch_count':len(dispatch),'oracle_count':len(named('task_oracle')),'task_status':t.get('status')})
verified=(named('task_oracle')[-1].get('parsed') or {}) if named('task_oracle') else {}
check('independent_oracle_binds_call_operation_generation',verified.get('status')=='verified' and verified.get('task_success') is True and receipt.get('call_id')==t.get('call_id') and receipt.get('operation_id')==t.get('operation_id') and receipt.get('target_generation')==t.get('target_generation') and receipt.get('oracle_id')==C['task']['oracle_id'],{'verification':verified,'receipt':receipt})
check('effect_exactly_matches_frozen_task',effect==expected and oracle.get('outcome')=='success' and oracle.get('actual')==expected,{'expected':expected,'effect':effect,'oracle':oracle})
check('action_completed_with_verified_neutral_release',action.get('status')=='completed' and action.get('operation_id')==t.get('operation_id') and action.get('target_generation')==t.get('target_generation') and action.get('release_confirmed') is True and (action.get('result') or {}).get('recovery_required') is False and neutral,{'action':action,'release_receipts':releases})
check('independent_state_witness_present',witness,{'release_receipt_count':len(releases),'witness_present':witness})
check('bounded_process_cleanup_and_foreground_restore',ph.get('task_exit_code')==0 and (t.get('cleanup') or {}).get('fixture_exit_code')==0 and (t.get('cleanup') or {}).get('foreground_restored') is True and closebody.get('status')=='closed',{'exit_code':ph.get('task_exit_code'),'cleanup':t.get('cleanup'),'server_close':closebody})
passed=sum(x['passed'] for x in checks)
result={'schema':'win32-r43-task-audit-v1','attempt_id':C['attempt_id'],'source_commit':C['source_commit'],'status':'PASS_SCOPED' if passed==len(checks) else 'FAIL_OR_UNKNOWN','passed':passed,'total':len(checks),'task_success':verified.get('task_success'),'checks':checks,'nonclaims':C['nonclaims'],'conditions_sha256':hashlib.sha256((P/'conditions.json').read_bytes()).hexdigest()}
(P/'audit_r43.json').write_text(json.dumps(result,indent=2,sort_keys=True,ensure_ascii=False)+'\n',encoding='utf-8')
print(json.dumps({'status':result['status'],'passed':passed,'total':len(checks),'task_success':result['task_success']},sort_keys=True))
