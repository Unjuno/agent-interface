from pathlib import Path
import json
import re

root = Path(__file__).parent
conditions = json.loads((root / 'CONDITIONS.json').read_text(encoding='utf-8'))
raw = json.loads((root / 'result.json').read_text(encoding='utf-8'))
stdout = (root / 'stdout.txt').read_text(encoding='utf-8')
xvfb_after = (root / 'xvfb-after-run.txt').read_text(encoding='utf-8-sig')
release = raw['independent_release_readback']
late = raw['late_request_horizon_readback']
terminal = raw['terminal']
cancel = raw['cancel']
fence = raw['terminal_owner_liveness_fence']
timing = raw['timing_ns']
disconnect = cancel['owner_client_disconnect']
match = re.search(r'Ran 1 test in ([0-9.]+)s', stdout)
checks = {
    'python_unittest_one_test_ok': bool(match) and '\nOK\n' in stdout,
    'private_xvfb_identity_captured': raw['xvfb']['status'] == 'captured' and raw['xvfb']['pid'] > 0,
    'blocked_sync_marker_matches_owner': raw['blocked_owner_sync']['owner_pid'] == disconnect['expected_pid'],
    'accepted_initial_input_before_block': raw['input_before_cancel']['keys_down'] == {'a': True, 'b': False} and not raw['input_before_cancel']['owner_sync_return_receipt_present'],
    'cancel_within_3000ms': 0 <= (timing['cancel_returned'] - timing['cancel_started']) / 1_000_000 <= conditions['conditions']['cancel_return_bound_ms'],
    'owner_client_disconnect_confirmed': disconnect['status'] == 'disconnected' and disconnect['observer_pid'] == disconnect['observed_pid'] and disconnect['observed_pid'] != disconnect['expected_pid'] and disconnect['worker_exitcode'] == 0,
    'independent_release_readback_verified': release['owner_release_attempt']['status'] == 'readback_verified' and release['owner_release_attempt']['worker_exitcode'] == 0 and release['keys_down'] == {'a': False, 'b': False},
    'delayed_request_horizon_observed': late['ms_after_cancel_start'] >= conditions['conditions']['delayed_keypress_ms'] and late['late_keypress_b_observed'] is False and late['keys_down'] == {'a': False, 'b': False},
    'independent_synthetic_task_oracle_pass': raw['independent_task_oracle']['status'] == 'pass' and raw['independent_task_oracle']['task_success'] is True and all(raw['independent_task_oracle']['checks'].values()),
    'liveness_timestamp_fence_observed': isinstance(fence['liveness_observed_monotonic_ns'], int) and (fence['liveness_observed_monotonic_ns'] < fence['cancel_returned_monotonic_ns'] or fence['alive'] is False),
    'caller_retains_conservative_unknown': terminal['release_confirmed'] is False and terminal['cleanup_status'] == 'UNKNOWN' and terminal['task_success'] is None and terminal['replay_allowed'] is False,
    'terminal_result_bounded': raw['terminal_elapsed_ms'] < conditions['conditions']['terminal_result_bound_ms'],
    'final_cleanup_all_keys_up': raw['final_cleanup']['status'] == 'key_release_sync_completed' and raw['final_cleanup']['keys_down'] == {'a': False, 'b': False},
    'private_xvfb_process_stopped': f"private_xvfb_pid={raw['xvfb']['pid']} state=absent" in xvfb_after,
}
summary = {
    'run_id': conditions['run_id'],
    'decision': 'PASS_SCOPED_NATIVE_WSL_XVFB_TIMESTAMP_ORDER_AND_BOUNDED_RELEASE' if all(checks.values()) else 'FAIL_OR_INCOMPLETE',
    'checks': checks,
    'derived': {
        'test_runtime_seconds': float(match.group(1)) if match else None,
        'cancel_elapsed_ms': (timing['cancel_returned'] - timing['cancel_started']) / 1_000_000,
        'disconnect_elapsed_ms': disconnect['elapsed_ms'],
        'release_elapsed_ms': release['owner_release_attempt']['elapsed_ms'],
        'horizon_ms_after_cancel_start': late['ms_after_cancel_start'],
        'liveness_precedes_cancel_by_ms': (fence['cancel_returned_monotonic_ns'] - fence['liveness_observed_monotonic_ns']) / 1_000_000,
        'terminal_elapsed_ms': raw['terminal_elapsed_ms'],
    },
    'qualification': 'One native WSL Ubuntu/Xvfb run only; no WSLc, Docker, model, physical desktop, full server-stop, MAP01, population reliability, or efficiency claim. Caller-level release remains UNKNOWN and caller task_success remains null.'
}
(root / 'audit.json').write_text(json.dumps(summary, indent=2, sort_keys=True) + '\n', encoding='utf-8', newline='\n')
print(summary['decision'])
for name, value in checks.items():
    print(('PASS' if value else 'FAIL'), name)
print(json.dumps(summary['derived'], sort_keys=True))
