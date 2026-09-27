import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import time

src = Path('/src')
work = Path('/work')
expected = json.loads((src / 'FREEZE.json').read_text())['source_sha256']
for name, digest in expected.items():
    actual = hashlib.sha256((src / name).read_bytes()).hexdigest()
    if actual != digest:
        raise SystemExit(f'source hash mismatch: {name}')
for name in ('runner.py', 'model.py'):
    shutil.copy2(src / name, work / name)
    actual = hashlib.sha256((work / name).read_bytes()).hexdigest()
    if actual != expected[name]:
        raise SystemExit(f'execution copy mismatch: {name}')
ap = argparse.ArgumentParser()
ap.add_argument('--check-only', action='store_true')
args = ap.parse_args()
formal_out = work / 'formal-01'
if formal_out.exists():
    raise SystemExit('formal output path already exists')
if args.check_only:
    receipt = {
        'check_only': True,
        'verified_frozen_files': len(expected),
        'runner_sha256': expected['runner.py'],
        'model_sha256': expected['model.py'],
        'formal_output_absent': True,
    }
    (work / 'LAUNCH_PREFLIGHT.json').write_text(json.dumps(receipt, indent=2, sort_keys=True) + '\n')
    print(json.dumps(receipt, sort_keys=True))
    raise SystemExit(0)
stdout_path = work / 'runner.stdout.txt'
stderr_path = work / 'runner.stderr.txt'
argv = ['python3', 'runner.py', '--out', 'formal-01', '--formal']
started = time.monotonic_ns()
with stdout_path.open('w', encoding='utf-8') as out, stderr_path.open('w', encoding='utf-8') as err:
    child = subprocess.Popen(argv, cwd=work, stdin=subprocess.DEVNULL, stdout=out, stderr=err, close_fds=True)
    pid = child.pid
    returncode = child.wait()
finished = time.monotonic_ns()
raw = formal_out / 'RAW.json'
receipt = {
    'allocation': 'runtime-assurance-fallback-4261-20260923-01',
    'formal_invocations': 1,
    'argv': argv,
    'cwd': str(work),
    'source_commit': '95e46a2d9362502d1a24917cbb735ea354acb5ce',
    'runner_sha256': expected['runner.py'],
    'model_sha256': expected['model.py'],
    'pid': pid,
    'returncode': returncode,
    'started_monotonic_ns': started,
    'finished_monotonic_ns': finished,
    'raw_exists': raw.is_file(),
    'raw_sha256': hashlib.sha256(raw.read_bytes()).hexdigest() if raw.is_file() else None,
}
(formal_out / 'EXECUTION.json').write_text(json.dumps(receipt, indent=2, sort_keys=True) + '\n', encoding='utf-8')
shutil.copy2(stdout_path, formal_out / 'runner.stdout.txt')
shutil.copy2(stderr_path, formal_out / 'runner.stderr.txt')
print(json.dumps(receipt, sort_keys=True))
raise SystemExit(returncode)
