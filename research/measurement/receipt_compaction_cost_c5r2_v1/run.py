"""Bound one worker and record its observed OS exit; never retry a condition."""
import json
from pathlib import Path
import subprocess
import sys
import time

root = Path(__file__).resolve().parent
index = int(sys.argv[1])
base = Path(sys.argv[2]).resolve()
base.mkdir(parents=True, exist_ok=True)
marker = base / ('consumed-' + str(index))
with marker.open('x') as f:
    f.write('one invocation\n')
argv = [sys.executable, '-S', '-B', str(root / 'worker.py'), str(index), str(base / ('case-' + str(index)))]
start = time.perf_counter_ns()
p = subprocess.Popen(argv, cwd=root, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
timed_out = False
try:
    stdout, stderr = p.communicate(timeout=20)
except subprocess.TimeoutExpired:
    timed_out = True
    p.kill()
    stdout, stderr = p.communicate()
record = {'index': index, 'argv': argv, 'pid': p.pid, 'exit': p.returncode,
          'timeout': timed_out, 'started_ns': start, 'ended_ns': time.perf_counter_ns(),
          'stdout': stdout.decode(), 'stderr': stderr.decode()}
(base / ('execution-' + str(index) + '.json')).write_text(json.dumps(record, indent=2) + '\n')
print(json.dumps(record))
raise SystemExit(0 if p.returncode == 0 and not timed_out else 1)
