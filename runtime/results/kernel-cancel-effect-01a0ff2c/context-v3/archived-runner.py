from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json
import os
import platform
import re
import subprocess
import sys

root = Path(__file__).resolve().parents[1]
out = root / 'outputs/cancel-effect-context-v3-01a0ff2c'
assert not (out / 'RUN_PLAN.json').exists(), 'Do not repeat an executed plan'
context = json.loads((out / 'SOURCE_REFRESH.json').read_text(encoding='utf-8'))
assert platform.python_version() == '3.12.10'
env = os.environ.copy()
env.pop('PYTHONPATH', None)
env.update(PYTHONHASHSEED='0', PYTHONNOUSERSITE='1', PYTHONDONTWRITEBYTECODE='1')

def utc():
    return datetime.now(timezone.utc).isoformat()

def verify_sources():
    for arm, rows in context['pins'].items():
        for row in rows:
            data = (out / (arm + '-source') / row['path']).read_bytes()
            assert len(data) == row['bytes']
            assert hashlib.sha256(data).hexdigest() == row['sha256']

verify_sources()
runs = [
    {'id': 'before-normal', 'arm': 'before', 'options': [], 'exit': 1, 'failures': 2},
    {'id': 'after-normal', 'arm': 'after', 'options': [], 'exit': 0, 'failures': 0},
    {'id': 'after-optimized', 'arm': 'after', 'options': ['-O'], 'exit': 0, 'failures': 0},
]
plan = {
    'id': '6894-context-v3-ordinary-regression-20261003-01a0ff2c',
    'frozen_utc': utc(), 'kind': 'ordinary regression, not a formal replay',
    'source_refresh_sha256': hashlib.sha256((out / 'SOURCE_REFRESH.json').read_bytes()).hexdigest(),
    'runner_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
    'python': sys.executable, 'python_version': platform.python_version(),
    'platform': platform.platform(),
    'environment': {k: env[k] for k in ['PYTHONHASHSEED', 'PYTHONNOUSERSITE', 'PYTHONDONTWRITEBYTECODE']},
    'PYTHONPATH_removed': True, 'methods_per_run': 40, 'timeout_seconds': 30,
    'runs': runs,
    'expected_before_failed_methods': [
        'test_stop_after_begin_without_receipt_preserves_possible_effect',
        'test_stale_cancel_refusal_then_fresh_release_preserves_possible_effect',
    ],
    'limits': 'Inert kernel contracts only; no GUI/backend task effects, real release, performance or main certificate.',
}
(out / 'RUN_PLAN.json').write_text(json.dumps(plan, indent=2, sort_keys=True) + '\n', encoding='utf-8', newline='\n')
receipts = []
for run in runs:
    verify_sources()
    argv = [sys.executable, *run['options'], '-m', 'unittest', 'discover', '-s', 'runtime/kernel', '-p', 'test_*.py', '-v']
    cwd = out / (run['arm'] + '-source')
    started = utc()
    proc = subprocess.Popen(argv, cwd=cwd, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    timed_out = False
    try:
        stdout, stderr = proc.communicate(timeout=30)
    except subprocess.TimeoutExpired:
        timed_out = True
        proc.kill()
        stdout, stderr = proc.communicate()
    ended = utc()
    (out / (run['id'] + '.stdout.log')).write_bytes(stdout)
    (out / (run['id'] + '.stderr.log')).write_bytes(stderr)
    text = stderr.decode('utf-8', errors='strict')
    count = re.findall(r'^Ran (\d+) tests? in ', text, re.M)
    failed_methods = re.findall(r'^FAIL: (\w+) \(', text, re.M)
    errors = re.findall(r'^ERROR: (\w+) \(', text, re.M)
    receipt = {
        'id': run['id'], 'argv': argv, 'cwd': str(cwd), 'pid': proc.pid,
        'started_utc': started, 'ended_utc': ended, 'exit_code': proc.returncode,
        'timed_out': timed_out, 'methods': int(count[0]) if len(count) == 1 else None,
        'failed_methods': failed_methods, 'error_methods': errors,
        'stdout_bytes': len(stdout), 'stderr_bytes': len(stderr),
        'stdout_sha256': hashlib.sha256(stdout).hexdigest(),
        'stderr_sha256': hashlib.sha256(stderr).hexdigest(),
    }
    receipts.append(receipt)
    (out / 'RUN_RECEIPTS.json').write_text(json.dumps(receipts, indent=2, sort_keys=True) + '\n', encoding='utf-8', newline='\n')
    assert not timed_out and proc.returncode == run['exit'], receipt
    assert receipt['methods'] == 40 and not errors, receipt
    if run['id'] == 'before-normal':
        assert set(failed_methods) == set(plan['expected_before_failed_methods']), receipt
    else:
        assert not failed_methods and text.rstrip().endswith('OK'), receipt
    print(json.dumps({k: receipt[k] for k in ['id', 'exit_code', 'methods', 'failed_methods', 'error_methods']}), flush=True)
verify_sources()
(out / 'REGRESSION_RESULT.json').write_text(json.dumps({
    'source_unchanged_after_runs': True, 'ordinary_regression_pass': True,
    'before_expected_failures': 2, 'after_normal_methods': 40, 'after_optimized_methods': 40,
    'plan_sha256': hashlib.sha256((out / 'RUN_PLAN.json').read_bytes()).hexdigest(),
    'receipts_sha256': hashlib.sha256((out / 'RUN_RECEIPTS.json').read_bytes()).hexdigest(),
    'formal_replay_count': 0, 'main_apply_certificate': False,
}, indent=2, sort_keys=True) + '\n', encoding='utf-8', newline='\n')
