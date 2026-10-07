#!/usr/bin/env python3
"""Run one frozen focused fake-X suite and retain machine-readable raw output."""
import contextlib
import hashlib
import importlib.metadata
import json
import platform
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
import unittest

ROOT = Path('/workspace')
OUT = Path('/out')
PACKAGE = ROOT / 'research/doom/issue_59_sync_ack_loss_linux_a03_20261007'
SOURCE_PATHS = (
    'research/live_control/input_owner_v12.py',
    'research/live_control/key_edge_measurement_v1.py',
    'research/doom/doom_owner_thread_release_batch_backend_v1.py',
    'research/live_control/test_batch_key_measurement_composition.py',
)
EXPECTED_COMMIT = 'ca8f4113510b4b01a8e7d001dfe812dcc7b640a9'
BASE_IMAGE = ('python@sha256:'
              'dddfd7e07f9d15aeeca61529320492139d21cac7f0070c00609243e51e4e0016')


def sha256(path):
    digest = hashlib.sha256()
    with path.open('rb') as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b''):
            digest.update(chunk)
    return digest.hexdigest()


def flatten(suite):
    for item in suite:
        if isinstance(item, unittest.TestSuite):
            yield from flatten(item)
        else:
            yield item


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    source_hashes = {name: sha256(ROOT / name) for name in SOURCE_PATHS}
    deps = {name: importlib.metadata.version(name) for name in
            ('et-xmlfile', 'numpy', 'openpyxl', 'Pillow', 'python-xlib', 'six')}
    raw = {
        'schema': 'issue-59-sync-ack-loss-linux-a03-v1',
        'candidate_source_commit': EXPECTED_COMMIT,
        'base_image': BASE_IMAGE,
        'python': sys.version,
        'platform': platform.platform(),
        'dependencies': deps,
        'source_sha256': source_hashes,
        'started_utc': datetime.now(timezone.utc).isoformat(),
        'started_monotonic_ns': time.monotonic_ns(),
        'test_ids': [],
        'tests_run': 0,
        'failures': [],
        'errors': [],
        'status': 'STOP_RUNNER',
        'exit_code': 2,
        'cgroup_limits': {
            name: (Path('/sys/fs/cgroup') / name).read_text(encoding='utf-8').strip()
            if (Path('/sys/fs/cgroup') / name).is_file() else None
            for name in ('cpu.max', 'memory.max', 'pids.max')
        },
    }

    sys.path.insert(0, str(ROOT))
    sys.path.insert(0, str(ROOT / 'research/live_control'))
    sys.path.append(str(ROOT / 'research/doom'))
    vd = type(sys)('vizdoom')
    vd.__version__ = 'not-used-test-import-stub'
    vd.scenarios_path = '/tmp'
    sys.modules['vizdoom'] = vd

    try:
        suite = unittest.defaultTestLoader.loadTestsFromName(
            'test_batch_key_measurement_composition')
        raw['test_ids'] = [test.id() for test in flatten(suite)]
        with (OUT / 'TEST_EVENTS.jsonl').open('w', encoding='utf-8') as trace:
            with contextlib.redirect_stdout(trace):
                runner = unittest.TextTestRunner(stream=sys.stderr, verbosity=2)
                result = runner.run(suite)
        raw['tests_run'] = result.testsRun
        raw['failures'] = [
            {'test': test.id(), 'traceback': traceback}
            for test, traceback in result.failures]
        raw['errors'] = [
            {'test': test.id(), 'traceback': traceback}
            for test, traceback in result.errors]
        raw['status'] = 'PASS_TESTS' if result.wasSuccessful() else 'FAIL_TESTS'
        raw['exit_code'] = 0 if result.wasSuccessful() else 1
    except BaseException as exc:
        raw['runner_error'] = {'type': type(exc).__name__, 'message': str(exc)[:500]}
    raw['ended_utc'] = datetime.now(timezone.utc).isoformat()
    raw['ended_monotonic_ns'] = time.monotonic_ns()
    raw['events_sha256'] = (sha256(OUT / 'TEST_EVENTS.jsonl')
                            if (OUT / 'TEST_EVENTS.jsonl').exists() else None)
    (OUT / 'TEST_RAW.json').write_text(
        json.dumps(raw, sort_keys=True, indent=2) + '\n', encoding='utf-8')
    sys.exit(raw['exit_code'])


if __name__ == '__main__':
    main()
