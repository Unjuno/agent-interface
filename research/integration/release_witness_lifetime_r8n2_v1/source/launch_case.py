"""Serial formal case launcher retaining the real subprocess exit and output."""
import argparse
import hashlib
import json
import subprocess
import sys
import time
from pathlib import Path

root = Path(__file__).resolve().parent.parent
p = argparse.ArgumentParser()
p.add_argument('index', type=int, choices=range(16))
a = p.parse_args()
freeze = json.loads((root / 'FREEZE.json').read_text())
for rel, expected in freeze['sha256'].items():
    if hashlib.sha256((root / rel).read_bytes()).hexdigest() != expected:
        raise SystemExit('frozen source mismatch: ' + rel)
receipt = root / 'evidence' / ('launch-%02d.json' % a.index)
if a.index:
    prior = json.loads((receipt.parent / ('launch-%02d.json' % (a.index - 1))).read_text())
    if prior.get('returncode') != 0:
        raise SystemExit('preceding case not successfully terminated; stop')
command = [sys.executable, '-B', str(root / 'source/run_case.py'), str(a.index),
           str(root / 'evidence' / ('case-%02d' % a.index)), '--formal']
record = dict(index=a.index, command=command, started_ns=time.monotonic_ns(), returncode=None)
with receipt.open('x') as f:
    json.dump(record, f, sort_keys=True)
try:
    done = subprocess.run(command, capture_output=True, text=True, timeout=30)
    record.update(returncode=done.returncode, stdout=done.stdout, stderr=done.stderr)
except subprocess.TimeoutExpired:
    record.update(error='STOP_CASE_TIMEOUT', stdout=None, stderr=None)
finally:
    record['ended_ns'] = time.monotonic_ns()
    receipt.write_text(json.dumps(record, sort_keys=True, indent=2) + '\n')
print(json.dumps(record, sort_keys=True))
raise SystemExit(0 if record.get('returncode') == 0 else 2)
