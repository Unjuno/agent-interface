"""Exclusive output allocation and externally observed batch exit."""
import json
from pathlib import Path
import subprocess
import sys
import time

root = Path(__file__).resolve().parent
phase, index = sys.argv[1], int(sys.argv[2])
if phase not in ('construction', 'construction_v1', 'formal') or index not in range(6):
    raise ValueError('allocation')
if phase == 'formal' and index:
    prior = json.loads((root / phase / str(index - 1) / 'EXIT.json').read_text())
    if prior['returncode'] != 0 or prior['timeout']:
        raise RuntimeError('previous batch incomplete')
path = root / phase / str(index)
path.mkdir(parents=True, exist_ok=False)
argv = [sys.executable, '-B', str(root / 'run.py'), str(path), str(index), phase]
(path / 'START.json').write_text(json.dumps({'argv': argv}, sort_keys=True) + '\n')
start = time.monotonic_ns()
with (path / 'stdout.txt').open('xb') as out, (path / 'stderr.txt').open('xb') as err:
    p = subprocess.Popen(argv, stdout=out, stderr=err)
    timed_out = False
    try:
        code = p.wait(timeout=30)
    except subprocess.TimeoutExpired:
        timed_out = True
        p.kill()
        code = p.wait()
receipt = {'argv': argv, 'pid': p.pid, 'returncode': code, 'timeout': timed_out,
           'start_ns': start, 'end_ns': time.monotonic_ns()}
(path / 'EXIT.json').write_text(json.dumps(receipt, sort_keys=True) + '\n')
print(json.dumps(receipt, sort_keys=True))
sys.exit(1 if timed_out or code else 0)
