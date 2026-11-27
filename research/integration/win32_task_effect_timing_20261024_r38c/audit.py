import json
from pathlib import Path
P=Path(__file__).resolve().parent
R=P/'run'/'phase2_task'
C=json.loads((P/'conditions.json').read_text(encoding='utf-8'))
raw=json.loads((R/'result.json').read_text(encoding='utf-8'))
oracle=json.loads((R/'oracle-evidence.json').read_text(encoding='utf-8'))
oracle_steps=[s for s in raw['steps'] if s.get('name')=='task_oracle']
assert len(oracle_steps)==1
oracle_reply=oracle_steps[0]['parsed']
receipt=oracle_reply['task_effect']['receipt']
action_candidates=[]
for step in raw['steps']:
    if step.get('name')=='dispatch':
        parsed=step.get('parsed') or {}
        for candidate in (parsed.get('action'), parsed.get('result')):
            if isinstance(candidate,dict) and candidate.get('status')=='completed': action_candidates.append(candidate)
    if step.get('name')=='read_only_results':
        for poll in step.get('polls',[]):
            parsed=poll.get('parsed') or {}
            candidate=parsed.get('action')
            if isinstance(candidate,dict) and candidate.get('status')=='completed': action_candidates.append(candidate)
assert action_candidates, 'no completed action receipt retained'
action=action_candidates[-1]
save=oracle['save_event']
start=save['save_write_started_monotonic_ns']; end=save['save_write_completed_monotonic_ns']; observed=oracle['observed_monotonic_ns']
latency={'lower_bound_ns':observed-end,'upper_bound_ns':observed-start}
checks=[
 {'name':'preflight_pass','passed':json.loads((P/'preflight.json').read_text())['status']=='PASS'},
 {'name':'runner_passed','passed':raw['status']=='PASS_SCOPED'},
 {'name':'one_completed_call','passed':bool(raw.get('call_id') and raw.get('operation_id'))},
 {'name':'one_dispatch_one_oracle','passed':sum(s.get('name')=='dispatch' for s in raw['steps'])==1 and len(oracle_steps)==1},
 {'name':'action_receipt_matches_run','passed':action.get('call_id')==raw.get('call_id') and action.get('operation_id')==raw.get('operation_id') and action.get('target_generation')==raw.get('target_generation')},
 {'name':'exact_generation_bound','passed':receipt['call_id']==raw['call_id'] and receipt['operation_id']==raw['operation_id'] and receipt['target_generation']==raw['target_generation']},
 {'name':'oracle_verified_success','passed':receipt['outcome']=='success' and oracle_reply['task_success'] is True},
 {'name':'save_event_interval_ordered','passed':type(start) is int and type(end) is int and start<=end<=observed},
 {'name':'timed_save_effect_matches','passed':save['actual']==C['phase2_task']['expected_effect'] and save['save_event']['kind']=='save' and len([e for e in save['events'] if e.get('kind')=='save'])==1},
 {'name':'effect_to_oracle_interval_nonnegative','passed':latency['lower_bound_ns']>=0 and latency['upper_bound_ns']>=latency['lower_bound_ns']},
 {'name':'release_and_readback_confirmed','passed':action.get('release_confirmed') is True and action.get('completion_custody',{}).get('completion_readback',{}).get('neutral') is True},
 {'name':'owned_cleanup','passed':raw['cleanup']['fixture_exit_code']==0 and raw['cleanup']['foreground_restored'] is True},
]
result={'schema':'win32-task-effect-timing-r38-audit-v1','attempt_id':C['attempt_id'],'status':'PASS_SCOPED' if all(x['passed'] for x in checks) else 'FAIL_OR_UNKNOWN','passed':sum(x['passed'] for x in checks),'total':len(checks),'checks':checks,'effect_to_oracle_latency_ns_interval':latency,'effect_to_oracle_latency_ms_interval':[latency['lower_bound_ns']/1e6,latency['upper_bound_ns']/1e6],'nonclaims':C['nonclaims']}
(P/'audit.json').write_text(json.dumps(result,sort_keys=True,indent=2)+'\n',encoding='utf-8')
print(json.dumps(result,indent=2))
