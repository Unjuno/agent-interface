import json
from pathlib import Path

root = Path(__file__).resolve().parent
raw = json.loads((root / 'raw' / 'standard-mcp-xvfb-blocked-release.json').read_text(encoding='utf-8'))
cancel = raw['cancel']
close = raw['close']
release = close['owner_release_attempt']
checks = {
    'run_is_failure': raw['status'] == 'FAIL',
    'pre_cancel_synthetic_effect_observed': raw['input_before_cancel']['synthetic_effect_committed'] is True,
    'pre_cancel_held_key_observed': raw['input_before_cancel']['keys_down'].get('a') is True,
    'cancel_response_within_3000ms': raw['cancel_elapsed_ms'] < raw['conditions']['cancel_return_bound_ms'],
    'cancel_did_not_retire_owner': cancel['owner_process_retired'] is False,
    'cancel_did_not_confirm_release': cancel['release_confirmed'] is False,
    'cancel_release_unknown': cancel['cleanup_status'] == 'UNKNOWN',
    'cancel_replay_disabled': cancel['replay_allowed'] is False,
    'cancel_task_success_unknown': cancel['task_success'] is None,
    'close_later_retired_owner': close['owner_process_retired'] is True,
    'close_observed_client_disconnect': close['owner_client_disconnect']['status'] == 'disconnected',
    'release_worker_timed_out': release['reason'] == 'supervision_timeout' and release['worker_retired'] is True,
    'runtime_release_readback_not_reached': raw['independent_release_readback'] is None,
    'harness_finally_keyup_readback_recorded': raw['final_cleanup']['status'] == 'key_release_sync_completed' and raw['final_cleanup']['keys_down'] == {'a': False, 'b': False},
    'no_terminal_result': raw['terminal'] is None,
}
result = {'audit':'PASS_RAW_SEMANTICS_SCOPED' if all(checks.values()) else 'FAIL_RAW_SEMANTICS', 'checks':checks, 'scope':'read-only reconstruction of one retained GitHub Actions artifact; no rerun or release inference'}
(root / 'audit.json').write_text(json.dumps(result, indent=2, sort_keys=True) + '\n', encoding='utf-8')
print(json.dumps(result, indent=2, sort_keys=True))
if not all(checks.values()):
    raise SystemExit(1)
