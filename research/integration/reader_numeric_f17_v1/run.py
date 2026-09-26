"""One retained, bounded CLI comparison. Never dispatches input or retries."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parent

def digest(data):
    return hashlib.sha256(data).hexdigest()

def source_check():
    freeze = json.loads((ROOT / 'FREEZE.json').read_text())
    for name, expected in freeze['files'].items():
        if digest((ROOT / name).read_bytes()) != expected:
            raise RuntimeError('SOURCE_MISMATCH:' + name)
    return digest((ROOT / 'FREEZE.json').read_bytes())

def execute(out):
    frozen = source_check()
    out.mkdir(exist_ok=False)
    cases = json.loads((ROOT / 'CASES.json').read_text())
    records = []
    started = time.monotonic_ns()
    try:
        for case in cases:
            directory = out / case['name']
            directory.mkdir()
            data = (case['prefix'] + case['subject'] + case['suffix']).encode()
            stream = directory / 'stream.jsonl'
            stream.write_bytes(data)
            order = ['upstream', 'candidate'] if len(records) % 12 == 0 else ['candidate', 'upstream']
            for policy in order:
                cursor_file = directory / (policy + '-cursor.json')
                for phase, limit in [('full', 32), ('first', 1), ('next', 32)]:
                    before = cursor_file.read_text() if phase == 'next' else None
                    command = [sys.executable, '-S', '-B', '-m', policy,
                               '--stream', str(stream.resolve()), '--stream-id', 'f17',
                               '--max-records', str(limit)]
                    if before is not None:
                        command += ['--cursor', str(cursor_file.resolve())]
                    t0 = time.monotonic_ns()
                    child = subprocess.Popen(command, cwd=ROOT, stdout=subprocess.PIPE,
                                             stderr=subprocess.PIPE, stdin=subprocess.DEVNULL)
                    timed_out = False
                    try:
                        stdout, stderr = child.communicate(timeout=5)
                    except subprocess.TimeoutExpired:
                        timed_out = True
                        child.kill()
                        stdout, stderr = child.communicate()
                    row = {'case': case['name'], 'policy': policy, 'phase': phase,
                           'argv': command, 'cwd': str(ROOT), 'pid': child.pid,
                           'start_ns': t0, 'end_ns': time.monotonic_ns(),
                           'returncode': child.returncode, 'timeout': timed_out,
                           'stdout': stdout.decode(), 'stderr': stderr.decode(),
                           'input_sha256': digest(data), 'input_after_sha256': digest(stream.read_bytes()),
                           'cursor_before': before,
                           'cursor_after': cursor_file.read_text() if before is not None else None}
                    records.append(row)
                    with (out / 'RECORDS.jsonl').open('a') as journal:
                        journal.write(json.dumps(row, sort_keys=True, allow_nan=False) + '\n')
                    if timed_out:
                        raise RuntimeError('CHILD_TIMEOUT')
                    if phase == 'first':
                        if child.returncode != 0:
                            raise RuntimeError('FIRST_PAGE_FAILED')
                        cursor_file.write_text(json.dumps(json.loads(stdout)['next_cursor']) + '\n')
        source_check()
        terminal = {'status': 'COMPLETE', 'records': len(records), 'freeze_sha256': frozen,
                    'start_ns': started, 'end_ns': time.monotonic_ns(), 'pid': os.getpid()}
    except Exception as error:
        terminal = {'status': 'STOP', 'error': repr(error), 'records': len(records),
                    'freeze_sha256': frozen, 'start_ns': started,
                    'end_ns': time.monotonic_ns(), 'pid': os.getpid()}
        (out / 'TERMINAL.json').write_text(json.dumps(terminal, sort_keys=True) + '\n')
        raise
    (out / 'TERMINAL.json').write_text(json.dumps(terminal, sort_keys=True) + '\n')
    print(json.dumps(terminal, sort_keys=True))

if __name__ == '__main__':
    if len(sys.argv) != 2:
        raise SystemExit('usage: run.py ABSENT_OUTPUT_DIRECTORY')
    execute(Path(sys.argv[1]).resolve())
