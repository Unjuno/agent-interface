#!/usr/bin/env python3
"""Run the focused #8272 + #8269 candidate-stack integration tests."""
import contextlib
import hashlib
import importlib.metadata
import io
import json
import platform
import sys
import unittest
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path('/workspace')
OUT = Path('/out')
TESTS = (
    ('executor_v13', 'test_executor_v13'),
    ('batch_key_measurement_composition', 'test_batch_key_measurement_composition'),
)
SOURCE_PATHS = (
    'research/live_control/executor_v13.py',
    'research/live_control/test_executor_v13.py',
    'research/live_control/input_owner_v12.py',
    'research/live_control/test_batch_key_measurement_composition.py',
    'research/doom/doom_batch_key_measurement_backend_v1.py',
)
MAIN = '75bfe2badd49376ac33cd8a87030e7a6a3396ecf'
PR_HEADS = {
    '8261': '4190104d0c72a025093c8569fdbd216b5929de0b',
    '8266': 'e7be07d196eebe00d9f306087edf5890cc0ecc98',
    '8269': '9f7a4a96847ee29787a87f6fb238e71da112712c',
    '8272': 'c9f054be4333de65cca57eac3e696dc3b9633b41',
}
SOURCE_TREE = '0c062cc8e15f1c003daac0108d452f07051ad21a'
IMAGE = 'sha256:b82a3260f3e5839b9dce6d745233f09c9189d5f2154cf7a6d18e24d190c10907'


def sha256(path):
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(chunk)
    return digest.hexdigest()


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    sys.path.insert(0, str(ROOT / 'research/live_control'))
    sys.path.insert(1, str(ROOT / 'research/doom'))
    # session_v7 imports vizdoom, but the focused fake-X tests never use it.
    vizdoom = type(sys)('vizdoom')
    vizdoom.__version__ = 'not-used-test-import-stub'
    vizdoom.scenarios_path = '/tmp'
    sys.modules['vizdoom'] = vizdoom

    results = {}
    started = datetime.now(timezone.utc).isoformat()
    for label, module in TESTS:
        suite = unittest.defaultTestLoader.loadTestsFromName(module)
        stdout = io.StringIO()
        stderr = io.StringIO()
        with contextlib.redirect_stdout(stdout):
            result = unittest.TextTestRunner(stream=stderr, verbosity=2).run(suite)
        (OUT / f'{label}.stdout.log').write_text(stdout.getvalue(), encoding='utf-8')
        (OUT / f'{label}.stderr.log').write_text(stderr.getvalue(), encoding='utf-8')
        results[label] = {
            'tests_run': result.testsRun,
            'failures': [test.id() for test, _ in result.failures],
            'errors': [test.id() for test, _ in result.errors],
            'was_successful': result.wasSuccessful(),
            'stdout_sha256': sha256(OUT / f'{label}.stdout.log'),
            'stderr_sha256': sha256(OUT / f'{label}.stderr.log'),
        }

    deps = {}
    for name in ('Pillow', 'python-xlib', 'six'):
        deps[name] = importlib.metadata.version(name)
    all_ok = all(row['was_successful'] for row in results.values())
    report = {
        'schema': 'issue-59-current-main-candidate-stack-check-v1',
        'status': 'PASS_SCOPED' if all_ok else 'FAIL',
        'started_utc': started,
        'ended_utc': datetime.now(timezone.utc).isoformat(),
        'main_sha': MAIN,
        'candidate_source_tree_before_evidence': SOURCE_TREE,
        'candidate_pr_heads': PR_HEADS,
        'image_id': IMAGE,
        'runtime': {
            'python': sys.version,
            'platform': platform.platform(),
            'dependencies': deps,
            'network': 'none',
            'source_mount': 'read-only',
            'cpu_limit': '1',
            'memory_limit': '1 GiB',
            'memory_swap_limit': '1 GiB',
            'pids_limit': '64',
            'capabilities': 'all dropped',
            'no_new_privileges': True,
        },
        'source_sha256': {name: sha256(ROOT / name) for name in SOURCE_PATHS},
        'suites': results,
        'tests_run_total': sum(row['tests_run'] for row in results.values()),
    }
    (OUT / 'RESULT.json').write_text(
        json.dumps(report, sort_keys=True, indent=2) + '\n', encoding='utf-8')
    raise SystemExit(0 if all_ok else 1)


if __name__ == '__main__':
    main()
