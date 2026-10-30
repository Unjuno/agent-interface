"""Recompute scoped A07 checks from the retained test-generated evidence."""
import hashlib
import json
import math
from pathlib import Path

root = Path(__file__).resolve().parent / 'a07'
r = json.loads((root / 'result.json').read_text(encoding='utf-8'))
run = json.loads((root / 'runner-result.json').read_text(encoding='utf-8'))
cleanup = json.loads((root / 'cleanup-result.json').read_text(encoding='utf-8'))
conditions = json.loads((root / 'conditions.json').read_text(encoding='utf-8'))
t, e, old = r['times'], r['events'], r['old_terminal']
checks = {
    'exit_and_runner_checks': run['status'] == 'completed' and run['exit'] == 0 and r['status'] == 'PASS' and len(r['checks']) == 18 and all(v is True for v in r['checks'].values()),
    'old_unknown_no_replay': old['status'] == 'runtime_failed' and old['cleanup_status'] == 'UNKNOWN' and old['task_success'] is None and old['replay_allowed'] is False,
    'old_target_exit_before_server_kill': type(r['old_target_exit_before_display_kill']) is int,
    'fresh_recorder_covers_delayed_request': t['old_queued'] < t['old_exit'] < t['fresh_started'] < t['recorder_ready'] < t['old_queued'] + 8_000_000_000 < t['horizon_end'],
    'coast_distance': math.isclose(math.dist(r['coast_before'], r['coast_after']), r['coast_displacement'], abs_tol=1e-8),
    'move_distance': math.isclose(math.dist(r['coast_after'], r['move_after']), r['move_displacement'], abs_tol=1e-8),
    # 25 and 56 are observed raw keycodes; independent mapping to W/B was not retained.
    'code25_down_up': any(x['type'] == 2 and x['detail'] == 25 for x in e) and any(x['type'] == 3 and x['detail'] == 25 for x in e),
    'no_code56_before_horizon': not any(x['type'] == 2 and x['detail'] == 56 and x['ns'] < t['horizon_end'] for x in e),
    'code56_positive_after': any(x['type'] == 2 and x['detail'] == 56 and x['ns'] >= t['horizon_end'] for x in e),
    'fresh_close_verified': r['fresh_close']['verified'] is True,
    'own_container_absent': cleanup['status'] == 'completed' and cleanup['exit'] == 0 and cleanup['no_matching_container'] is True,
    'runner_hash': hashlib.sha256((root / 'runner.py').read_bytes()).hexdigest() == conditions['runner_sha256'],
}
for row in (root / 'SHA256SUMS').read_text(encoding='ascii').splitlines():
    digest, name = row.split('  ', 1)
    checks['sha256:' + name] = hashlib.sha256((root / name).read_bytes()).hexdigest() == digest
print(json.dumps({'checks': checks, 'passed': sum(checks.values()), 'total': len(checks)}, indent=2, sort_keys=True))
raise SystemExit(0 if all(checks.values()) else 1)
