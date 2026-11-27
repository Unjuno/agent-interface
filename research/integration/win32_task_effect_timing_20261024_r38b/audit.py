import json
from pathlib import Path
P=Path(__file__).resolve().parent
R=P/'run'/'phase2_task'
C=json.loads((P/'conditions.json').read_text(encoding='utf-8'))
raw=json.loads((R/'result.json').read_text(encoding='utf-8'))
oracle=json.loads((R/'oracle-evidence.json').read_text(encoding='utf-8'))
receipt=raw['steps'][-2]['parsed']['task_effect']['receipt']
save=oracle['save_event']
start=save['save_write_started_monotonic_ns']; end=save['save_write_completed_monotonic_ns']; observed=oracle['observed_monotonic_ns']
latency={'lower_bound_ns':observed-end,'upper_bound_ns':observed-start}
checks=[
 {'name':'preflight_pass','passed':json.loads((P/'preflight.json').read_text())['status']=='PASS'},
 {'name':'runner_passed','passed':raw['status']=='PASS_SCOPED'},
 {'name':'one_completed_call','passed':bool(raw.get('call_id') and raw.get('operation_id'))},
 {'name':'exact_generation_bound','passed':receipt['call_id']==raw['call_id'] and receipt['operation_id']==raw['operation_id'] and receipt['target_generation']==raw['target_generation']},
 {'name':'oracle_verified_success','passed':receipt['outcome']=='success' and raw['steps'][-2]['parsed']['task_success'] is True},
 {'name':'save_event_interval_ordered','passed':type(start) is int and type(end) is int and start<=end<=observed},
 {'name':'timed_save_effect_matches','passed':save['actual']==C['phase2_task']['expected_effect'] and save['save_event']['kind']=='save' and len([e for e in save['events'] if e.get('kind')=='save'])==1},
 {'name':'effect_to_oracle_interval_nonnegative','passed':latency['lower_bound_ns']>=0 and latency['upper_bound_ns']>=latency['lower_bound_ns']},
 {'name':'release_and_readback_confirmed','passed':raw['steps'][-3]['parsed']['action']['release_confirmed'] is True and raw['steps'][-3]['parsed']['action']['completion_custody']['completion_readback']['neutral'] is True},
 {'name':'owned_cleanup','passed':raw['cleanup']['fixture_exit_code']==0 and raw['cleanup']['foreground_restored'] is True},
]
result={'schema':'win32-task-effect-timing-r38-audit-v1','attempt_id':C['attempt_id'],'status':'PASS_SCOPED' if all(x['passed'] for x in checks) else 'FAIL_OR_UNKNOWN','passed':sum(x['passed'] for x in checks),'total':len(checks),'checks':checks,'effect_to_oracle_latency_ns_interval':latency,'effect_to_oracle_latency_ms_interval':[latency['lower_bound_ns']/1e6,latency['upper_bound_ns']/1e6],'nonclaims':C['nonclaims']}
(P/'audit.json').write_text(json.dumps(result,sort_keys=True,indent=2)+'\n',encoding='utf-8')
print(json.dumps(result,indent=2))
