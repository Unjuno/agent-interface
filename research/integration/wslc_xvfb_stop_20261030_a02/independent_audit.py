"""Recompute bounded claims from retained A02 receipts; no live control."""
import json
from pathlib import Path

root = Path(__file__).resolve().parent
r = json.loads((root / 'receipt.json').read_text(encoding='utf-8'))
run = json.loads((root / 'result.json').read_text(encoding='utf-8'))
cleanup = json.loads((root / 'cleanup-result.json').read_text(encoding='utf-8'))
c = r['stopped_terminal']['cancellation']['result']
recovery = r['recovery']
effect = recovery['effect_timing']
checks = {
    'run_exited_zero': run['status'] == 'completed' and run['exit'] == 0,
    'cancel_between_stop_and_resume': r['server_process']['stopped_ns'] <= r['timing_ns']['cancel_started'] <= r['timing_ns']['cancel_returned'] < r['server_resume']['monotonic_ns'],
    'old_unknown_no_replay': c['cleanup_status'] == 'UNKNOWN' and c['task_success'] is None and c['replay_allowed'] is False,
    'old_release_retained': c['owner_release_attempt']['status'] == 'not_attempted' and r['post_resume_close']['owner_release_attempt'] == c['owner_release_attempt'],
    'new_hold_observed_after_close': r['independent_readback_after_close']['keys_down']['a'] is True,
    'old_terminal_failed': r['terminal']['status'] == 'runtime_failed',
    'old_alias_refused': recovery['stale_alias_terminal']['status'] == 'refused',
    'one_new_b_and_oracle_pass': recovery['new_target_b_keypresses'] == 1 and recovery['independent_task_oracle']['status'] == 'pass' and recovery['independent_task_oracle']['task_success'] is True and all(recovery['independent_task_oracle']['checks'].values()),
    'effect_after_new_input': effect['observation_public_returned_ns'] <= effect['input_tool_started_ns'] <= effect['app_keypress_received_ns'] <= effect['app_effect_committed_ns'] <= effect['independent_readback_monotonic_ns'],
    'final_key_readback_up': r['final_cleanup']['status'] == 'completed' and r['final_cleanup']['keys_down'] == {'a': False, 'b': False},
    'exact_id_cleanup_empty': cleanup['status'] == 'completed' and cleanup['exit'] == 0 and cleanup['no_matching_container'] is True,
}
print(json.dumps({'checks': checks, 'passed': sum(checks.values()), 'total': len(checks)}, indent=2, sort_keys=True))
raise SystemExit(0 if all(checks.values()) else 1)
