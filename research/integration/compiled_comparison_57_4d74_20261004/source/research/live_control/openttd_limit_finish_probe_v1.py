"""Exercise the v5 driver's bounded-limit finish handshake without model or pointer input."""
import hashlib
import json
import os
import subprocess
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
STUDY = 'timing-envelope-openttd-l-limit-01'
BASE = HERE / 'results' / STUDY
ROOT = BASE / 'fixed-astra'
CONTROL = BASE / 'probe-control'
CONTROL.mkdir(parents=True, exist_ok=False)
SOURCES = ['openttd_limit_finish_probe_v1.py', 'timing_envelope_openttd_l_driver_v5.py',
           'openttd_finish_outcome_v1.py', 'durable_submit_v4.py', 'append_checkpoint_v1.py']


def dump(path, value):
    temporary = path.with_suffix(path.suffix + '.tmp')
    temporary.write_text(json.dumps(value, indent=2) + '\n', encoding='utf-8')
    os.replace(temporary, path)


def read(path):
    return json.loads(path.read_text(encoding='utf-8'))


def linux(path):
    path = path.resolve()
    return '/mnt/' + path.drive[0].lower() + path.as_posix()[2:]


def wait_file(path, process, seconds=120):
    deadline = time.monotonic() + seconds
    while not path.exists():
        if process.poll() is not None:
            raise RuntimeError('driver exited before ' + path.name)
        if time.monotonic() > deadline:
            raise TimeoutError(path.name)
        time.sleep(.025)
    return read(path)


dump(CONTROL / 'plan.json', {
    'status': 'FROZEN_BEFORE_EXECUTION',
    'scope': 'twelve observe-only proposals followed by supervisor abort; require independent bounded_turn_limit outcome',
    'model_calls': 0,
    'pointer_steps': 0,
    'sources': {name: hashlib.sha256((HERE / name).read_bytes()).hexdigest() for name in SOURCES},
})
started = time.perf_counter_ns()
driver = subprocess.Popen(
    ['wsl', '-d', 'Ubuntu', '--', 'python3', linux(HERE / 'timing_envelope_openttd_l_driver_v5.py'),
     'fixed-astra', STUDY],
    stdout=(CONTROL / 'driver-stdout.txt').open('wb'),
    stderr=(CONTROL / 'driver-stderr.txt').open('wb'))
try:
    ready = wait_file(ROOT / 'ready.json', driver)
    for turn in range(1, 13):
        dump(ROOT / f'proposal-{turn}.json', {
            'steps': [{'op': 'observe'}],
            'rationale': 'model-free bounded-limit handshake probe',
            'typed_kind': 'probe',
        })
        wait_file(ROOT / f'applied-{turn}.json', driver, 30)
    dump(ROOT / 'abort.json', {'finish': True, 'reason': 'bounded turn limit; independent failure score required'})
    failure = wait_file(ROOT / 'failure-evaluation.json', driver, 30)
    code = driver.wait(timeout=10)
    calls = read(ROOT / 'calls.json')
    assert code == 0
    assert failure['success'] is False and failure['failure_mode'] == 'bounded_turn_limit'
    assert failure['proposals_executed'] == 12 and failure['journal_calls'] == 50
    assert failure['evaluation']['success'] is False
    assert failure['evaluation']['changed_surrounding_tiles'] == []
    assert len(calls) == 50 and not (ROOT / 'result.json').exists()
    dump(CONTROL / 'result.json', {
        'success': True,
        'driver_exit_code': code,
        'model_calls': 0,
        'pointer_steps': 0,
        'observe_only_proposals': 12,
        'durable_calls': len(calls),
        'failure_outcome': failure,
        'supervisor_wall_ms': (time.perf_counter_ns() - started) / 1e6,
        'task': ready['task'],
    })
    print('openttd_limit_finish_probe_v1: PASS')
finally:
    if driver.poll() is None:
        driver.terminate()
        driver.wait(timeout=10)
