"""Frozen read-only audit for supervised standard-caller cancellation R33."""
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
polls = RAW.get('hook_wait',{}).get('status_polls',[])
poll_interval_ms = trial.get('hook_status_poll_interval_ms',0)
max_polls = (CONDITIONS.get('timeouts_seconds',{}).get('hook_entry',0)*1000 // max(1,poll_interval_ms)) + 4
check('bounded_same_call_status_polling_during_hook_window',
    isinstance(polls,list) and 1 <= len(polls) <= max_polls
    and any(item.get('call_id') == RAW.get('blocked_call_id')
            and item.get('is_error') is False for item in polls)
    and all(((index == 0 and item.get('is_error') is True
              and item.get('status') == 'unknown_call'
              and item.get('operation_invoked') is False
              and item.get('call_id') is None)
             or (item.get('is_error') is False
                 and item.get('call_id') == RAW.get('blocked_call_id')))
            and type(item.get('started_monotonic_ns')) is int
            and type(item.get('returned_monotonic_ns')) is int
            and item['returned_monotonic_ns'] >= item['started_monotonic_ns']
            for index,item in enumerate(polls)),
    {'poll_count':len(polls),'max_polls':max_polls,'polls':polls})
check('hook_callback_held_through_single_cancel',
    type(hook.get('callback_entry_ns')) is int
    and type(hook.get('callback_return_ns')) is int
    and type(public_cancel.get('returned_monotonic_ns')) is int
    and hook['callback_entry_ns'] <= public_cancel.get('started_monotonic_ns',-1)
    and hook['callback_return_ns'] >= public_cancel['returned_monotonic_ns']
    and hook['callback_return_ns'] - hook['callback_entry_ns']
        <= trial.get('native_stimulus',{}).get('max_callback_hold_ms',0)*1_000_000,
    {'hook_entry_ns':hook.get('callback_entry_ns'),
     'hook_return_ns':hook.get('callback_return_ns'),
     'cancel_start_ns':public_cancel.get('started_monotonic_ns'),
     'cancel_return_ns':public_cancel.get('returned_monotonic_ns'),
     'hold_limit_ms':trial.get('native_stimulus',{}).get('max_callback_hold_ms')})
q_down_events = [item for item in hook.get('events', [])
                 if item.get('message') == 0x0100 and item.get('vk') == ord('Q')
                 and item.get('flags', 0) & 0x10]
q_down_event = q_down_events[0] if q_down_events else {}
pre_cancel_state = RAW.get('pre_cancel_independent_readback', {})
check('hook_observed_injected_q_down_before_cancel',
    bool(q_down_event)
    and type(q_down_event.get('callback_return_ns')) is int
    and type(hook.get('callback_entry_ns')) is int
    and q_down_event['callback_return_ns'] <= hook['callback_entry_ns']
    and type(public_cancel.get('started_monotonic_ns')) is int
    and hook['callback_entry_ns'] <= public_cancel['started_monotonic_ns']
    and pre_cancel_state.get('status') == 'observed'
    and pre_cancel_state.get('q_down') is True
    and pre_cancel_state.get('generation_before') == owned_generation
    and pre_cancel_state.get('generation_after') == owned_generation,
    {'q_down_event':q_down_event,'held_q_up_entry_ns':hook.get('callback_entry_ns'),
     'pre_cancel_independent_readback':pre_cancel_state,
     'cancel_started_ns':public_cancel.get('started_monotonic_ns')})
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
hook_stopped = RAW.get('hook_stopped', {})
hook_was_silently_removed = (
    hook_stopped.get('unhook_return') is False
    and hook_stopped.get('unhook_last_error') == 1404
    and type(hook_stopped.get('callback_return_ns')) is int)
q_up_events_after_exit = [item for item in hook_stopped.get('events', [])
    if item.get('message') == 0x0101 and item.get('vk') == ord('Q')
    and item.get('flags', 0) & 0x10
    and type(item.get('callback_entry_ns')) is int
    and type(producer_exit_ns) is int
    and item['callback_entry_ns'] > producer_exit_ns]
q_up_events = [item for item in hook_stopped.get('events', [])
    if item.get('message') == 0x0101 and item.get('vk') == ord('Q')
    and item.get('flags', 0) & 0x10]
first_held = next((item for item in q_up_events
    if item.get('callback_entry_ns') == hook.get('callback_entry_ns')), {})
second_recovery = next((item for item in q_up_events
    if type(first_held.get('callback_return_ns')) is int
    and type(item.get('callback_entry_ns')) is int
    and item['callback_entry_ns'] > first_held['callback_return_ns']
    and type(item.get('callback_return_ns')) is int), {})
check('distinct_recovery_q_up_hook_callback_after_held_callback',
    bool(first_held) and bool(second_recovery)
    and second_recovery.get('callback_entry_ns',0) > first_held['callback_return_ns'],
    {'first_held_q_up':first_held,'second_recovery_q_up':second_recovery,
     'q_up_events':q_up_events})
check('recovery_up_hook_event_or_silent_hook_removal_after_exact_exit',
    type(producer_exit_ns) is int
    and (bool(q_up_events_after_exit)
         or (not hook_stopped.get('events') and hook_was_silently_removed)),
    {'producer_exit_observed_ns':producer_exit_ns,
     'q_up_callback_events_after_exit':q_up_events_after_exit,
     'hook_events':hook_stopped.get('events',[]),'hook_stopped':hook_stopped,
     'silent_removal_witness':hook_was_silently_removed})
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
hold = RAW.get('post_cancel_io_hold', {})
hold_polls = hold.get('status_polls', [])
hold_start = hold.get('started_monotonic_ns')
hold_end = hold.get('ended_monotonic_ns')
hold_hook_before = hold.get('hook_trace_before_release', {})
hold_hook_after = hold.get('hook_trace_after_release', {})
blocked_readback = RAW.get('blocked_io_independent_readback', {})
readback = RAW.get('independent_readback', {})
final_hook_trace = RAW.get('hook_stopped', {})
callback_return = final_hook_trace.get('callback_return_ns')
release_seen_during_hold = any(
    item.get('is_error') is False
    and item.get('cancellation_status') == 'recovered'
    and item.get('cancellation_release_confirmed') is True
    and item.get('owner_release_confirmed') is True
    and type(item.get('returned_monotonic_ns')) is int
    and type(hold_start) is int and type(hold_end) is int
    and hold_start <= item['returned_monotonic_ns'] <= hold_end
    for item in hold_polls)
trace_rows = RAW.get('cancellation_call_trace', [])
recovery_helper_pids = {item.get('pid') for item in trace_rows
    if item.get('event') == 'helper_enter' and item.get('helper') == 'recovery'}
recovery_helper_pids |= {item.get('pid') for item in trace_rows
    if item.get('event') == 'helper_main_enter' and item.get('helper') == 'recovery'}
q_up_returns = [item.get('monotonic_ns') for item in trace_rows
    if item.get('event') == 'sendinput_return' and item.get('pid') in recovery_helper_pids
    and item.get('input_type') == 1 and item.get('vk') == ord('Q')
    and item.get('key_up') is True and type(item.get('monotonic_ns')) is int]
q_up_return_ns = min(q_up_returns) if q_up_returns else None
series_info = RAW.get('independent_state_series') or {}
series_path = HERE / series_info.get('samples_path','')
series_records = ([json.loads(line) for line in series_path.read_text(encoding='utf-8').splitlines()
                   if line.strip()] if series_path.is_file() else [])
series_samples = [row for row in series_records if row.get('record_type') == 'sample']
series_summary = next((row for row in reversed(series_records)
                       if row.get('record_type') == 'summary'), {})
series_pid = series_info.get('pid')
valid_release_samples = [sample for sample in series_samples
    if sample.get('q_down') is False
    and sample.get('expected_generation') == owned_generation
    and sample.get('generation_before') == owned_generation
    and sample.get('generation_after') == owned_generation
    and type(sample.get('started_monotonic_ns')) is int
    and type(sample.get('returned_monotonic_ns')) is int
    and type(q_up_return_ns) is int
    and sample['started_monotonic_ns'] > q_up_return_ns
    and type(hold_end) is int
    and sample['returned_monotonic_ns'] <= hold_end
    and type(series_pid) is int
    and sample.get('pid') == series_pid]
readback_during_hold = (series_info.get('status') == 'observed'
    and series_info.get('exit_code') == 0
    and series_summary.get('status') == 'observed'
    and len(series_samples) >= 10
    and bool(valid_release_samples))
readback_start = (valid_release_samples[0].get('started_monotonic_ns')
                  if valid_release_samples else None)
check('bounded_release_and_independent_q_up_while_native_callback_blocked',
    type(hold_start) is int and type(hold_end) is int
    and elapsed(hold_start, hold_end) >= trial.get('post_cancel_hook_hold_ms',0)-50
    and hold_hook_before.get('callback_return_ns') is None
    and type(hold_hook_before.get('callback_entry_ns')) is int
    and type(callback_return) is int and callback_return > hold_end
    and len(hold_polls) >= 2
    and all(item.get('is_error') is False
            and type(item.get('returned_monotonic_ns')) is int
            and hold_start <= item['returned_monotonic_ns'] <= hold_end
            for item in hold_polls)
    and release_seen_during_hold and readback_during_hold,
    {'hold_ms':elapsed(hold_start,hold_end),'target_hold_ms':trial.get('post_cancel_hook_hold_ms'),
     'callback_before_release':hold_hook_before,'callback_after_release':hold_hook_after,
     'q_up_sendinput_return_ns':q_up_return_ns,'hold_end_ns':hold_end,
     'polls':hold_polls,'release_seen_during_hold':release_seen_during_hold,
     'prearmed_series_info':series_info,'series_summary':series_summary,
     'sample_count':len(series_samples),
     'first_valid_release_samples':valid_release_samples[:3],
     'readback_started_ns':readback_start,
     'final_hook_trace':final_hook_trace})
check('strict_minimum_21_same_call_hold_polls',
    len(hold_polls) >= 21
    and all(type(item.get('returned_monotonic_ns')) is int
            and type(hold_start) is int and type(hold_end) is int
            and hold_start <= item['returned_monotonic_ns'] <= hold_end
            for item in hold_polls),
    {'poll_count':len(hold_polls),'required_minimum':21,
     'blocked_call_id':RAW.get('blocked_call_id'),
     'poll_call_id_source':'Frozen probe loop uses the blocked_call_id argument for every interface_results poll; raw rows do not repeat call_id.'})
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
    and type(blocked_readback.get('returned_monotonic_ns')) is int
    and blocked_readback['returned_monotonic_ns'] - public_cancel['started_monotonic_ns']
        <= CONDITIONS['trial'].get('recovery_deadline_ms',2500)*1_000_000
    and blocked_readback.get('q_down') is False,
    {'cancel_started_ns':public_cancel.get('started_monotonic_ns'),
     'blocked_readback_returned_ns':blocked_readback.get('returned_monotonic_ns'),
     'q_down':blocked_readback.get('q_down'),
     'limit_ms':trial.get('recovery_deadline_ms',2500)})
check('independent_saved_task_effect_and_journal_prefix',
    effect == trial.get('expected_effect') and events[:len(expected_prefix)] == expected_prefix,
    {'effect':effect,'expected':trial.get('expected_effect'),
     'journal_prefix_matches':events[:len(expected_prefix)] == expected_prefix,
     'event_count':len(events)})
close = RAW.get('public_close',{}).get('response',{})
close_attempts = RAW.get('public_close_attempts',[])
close_interval_ms = trial.get('close_retry_interval_ms',0)
close_max_attempts = (CONDITIONS.get('timeouts_seconds',{}).get('close_drain',0)*1000 // max(1,close_interval_ms)) + 2
close_elapsed_ms = ((close_attempts[-1].get('returned_monotonic_ns',0)
    - close_attempts[0].get('started_monotonic_ns',0))/1_000_000
    if close_attempts else None)
check('fixture_session_hook_and_foreground_cleanup',
    fixture.get('exit_code') == 0 and fixture.get('window_exists_after_exit') is False
    and close.get('status') == 'closed'
    and (close.get('session') or {}).get('state') == 'closed'
    and 1 <= len(close_attempts) <= close_max_attempts
    and all(item.get('response',{}).get('status') == 'busy'
            for item in close_attempts[:-1])
    and close_elapsed_ms is not None
    and close_elapsed_ms <= (CONDITIONS.get('timeouts_seconds',{}).get('close_drain',0)*1000
        + CONDITIONS.get('timeouts_seconds',{}).get('close_response',0)*1000)
    and RAW.get('hook_stopped',{}).get('thread_exited') is True
    and RAW.get('foreground_restore',{}).get('restored') is True,
    {'fixture_exit_code':fixture.get('exit_code'),'close':close,
     'close_attempt_count':len(close_attempts),'close_max_attempts':close_max_attempts,
     'close_elapsed_ms':close_elapsed_ms,
     'hook_stopped':RAW.get('hook_stopped'),
     'foreground_restore':RAW.get('foreground_restore')})
check('subsecond_result_cannot_claim_r29_strict_gate',
    trial.get('post_cancel_hook_hold_ms',0) < 1250
    and 'R29 strict 1250 ms blocked-callback gate' in CONDITIONS.get('claims_excluded',[]),
    {'hold_ms':trial.get('post_cancel_hook_hold_ms'),
     'strict_gate_required_ms':1250,
     'excluded_claims':CONDITIONS.get('claims_excluded',[])})
check('runtime_task_success_remains_unclaimed',
    action.get('task_success') is None and cancellation.get('task_success') is None,
    {'action_task_success':action.get('task_success'),
     'cancellation_task_success':cancellation.get('task_success')})

passed = sum(item['passed'] for item in checks)
result = {'schema':'win32-supervised-standard-caller-r35-diagnostic-audit-v1',
    'attempt_id':CONDITIONS.get('attempt_id'),'source_commit':CONDITIONS.get('source_commit'),
    'repair_note':'R35 supplemental diagnostic evaluator: restores the intended independent_readback binding, validates pre-armed same-generation state samples against the recovery SendInput return and callback-hold end, enforces at least 21 polls, and checks distinct recovery hook delivery. The frozen R29 1250 ms gate is explicitly not claimed.',
    'status':('DIAGNOSTIC_PASS' if passed == len(checks) and trial.get('post_cancel_hook_hold_ms',0) < 1250 else 'FAIL_OR_UNKNOWN'),
    'passed':passed,'total':len(checks),'checks':checks}
(HERE/'audit_repaired.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n',encoding='utf-8')
print(json.dumps({key:result[key] for key in ('attempt_id','status','passed','total')},sort_keys=True))

