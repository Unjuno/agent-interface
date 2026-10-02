"""Retain actual child return codes; do not retry a consumed output directory."""
import json
import os
import signal
from pathlib import Path
import subprocess
import sys
import time

root = Path(__file__).resolve().parent
kind, batch, dest = sys.argv[1:]
dest = Path(dest)
receipt = dest.with_suffix('.execution.json')
if dest.exists() or receipt.exists():
    raise SystemExit('destination already consumed')
dest.parent.mkdir(parents=True,exist_ok=True)
argv = [sys.executable,'-I','-S','-B',str(root/'run.py'),kind,batch,str(dest)]
start = time.monotonic_ns()
with dest.with_suffix('.stdout').open('xb') as out, dest.with_suffix('.stderr').open('xb') as err:
    child = subprocess.Popen(argv,stdout=out,stderr=err,start_new_session=True)
    timed_out = False
    try:
        code = child.wait(timeout=25)
    except subprocess.TimeoutExpired:
        timed_out = True
        os.killpg(child.pid, signal.SIGKILL)
        code = child.wait()
result = {'argv':argv,'pid':child.pid,'exit':code,'timeout':timed_out,'start_ns':start,'end_ns':time.monotonic_ns()}
receipt.write_text(json.dumps(result,sort_keys=True)+'\n')
print(json.dumps(result,sort_keys=True))
raise SystemExit(0 if code==0 and not timed_out else 1)
