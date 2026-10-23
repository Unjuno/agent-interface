"""Frozen read-only audit for supervised standard-caller cancellation R08."""
from __future__ import annotations
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
CONDITIONS = json.loads((HERE / 'conditions.json').read_text(encoding='utf-8'))
RAW = json.loads((HERE / 'raw.json').read_text(encoding='utf-8'))
trial = CONDITIONS['trial']
checks = []
def check(name, passed, evidence=None):
    checks.append({'name':name,'passed':bool(passed),'evidence':evidence})

def elapsed(a,b):
    return (b-a)/1_000_000 if type(a) is int and type(b) is int else None

fixture = RAW.get('fixture', {})
identity = fixture.get('target_identity', {})
owned_generation = identity.get('generation')
observation = RAW.get('public_observation', {}).get('raw_report', {})
validation = RAW.get('public_validation', {}).get('response', {})
program = RAW.get('program', {})
hook = RAW.get('hook_trace_after_recovery') or RAW.get('hook_trace_after_dispatch') or {}
public_cancel = RAW.get('public_cancel', {})
cancel = public_cancel.get('response', {})
exit_witness = RAW.get('producer_exit_witness', {})
readbacks = RAW.get('result_readbacks', [])
terminal = readbacks[-1].get('response', {}) if readbacks else {}
row = terminal.get('result') if isinstance(terminal.get('result'), dict) else terminal
cancellation = (row.get('cancellation') or {}) if isinstance(row, dict) else {}
owner_result = cancellation.get('result', {}) if isinstance(cancellation, dict) else {}
action = row.get('action', {}) if isinstance(row, dict) else {}
effect = RAW.get('effect_readback')
events = fixture.get('events', [])
text = trial['text_effect']
expected_prefix = ([{'kind':'ready','hwnd':fixture.get('hwnd')},{'kind':'click'}]
    + [{'kind':'char','code':ord(ch)} for ch in text]
    + [{'kind':'save',**trial['expected_effect']}])

check('attempt_and_source_identity',
    RAW.get('attempt_id') == CONDITIONS.get('attempt_id')
    and RAW.get('source_commit') == CONDITIONS.get('source_commit')
    and RAW.get('source_tracked_tree_clean') is True,
    {'attempt_id':RAW.get('attempt_id'),'source_commit':RAW.get('source_commit'),
     'tracked_tree_clean':RAW.get('source_tracked_tree_clean')})
check('one_owned_fixture_generation',
    identity.get('owner',{}).get('pid') == fixture.get('pid')
    and isinstance(owned_generation,str) and len(owned_generation)==64,
    {'fixture_pid':fixture.get('pid'),'owner':identity.get('owner'),
     'generation':owned_generation})
check('public_observation_generation_matches_fixture',
    observation.get('target_generation') == owned_generation,
    {'observed':observation.get('target_generation'),'owned':owned_generation})
check('static_validation_passed',
    validation.get('static_valid') is True and validation.get('status') == 'valid',
    validation)
check('one_exact_dispatch_program',
    RAW.get('dispatch_attempts') == 1
    and program.get('program_id') == trial.get('program_id')
    and program.get('ops') == trial.get('operations')
    and program.get('source',{}).get('target_generations',{}).get('fixture') == owned_generation,
    {'attempts':RAW.get('dispatch_attempts'),'program_id':program.get('program_id'),
     'operations':program.get('ops')})
check('hook_observed_injected_q_down_before_cancel',
    hook.get('vk') == ord('Q') and hook.get('flags',0) & 0x10
    and type(hook.get('callback_entry_ns')) is int
    and type(public_cancel.get('started_monotonic_ns')) is int
    and hook['callback_entry_ns'] <= public_cancel['started_monotonic_ns'],
    {'hook':hook,'cancel_started_ns':public_cancel.get('started_monotonic_ns')})
pre_cancel = RAW.get('pre_cancel_status_readback', {})
check('dispatch_still_running_at_hook_barrier',
    pre_cancel.get('action',{}).get('status') == 'running'
    and pre_cancel.get('call_id') == RAW.get('blocked_call_id'),
    {'call_id':pre_cancel.get('call_id'),
     'action_status':pre_cancel.get('action',{}).get('status')})
check('call_id_custody_and_single_cancel',
    RAW.get('blocked_call_id') == cancel.get('call_id')
    and isinstance(cancel.get('cancellation'),dict)
    and cancel.get('status') in ('pending','recovered')
    and public_cancel.get('is_error') is False,
    {'blocked_call_id':RAW.get('blocked_call_id'),'cancel':cancel})
check('bounded_public_cancel_response',
    isinstance(public_cancel.get('elapsed_ms'),(int,float))
    and public_cancel['elapsed_ms'] <= 1000,
    {'elapsed_ms':public_cancel.get('elapsed_ms'),'limit_ms':1000})
check('exact_producer_process_retired',
    exit_witness.get('status') == 'exited'
    and exit_witness.get('pid') == RAW.get('producer_identity_from_cancel',{}).get('pid')
    and exit_witness.get('creation_time_100ns') == RAW.get('producer_identity_from_cancel',{}).get('creation_time_100ns'),
    {'identity':RAW.get('producer_identity_from_cancel'),'witness':exit_witness})
q_up_ns = hook.get('q_up_callback_ns')
producer_exit_ns = exit_witness.get('observed_monotonic_ns')
check('recovery_up_hook_event_follows_exact_exit',
    type(producer_exit_ns) is int and type(q_up_ns) is int and q_up_ns > producer_exit_ns,
    {'producer_exit_observed_ns':producer_exit_ns,'injected_q_up_callback_ns':q_up_ns,
     'hook_events':hook.get('events',[])})
check('same_operation_generation_recovered',
    cancellation.get('status') == 'recovered'
    and cancellation.get('release_confirmed') is True
    and cancellation.get('replay_allowed') is False
    and cancellation.get('task_success') is None
    and owner_result.get('phase') == 'recovered'
    and owner_result.get('release_confirmed') is True
    and cancellation.get('action_operation_id') == action.get('operation_id')
    and cancellation.get('target_generation') == owned_generation
    and type(owner_result.get('producer_exit_code')) is int,
    {'cancellation':cancellation,'action_operation_id':action.get('operation_id'),
     'action_status':action.get('status')})
readback = RAW.get('independent_readback',{})
check('separate_process_independent_neutral_readback',
    readback.get('status') == 'observed' and readback.get('process_retired') is True
    and readback.get('exit_code') == 0 and readback.get('q_down') is False
    and readback.get('generation_before') == owned_generation
    and readback.get('generation_after') == owned_generation
    and readback.get('pid') not in (RAW.get('probe_pid'), fixture.get('pid'),
        RAW.get('producer_identity_from_cancel',{}).get('pid'))
    and type(readback.get('state_witness')) is list and len(readback['state_witness']) >= 2,
    readback)
check('bounded_recovery_window',
    type(public_cancel.get('started_monotonic_ns')) is int
    and type(readback.get('returned_monotonic_ns')) is int
    and readback['returned_monotonic_ns'] - public_cancel['started_monotonic_ns']
        <= CONDITIONS['trial'].get('recovery_deadline_ms',2500)*1_000_000,
    {'cancel_started_ns':public_cancel.get('started_monotonic_ns'),
     'readback_returned_ns':readback.get('returned_monotonic_ns'),
     'limit_ms':trial.get('recovery_deadline_ms',2500)})
check('independent_saved_task_effect_and_journal_prefix',
    effect == trial.get('expected_effect') and events[:len(expected_prefix)] == expected_prefix,
    {'effect':effect,'expected':trial.get('expected_effect'),
     'journal_prefix_matches':events[:len(expected_prefix)] == expected_prefix,
     'event_count':len(events)})
close = RAW.get('public_close',{}).get('response',{})
check('fixture_session_hook_and_foreground_cleanup',
    fixture.get('exit_code') == 0 and fixture.get('window_exists_after_exit') is False
    and close.get('status') == 'closed'
    and (close.get('session') or {}).get('state') == 'closed'
    and RAW.get('hook_stopped',{}).get('thread_exited') is True
    and RAW.get('foreground_restore',{}).get('restored') is True,
    {'fixture_exit_code':fixture.get('exit_code'),'close':close,
     'hook_stopped':RAW.get('hook_stopped'),
     'foreground_restore':RAW.get('foreground_restore')})
check('runtime_task_success_remains_unclaimed',
    action.get('task_success') is None and cancellation.get('task_success') is None,
    {'action_task_success':action.get('task_success'),
     'cancellation_task_success':cancellation.get('task_success')})

passed = sum(item['passed'] for item in checks)
result = {'schema':'win32-supervised-standard-caller-cancel-audit-v1',
    'attempt_id':CONDITIONS.get('attempt_id'),'source_commit':CONDITIONS.get('source_commit'),
    'status':'PASS' if passed == len(checks) else 'FAIL_OR_UNKNOWN',
    'passed':passed,'total':len(checks),'checks':checks}
(HERE/'audit.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n',encoding='utf-8')
print(json.dumps({key:result[key] for key in ('attempt_id','status','passed','total')},sort_keys=True))
