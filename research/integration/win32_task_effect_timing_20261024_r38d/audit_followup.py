import json,hashlib
from pathlib import Path
P=Path(__file__).resolve().parent
R=P/'run'/'phase2_task'
C=json.loads((P/'conditions.json').read_text(encoding='utf-8'))
raw=json.loads((R/'result.json').read_text(encoding='utf-8'))
oracle=json.loads((R/'oracle-evidence.json').read_text(encoding='utf-8'))
steps=raw['steps']
get=lambda name: next(s for s in steps if s.get('name')==name)
verification=get('task_oracle')['parsed']
receipt=verification['task_effect']['receipt']
polls=get('read_only_results')['polls']
actions=[(p.get('parsed') or {}).get('action') for p in polls]
action=next(a for a in reversed(actions) if isinstance(a,dict) and a.get('status')=='completed')
execution=action['result']['execution']
save=oracle['save_event']; s0=save['save_write_started_monotonic_ns']; s1=save['save_write_completed_monotonic_ns']; observed=oracle['observed_monotonic_ns']
latency={'lower_bound_ns':observed-s1,'upper_bound_ns':observed-s0}
obs_capture=get('observation')['parsed']['image_reference']['recorded_capture']['capture_ended_ns']
dispatch_t=get('dispatch')['client_timing_ns']
verify_t=get('task_oracle')['client_timing_ns']
events=oracle['events']; token=C['phase2_task']['token']
char_text=''.join(chr(e['code']) for e in events if e.get('kind')=='char' and isinstance(e.get('code'),int))
checks=[
 {'name':'input_free_preflight_14_of_14','passed':json.loads((P/'preflight.json').read_text())['status']=='PASS' and json.loads((P/'preflight.json').read_text())['passed']==14},
 {'name':'runner_passed_and_cleanup','passed':raw['status']=='PASS_SCOPED' and raw['cleanup']['fixture_exit_code']==0 and raw['cleanup']['foreground_restored'] is True},
 {'name':'exact_effect_and_timed_save_match','passed':oracle['actual']==C['phase2_task']['expected_effect'] and oracle['outcome']=='success' and save['kind']=='save' and len([e for e in events if e.get('kind')=='save'])==1},
 {'name':'exact_action_identity_and_success','passed':receipt['call_id']==raw['call_id'] and receipt['operation_id']==raw['operation_id']==action['operation_id'] and receipt['target_generation']==raw['target_generation']==action['target_generation'] and receipt['oracle_id']==C['phase2_task']['oracle_id'] and verification['task_success'] is True},
 {'name':'single_observation_dispatch_oracle','passed':sum(s.get('name')=='observation' for s in steps)==1 and sum(s.get('name')=='dispatch' for s in steps)==1 and sum(s.get('name')=='task_oracle' for s in steps)==1},
 {'name':'fixture_input_sequence_exact','passed':len([e for e in events if e.get('kind')=='click'])==1 and char_text==token},
 {'name':'effect_time_interval_ordered','passed':type(s0) is int and type(s1) is int and s0<=s1<=observed},
 {'name':'neutral_terminal_release','passed':action.get('release_confirmed') is True and action.get('completion_custody',{}).get('completion_readback',{}).get('neutral') is True},
 {'name':'same_clock_timing_bounds','passed':latency['lower_bound_ns']>=0 and latency['upper_bound_ns']>=latency['lower_bound_ns'] and execution['started_ns']<=s0<=s1<=execution['ended_ns']},
]
timing={
 'clock':'same-host time.monotonic_ns',
 'observation_capture_ns':obs_capture,
 'dispatch_request_ns':dispatch_t['started'],
 'dispatch_pending_response_ns':dispatch_t['returned'],
 'execution_start_ns':execution['started_ns'],
 'save_write_interval_ns':[s0,s1],
 'execution_end_ns':execution['ended_ns'],
 'completion_readback_ns':action['completion_custody']['completion_readback']['observed_monotonic_ns'],
 'task_oracle_request_ns':verify_t['started'],
 'task_oracle_observed_ns':observed,
 'task_oracle_reply_ns':verify_t['returned'],
 'observation_to_save_interval_ns':[s0-obs_capture,s1-obs_capture],
 'dispatch_request_to_save_interval_ns':[s0-dispatch_t['started'],s1-dispatch_t['started']],
 'dispatch_response_to_save_interval_ns':[s0-dispatch_t['returned'],s1-dispatch_t['returned']],
 'save_to_execution_end_interval_ns':[execution['ended_ns']-s1,execution['ended_ns']-s0],
 'effect_to_oracle_observation_interval_ns':latency,
 'save_write_interval_width_ns':s1-s0,
 'reported_timer_resolution_seconds':__import__('time').get_clock_info('monotonic').resolution,
}
result={'schema':'win32-task-effect-timing-r38d-additive-audit-v1','attempt_id':C['attempt_id'],'status':'PASS_SCOPED' if all(x['passed'] for x in checks) else 'FAIL_OR_UNKNOWN','passed':sum(x['passed'] for x in checks),'total':len(checks),'checks':checks,'timing':timing,'source_commit':C['source_commit'],'raw_sha256':hashlib.sha256((R/'result.json').read_bytes()).hexdigest(),'conditions_sha256':hashlib.sha256((P/'conditions.json').read_bytes()).hexdigest(),'limitations':['one fixture sample','effect transition is bounded by file-write interval, not observed at a hardware timestamp','not matched efficiency or reliability','not MAP01 or real-app transfer','task oracle is fixture-specific']}
(P/'audit_followup.json').write_text(json.dumps(result,sort_keys=True,indent=2)+'\n',encoding='utf-8')
(P/'audit_followup.py').write_text(Path(__file__).read_text(encoding='utf-8'),encoding='utf-8')
print(json.dumps(result,indent=2))
