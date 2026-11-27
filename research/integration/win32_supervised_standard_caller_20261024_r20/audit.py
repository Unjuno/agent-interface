"""Frozen read-only audit for bounded UNKNOWN under a blocked Win32 hook — R20."""
from __future__ import annotations
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
CONDITIONS = json.loads((HERE / 'conditions.json').read_text(encoding='utf-8'))
RAW = json.loads((HERE / 'raw.json').read_text(encoding='utf-8'))
trial = CONDITIONS['trial']
checks = []
def check(name, passed, evidence=None):
    checks.append({'name': name, 'passed': bool(passed), 'evidence': evidence})
def elapsed(a, b):
    return (b-a)/1_000_000 if type(a) is int and type(b) is int else None

fixture = RAW.get('fixture', {})
identity = fixture.get('target_identity', {})
generation = identity.get('generation')
program = RAW.get('program', {})
observation = RAW.get('public_observation', {}).get('raw_report', {})
validation = RAW.get('public_validation', {}).get('response', {})
cancel = RAW.get('public_cancel', {})
cancel_response = cancel.get('response', {})
hold = RAW.get('post_cancel_io_hold', {})
polls = hold.get('status_polls', [])
hook = hold.get('hook_trace_before_release', {})
unknown = [item for item in polls if item.get('cancellation_status') == 'unknown']
first_unknown = min(unknown, key=lambda item: item.get('returned_monotonic_ns', 2**63-1)) if unknown else {}
cancel_ns = cancel.get('started_monotonic_ns')
hold_start = hold.get('started_monotonic_ns')
hold_end = hold.get('ended_monotonic_ns')
hook_return = hook.get('callback_return_ns')
producer = RAW.get('producer_identity_from_cancel') or {}
samples = hold.get('producer_liveness_samples', [])
exit_samples = [item for item in samples if item.get('status') == 'exited'
    and item.get('wait_result') == 0 and item.get('pid') == producer.get('pid')
    and item.get('creation_time_100ns') == producer.get('creation_time_100ns')]
readbacks = RAW.get('result_readbacks', [])
terminal = readbacks[-1].get('response', {}) if readbacks else {}
row = terminal.get('result') if isinstance(terminal.get('result'), dict) else terminal
row = row if isinstance(row, dict) else {}
cancellation = row.get('cancellation') or {}
action = row.get('action') or {}
effect = RAW.get('effect_readback')
expected_effect = trial['expected_effect']

check('attempt_source_and_clean_tracked_tree',
    RAW.get('attempt_id') == CONDITIONS.get('attempt_id')
    and RAW.get('source_commit') == CONDITIONS.get('source_commit')
    and RAW.get('source_tracked_tree_clean') is True,
    {'attempt': RAW.get('attempt_id'), 'source_commit': RAW.get('source_commit'),
     'tracked_tree_clean': RAW.get('source_tracked_tree_clean')})
check('one_owned_fixture_and_matching_observation',
    identity.get('owner', {}).get('pid') == fixture.get('pid')
    and isinstance(generation, str) and len(generation) == 64
    and observation.get('target_generation') == generation,
    {'fixture_pid': fixture.get('pid'), 'generation': generation,
     'observed_generation': observation.get('target_generation')})
check('validation_and_single_exact_dispatch',
    validation.get('static_valid') is True and validation.get('status') == 'valid'
    and RAW.get('dispatch_attempts') == 1
    and program.get('program_id') == trial.get('program_id')
    and program.get('ops') == trial.get('operations')
    and program.get('source', {}).get('target_generations', {}).get('fixture') == generation,
    {'validation': validation, 'dispatch_attempts': RAW.get('dispatch_attempts'),
     'program_id': program.get('program_id')})
check('hook_observed_injected_q_and_cancel_was_bounded',
    hook.get('vk') == ord('Q') and hook.get('flags', 0) & 0x10
    and type(hook.get('callback_entry_ns')) is int
    and type(cancel.get('returned_monotonic_ns')) is int
    and cancel_response.get('status') == 'pending'
    and (cancel.get('elapsed_ms') or float('inf')) <= 1000,
    {'hook': hook, 'cancel': cancel_response, 'cancel_elapsed_ms': cancel.get('elapsed_ms')})
check('producer_exact_identity_exited_during_retained_callback',
    len(samples) >= 4 and bool(exit_samples)
    and all(item.get('pid') == producer.get('pid')
        and item.get('creation_time_100ns') == producer.get('creation_time_100ns')
        and type(item.get('sampled_monotonic_ns')) is int
        and type(hold_start) is int and type(hold_end) is int
        and hold_start <= item['sampled_monotonic_ns'] <= hold_end for item in samples)
    and type(hook_return) is int and hook_return > min(
        item['sampled_monotonic_ns'] for item in exit_samples),
    {'producer_identity': producer, 'samples': samples,
     'callback_return_ns': hook_return})
unknown_elapsed = elapsed(cancel_ns, first_unknown.get('returned_monotonic_ns'))
check('terminal_unknown_within_bound_while_hook_remains_blocked',
    type(hold_start) is int and type(hold_end) is int
    and elapsed(hold_start, hold_end) >= trial.get('post_cancel_hook_hold_ms', 0)-50
    and type(hook.get('callback_return_ns')) is int
    and hook['callback_return_ns'] > hold_end
    and type(cancel_ns) is int and type(first_unknown.get('returned_monotonic_ns')) is int
    and first_unknown['returned_monotonic_ns'] < hold_end
    and unknown_elapsed is not None
    and unknown_elapsed <= trial.get('unknown_terminal_bound_ms', 0)
    and first_unknown.get('action_status') == 'unknown',
    {'hold_ms': elapsed(hold_start, hold_end), 'unknown_elapsed_ms': unknown_elapsed,
     'unknown_poll': first_unknown, 'callback_return_ns': hook.get('callback_return_ns'),
     'hold_end_ns': hold_end})
check('unknown_keeps_release_replay_and_task_success_unclaimed',
    bool(unknown) and all(item.get('cancellation_release_confirmed') is False
        and item.get('owner_release_confirmed') is False for item in unknown)
    and cancellation.get('status') == 'unknown'
    and cancellation.get('release_confirmed') is False
    and cancellation.get('replay_allowed') is False
    and cancellation.get('task_success') is None
    and action.get('task_success') is None,
    {'unknown_polls': unknown, 'terminal_cancellation': cancellation,
     'action': action})
hook_events = hook.get('events', [])
check('held_q_down_suppressed_on_callback_return',
    hook.get('blocked_q_down_suppressed') is True
    and any(item.get('message') == 0x0100 and item.get('suppressed') is True
        for item in hook_events),
    {'suppressed': hook.get('blocked_q_down_suppressed'), 'events': hook_events})
check('exact_fixture_effect_and_cleanup',
    effect == expected_effect and fixture.get('exit_code') == 0
    and fixture.get('window_exists_after_exit') is False
    and RAW.get('hook_stopped', {}).get('thread_exited') is True
    and RAW.get('foreground_restore', {}).get('restored') is True,
    {'effect': effect, 'expected_effect': expected_effect, 'fixture': fixture,
     'hook_stopped': RAW.get('hook_stopped'),
     'foreground_restore': RAW.get('foreground_restore')})

close_attempts = RAW.get('public_close_attempts', [])
close_statuses = [item.get('response', {}).get('status') for item in close_attempts
                  if isinstance(item, dict)]
check('unknown_custody_keeps_public_close_busy',
    bool(close_statuses) and all(status == 'busy' for status in close_statuses)
    and (RAW.get('session_close_report') or {}).get('status') == 'busy',
    {'close_statuses': close_statuses,
     'session_close_report': RAW.get('session_close_report')})

passed = sum(item['passed'] for item in checks)
result = {'schema': 'win32-supervised-standard-caller-r20-audit-v1',
    'attempt_id': CONDITIONS.get('attempt_id'), 'source_commit': CONDITIONS.get('source_commit'),
    'status': 'PASS' if passed == len(checks) else 'FAIL_OR_UNKNOWN',
    'passed': passed, 'total': len(checks), 'checks': checks,
    'claim_scope': 'bounded fail-closed UNKNOWN only; no release or recovery success'}
(HERE / 'audit.json').write_text(json.dumps(result, indent=2, sort_keys=True) + '\n',
                                 encoding='utf-8')
print(json.dumps({'status': result['status'], 'passed': passed, 'total': len(checks)}, sort_keys=True))
