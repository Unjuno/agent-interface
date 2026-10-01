"""Bounded launcher records actual exit; no automatic case retries."""
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time

root=Path(sys.argv[1]).resolve()
phase=sys.argv[2]
index=int(sys.argv[3])
receipt=root/phase/f'PROCESS-{index}.json'
receipt.parent.mkdir(parents=True,exist_ok=True)
with open(root/phase/f'CLAIM-{index}','x'):
    pass
args=[sys.executable,'-S','-B',str(root/'source/experiment.py'),str(root/phase/f'batch{index}'),phase,str(index)]
t0=time.monotonic_ns()
p=subprocess.Popen(args,stdout=subprocess.PIPE,stderr=subprocess.PIPE,start_new_session=True)
timeout=False
try:
    out,err=p.communicate(timeout=25)
except subprocess.TimeoutExpired:
    timeout=True
    os.killpg(p.pid,signal.SIGKILL)
    out,err=p.communicate()
r={'batch':index,'argv':args,'pid':p.pid,'returncode':p.returncode,'timeout':timeout,
   'start_ns':t0,'end_ns':time.monotonic_ns(),'stdout':out.decode(),'stderr':err.decode()}
receipt.write_text(json.dumps(r,sort_keys=True,indent=2)+'\n')
print(json.dumps(r,sort_keys=True))
raise SystemExit(0 if p.returncode==0 and not timeout else 1)
