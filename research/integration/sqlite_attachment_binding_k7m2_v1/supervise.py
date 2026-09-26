"""Record the real foreground batch exit. No background job or automatic retry."""
import json
from pathlib import Path
import subprocess
import sys
import time

root = Path(__file__).resolve().parent
out = Path(sys.argv[1]).resolve()
index = int(sys.argv[2])
if index not in range(4):
    raise ValueError('INVALID_BATCH')
out.mkdir(exist_ok=True)
record = out / ('EXIT-%d.json' % index)
if record.exists() or (out / ('batch-%d' % index)).exists():
    raise ValueError('CONSUMED_BATCH')
command = [sys.executable, '-B', str(root / 'study.py'), str(out), str(index)]
start = time.monotonic_ns()
try:
    child = subprocess.run(command, capture_output=True, timeout=25)
    result = {'command': command, 'returncode': child.returncode,
              'stdout': child.stdout.decode(), 'stderr': child.stderr.decode(),
              'start_ns': start, 'end_ns': time.monotonic_ns()}
except subprocess.TimeoutExpired as error:
    result = {'command': command, 'returncode': None, 'stop': 'BATCH_TIMEOUT',
              'stdout': (error.stdout or b'').decode(), 'stderr': (error.stderr or b'').decode(),
              'start_ns': start, 'end_ns': time.monotonic_ns()}
record.write_text(json.dumps(result, indent=2, sort_keys=True) + '\n')
print(json.dumps(result))
raise SystemExit(0 if result['returncode'] == 0 else 1)
