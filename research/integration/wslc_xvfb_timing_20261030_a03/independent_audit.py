"""Recompute A03 evidence checks from retained records; no live control."""
import hashlib
import json
from pathlib import Path

root = Path(__file__).resolve().parent
r = json.loads((root / 'receipt.json').read_text(encoding='utf-8'))
run = json.loads((root / 'result.json').read_text(encoding='utf-8'))
cleanup = json.loads((root / 'cleanup-result.json').read_text(encoding='utf-8'))
o = r['stopped_terminal_observation']
s = r['server_process']
c = r['stopped_terminal']['cancellation']['result']
fresh = r['recovery']
checks = {
    'test_exit_zero': run['status'] == 'completed' and run['exit'] == 0,
    'same_server_identity': all(o['process'][k] == s[k] for k in ('pid', 'start_ticks', 'executable', 'command')),
    'stopped_at_observation': o['process']['state'] in ('T', 't') and o['cancellation_status'] in ('completed', 'unknown'),
    'observation_after_stop_before_resume': s['stopped_ns'] <= o['before_process_read_ns'] <= o['after_process_read_ns'] < r['server_resume']['monotonic_ns'],
    'old_unknown_no_replay': c['cleanup_status'] == 'UNKNOWN' and c['replay_allowed'] is False and c['task_success'] is None,
    'old_release_receipt_preserved': c['owner_release_attempt']['status'] == 'not_attempted' and r['post_resume_close']['owner_release_attempt'] == c['owner_release_attempt'],
    'new_hold_survives': r['independent_readback_after_close']['keys_down']['a'] is True,
    'fresh_synthetic_effect': fresh['independent_task_oracle']['status'] == 'pass' and fresh['independent_task_oracle']['task_success'] is True and fresh['new_target_b_keypresses'] == 1,
    'final_keys_up': r['final_cleanup']['status'] == 'completed' and r['final_cleanup']['keys_down'] == {'a': False, 'b': False},
    'own_container_absent': cleanup['status'] == 'completed' and cleanup['exit'] == 0 and cleanup['no_matching_container'] is True,
}
for row in (root / 'SHA256SUMS').read_text(encoding='ascii').splitlines():
    digest, name = row.split('  ', 1)
    checks['sha256:' + name] = hashlib.sha256((root / name).read_bytes()).hexdigest() == digest
print(json.dumps({'checks': checks, 'passed': sum(checks.values()), 'total': len(checks)}, indent=2, sort_keys=True))
raise SystemExit(0 if all(checks.values()) else 1)
