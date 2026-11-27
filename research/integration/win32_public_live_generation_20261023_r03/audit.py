"""Independent audit for the live public-caller generation discriminator."""
import json
from pathlib import Path
import re
P=Path(__file__).resolve().parent
C=json.loads((P/'conditions.json').read_text(encoding='utf-8'))
R=json.loads((P/'raw.json').read_text(encoding='utf-8'))
checks=[]
def check(name,ok,evidence=None): checks.append({'name':name,'passed':bool(ok),'evidence':evidence})
def data(name): return (R.get(name) or {}).get('data') or {}
fixtures=R.get('fixtures',[])
bind=data('bind'); admitted=data('admit'); started=data('start'); retained=data('interface_results')
action=retained.get('action') or {}; action_result=action.get('result') or {}
owner=R.get('owner_result') or {}
check('attempt_and_source_pinned',R.get('attempt_id')==C['attempt_id'] and R.get('source_commit')==C['source_commit'],{'attempt_id':R.get('attempt_id'),'source_commit':R.get('source_commit')})
check('windows_only_no_shared_resources','win' in R.get('platform','').lower() and R.get('resource_commands')==[] and R.get('scope')==C['scope'],{'platform':R.get('platform'),'resource_commands':R.get('resource_commands'),'scope':R.get('scope')})
check('two_owned_fixture_generations',len(fixtures)==2 and all(type(x.get('pid')) is int and type(x.get('hwnd')) is int and x.get('exit_code')==0 and x.get('window_exists_after_exit') is False for x in fixtures) and fixtures[0]['pid']!=fixtures[1]['pid'],fixtures)
check('actual_generation_changed',bool(re.fullmatch(r'[0-9a-f]{64}',R.get('generation_a',''))) and bool(re.fullmatch(r'[0-9a-f]{64}',R.get('generation_b',''))) and R.get('generation_a')!=R.get('generation_b'),{'a':R.get('generation_a'),'b':R.get('generation_b')})
check('public_bind_and_admit_pin_generation_a',not (R.get('bind') or {}).get('is_error') and bind.get('target_generation')==R.get('generation_a') and not (R.get('admit') or {}).get('is_error') and (admitted.get('action') or {}).get('target_generation')==R.get('generation_a'),{'bind':bind,'admit':admitted})
check('public_start_fails_closed_before_producer',started.get('status')=='unknown' and action.get('status')=='unknown' and action_result.get('error')=='target_generation_changed_before_start' and R.get('producer_factory_calls')==[] and started.get('input_dispatched') is False and started.get('task_success') is None and started.get('replay_allowed') is False,{'start':started,'action':action,'producer_factory_calls':R.get('producer_factory_calls')})
check('interface_results_and_owner_retain_unknown',(retained.get('action') or {}).get('status')=='unknown' and owner.get('phase')=='unknown' and owner.get('producer_gate_state')=='closed' and owner.get('producer_identity') is None and owner.get('release_confirmed') is False and owner.get('task_success') is None and owner.get('replay_allowed') is False,{'retained':retained,'owner':owner})
check('cleanup_and_no_input',R.get('cleanup_errors')==[] and all(x.get('close_posted') is True and x.get('window_exists_after_exit') is False for x in fixtures) and R.get('producer_factory_calls')==[],{'cleanup_errors':R.get('cleanup_errors'),'fixtures':fixtures})
A={'schema':'win32-public-live-generation-audit-v1','attempt_id':C['attempt_id'],'source_commit':C['source_commit'],'status':'PASS' if all(x['passed'] for x in checks) else 'FAIL_OR_UNKNOWN','passed':sum(x['passed'] for x in checks),'total':len(checks),'checks':checks}
(P/'audit.json').write_text(json.dumps(A,indent=2,sort_keys=True)+'\n',encoding='utf-8')
print(json.dumps({k:A[k] for k in ('attempt_id','status','passed','total')},sort_keys=True))
raise SystemExit(0 if A['status']=='PASS' else 1)
