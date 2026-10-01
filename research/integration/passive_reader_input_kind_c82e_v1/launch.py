"""One-shot source gate. Never overwrite or rerun a consumed allocation."""
import hashlib
import json
import os
from pathlib import Path
import sys
import time

root = Path(__file__).resolve().parent
freeze = json.loads((root / 'FREEZE.json').read_text())
actual = {name: hashlib.sha256((root / name).read_bytes()).hexdigest() for name in freeze['files']}
if actual != freeze['files']:
    raise SystemExit('STOP_SOURCE_MISMATCH')
if (root / 'formal-01').exists():
    raise SystemExit('STOP_OUTPUT_ALREADY_EXISTS')
command = [sys.executable, '-B', str(root / 'experiment.py'), 'run', str(root / 'formal-01'), 'formal']
with (root / 'FORMAL_INVOCATION.json').open('x') as destination:
    json.dump({'allocation': freeze['allocation'], 'source_gate': 'PASS', 'files': actual,
               'monotonic_ns': time.monotonic_ns(), 'command': command}, destination, sort_keys=True)
    destination.write('\n')
    destination.flush()
    os.fsync(destination.fileno())
os.execv(sys.executable, command)
