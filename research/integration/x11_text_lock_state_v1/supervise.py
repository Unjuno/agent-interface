"""Collect actual direct-child exit within one bounded synchronous invocation."""
import argparse
import hashlib
import json
import os
import signal
from pathlib import Path
import subprocess
import sys
import time

ap = argparse.ArgumentParser()
ap.add_argument('batch', type=int, choices=range(4))
a = ap.parse_args()
root = Path(__file__).resolve().parent
out = root / 'formal'
out.mkdir(exist_ok=True)
marker = out / f'batch-{a.batch}.consumed'
marker.open('x').close()
argv = [sys.executable, '-B', str(root/'run.py'), '--batch', str(a.batch), '--out', str(out/f'batch-{a.batch}')]
start = time.monotonic_ns()
with (out/f'batch-{a.batch}.stdout').open('xb') as so, (out/f'batch-{a.batch}.stderr').open('xb') as se:
    p = subprocess.Popen(argv, stdout=so, stderr=se, start_new_session=True)
    timed_out = False
    try:
        code = p.wait(timeout=15)
    except subprocess.TimeoutExpired:
        timed_out = True
        os.killpg(p.pid, signal.SIGTERM)
        try:
            code = p.wait(timeout=2)
        except subprocess.TimeoutExpired:
            os.killpg(p.pid, signal.SIGKILL)
            code = p.wait(timeout=1)
raw = out/f'batch-{a.batch}'/'raw.json'
r = {'argv':argv,'pid':p.pid,'returncode':code,'timed_out':timed_out,
     'started_ns':start,'ended_ns':time.monotonic_ns(),
     'raw_sha256':hashlib.sha256(raw.read_bytes()).hexdigest() if raw.exists() else None}
with (out/f'batch-{a.batch}.exit.json').open('x') as f:
    json.dump(r,f,sort_keys=True,indent=2);f.write('\n')
print(json.dumps(r,sort_keys=True))
raise SystemExit(0 if code==0 and not timed_out else 2)
