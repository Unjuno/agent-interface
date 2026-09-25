"""Capture one actual invocation and its exit. Refuse existing output paths."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parent
out = ROOT/sys.argv[1]
out.mkdir(exist_ok=False)
command = [sys.executable, '-S', '-B', str(ROOT/'run.py')]
start = time.time_ns()
with (out/'records.json').open('wb') as stdout, (out/'stderr.txt').open('wb') as stderr:
    process = subprocess.Popen(command, cwd=ROOT, stdout=stdout, stderr=stderr)
    timeout = False
    try:
        code = process.wait(timeout=35)
    except subprocess.TimeoutExpired:
        timeout = True
        process.kill()
        code = process.wait()
receipt = {'argv': command, 'pid': process.pid, 'start_utc_ns': start,
           'end_utc_ns': time.time_ns(), 'returncode': code, 'timeout': timeout,
           'stdout_sha256': hashlib.sha256((out/'records.json').read_bytes()).hexdigest(),
           'stderr_bytes': (out/'stderr.txt').stat().st_size}
(out/'PROCESS.json').write_text(json.dumps(receipt, sort_keys=True, indent=2)+'\n')
print(json.dumps(receipt, sort_keys=True))
raise SystemExit(0 if code == 0 and not timeout else 1)
