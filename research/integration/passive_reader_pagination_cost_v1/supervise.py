"""Wait for exactly one bounded batch and retain actual Popen exit, never infer it."""
import argparse
import hashlib
import json
import os
import signal
from pathlib import Path
import subprocess
import sys
import time
ROOT=Path(__file__).resolve().parent
p=argparse.ArgumentParser()
p.add_argument('out',type=Path)
p.add_argument('index',type=int,choices=range(4))
a=p.parse_args()
folder=a.out/f'batch-{a.index}'
if folder.exists():
    raise SystemExit('CONSUMED_BATCH')
command=[sys.executable,'-B',str(ROOT/'batch.py'),str(a.out),str(a.index)]
started=time.perf_counter_ns()
child=subprocess.Popen(command,stdout=subprocess.PIPE,stderr=subprocess.PIPE,start_new_session=True)
timeout=False
try:
    stdout,stderr=child.communicate(timeout=20)
except subprocess.TimeoutExpired:
    timeout=True
    os.killpg(child.pid,signal.SIGKILL)
    stdout,stderr=child.communicate()
folder=a.out/f'batch-{a.index}'
folder.mkdir(parents=True,exist_ok=True)
(folder/'batch.stdout').write_bytes(stdout)
(folder/'batch.stderr').write_bytes(stderr)
receipt={'index':a.index,'command':command,'pid':child.pid,'exit_code':child.returncode,'timeout':timeout,
         'wall_start_ns':started,'wall_end_ns':time.perf_counter_ns(),
         'stdout_sha256':hashlib.sha256(stdout).hexdigest(),'stderr_sha256':hashlib.sha256(stderr).hexdigest(),
         'batch_sha256':hashlib.sha256((folder/'BATCH.json').read_bytes()).hexdigest() if (folder/'BATCH.json').exists() else None}
(folder/'SUPERVISOR.json').write_text(json.dumps(receipt,sort_keys=True,separators=(',',':'))+'\n')
print(json.dumps(receipt),flush=True)
raise SystemExit(0 if child.returncode==0 and not timeout else 2)
