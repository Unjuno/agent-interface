"""Bound and retain a local orchestration, including exact child exit receipts."""
import hashlib
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parent


def main():
    phase, name = sys.argv[1:]
    if phase not in ('construction', 'formal') or Path(name).name != name:
        raise ValueError('invalid allocation')
    out = ROOT / name
    receipt_path = ROOT / (name + '.DRIVER.json')
    start_path = ROOT / (name + '.START.json')
    command = [sys.executable, str(ROOT / 'run.py'), '--phase', phase, '--output', str(out)]
    with start_path.open('x') as file:
        json.dump({'command': command, 'started_ns': time.time_ns(), 'budget_s': 240}, file)
    record = {'command': command, 'budget_s': 240, 'timeout': False}
    child = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, start_new_session=True)
    record['pid'] = child.pid
    try:
        stdout, stderr = child.communicate(timeout=240)
    except subprocess.TimeoutExpired:
        record['timeout'] = True
        os.killpg(child.pid, signal.SIGKILL)
        stdout, stderr = child.communicate()
    record['returncode'] = child.returncode
    (ROOT / (name + '.stdout.txt')).write_bytes(stdout)
    (ROOT / (name + '.stderr.txt')).write_bytes(stderr)
    if child.returncode == 0 and not record['timeout']:
        raw = out / 'RAW.json'
        raw_sha = hashlib.sha256(raw.read_bytes()).hexdigest()
        audit_cmd = [sys.executable, str(ROOT / 'audit.py'), str(raw), '--expected-sha256', raw_sha]
        audit = subprocess.run(audit_cmd, capture_output=True, timeout=30)
        (ROOT / (name + '.AUDIT.json')).write_bytes(audit.stdout)
        (ROOT / (name + '.audit.stderr.txt')).write_bytes(audit.stderr)
        record['audit'] = {'command': audit_cmd, 'returncode': audit.returncode,
                           'raw_sha256': raw_sha, 'stdout_sha256': hashlib.sha256(audit.stdout).hexdigest()}
        if audit.returncode == 0:
            env = dict(os.environ, EPOCH_CONSTRUCTION_RAW=str(raw),
                       EPOCH_CONTROL_OUTPUT=str(ROOT / (name + '.MUTATIONS.json')))
            command = [sys.executable, str(ROOT / 'test_study.py')]
            tests = subprocess.run(command, capture_output=True, timeout=30, env=env)
            (ROOT / (name + '.tests.stdout.txt')).write_bytes(tests.stdout)
            (ROOT / (name + '.tests.stderr.txt')).write_bytes(tests.stderr)
            record['controls'] = {'command': command, 'returncode': tests.returncode,
                                  'stderr_sha256': hashlib.sha256(tests.stderr).hexdigest()}
    record['ended_ns'] = time.time_ns()
    with receipt_path.open('x') as file:
        json.dump(record, file, sort_keys=True, indent=2)
    print(json.dumps(record))


if __name__ == '__main__':
    main()
