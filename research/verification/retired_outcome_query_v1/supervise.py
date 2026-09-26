"""Foreground bounded wrapper; retain the actual runner wait status."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parent
p = argparse.ArgumentParser()
p.add_argument('--batch',type=int,choices=range(3),required=True)
p.add_argument('--construction',action='store_true')
p.add_argument('--parent',type=Path,required=True)
a = p.parse_args()
a.parent = a.parent.resolve()
a.parent.mkdir(parents=True,exist_ok=True)
out = a.parent/f'batch-{a.batch}'
marker = a.parent/f'launch-{a.batch}.json'
with marker.open('x') as m:
    json.dump({'supervisor_pid':os.getpid(),'batch':a.batch,'out':str(out)},m)
argv = [sys.executable,'-B',str(ROOT/'run.py'),'--batch',str(a.batch),'--out',str(out)]
if a.construction:
    argv.append('--construction')
start = time.monotonic_ns()
child = subprocess.Popen(argv,stdout=subprocess.PIPE,stderr=subprocess.PIPE,start_new_session=True)
timed_out = False
try:
    stdout,stderr = child.communicate(timeout=35)
except subprocess.TimeoutExpired:
    import signal
    timed_out = True
    os.killpg(child.pid,signal.SIGKILL)
    stdout,stderr = child.communicate(timeout=3)
raw = out/'RAW.jsonl'
receipt = {'argv':argv,'pid':child.pid,'returncode':child.returncode,'timeout':timed_out,
           'start_ns':start,'end_ns':time.monotonic_ns(),'stdout':stdout.decode(),
           'stderr':stderr.decode(),'raw_sha256':hashlib.sha256(raw.read_bytes()).hexdigest() if raw.exists() else None}
(out if out.exists() else a.parent).joinpath('EXECUTION.json').write_text(json.dumps(receipt,sort_keys=True)+'\n')
print(json.dumps(receipt,sort_keys=True))
sys.exit(0 if child.returncode == 0 and not timed_out else 1)
