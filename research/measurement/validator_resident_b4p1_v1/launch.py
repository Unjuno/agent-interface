"""Finite supervisor, preserving stdout/stderr/exit and no rerun."""
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time
ROOT=Path(__file__).resolve().parent
out=Path(sys.argv[2]).resolve()
if out.exists():raise FileExistsError(out)
cmd=[sys.executable,'-I','-S','-B',str(ROOT/'run_batch.py'),'--count',sys.argv[1],'--out',str(out)]
begin=time.time_ns()
p=subprocess.Popen(cmd,stdout=subprocess.PIPE,stderr=subprocess.PIPE,start_new_session=True)
timeout=False
try:
    stdout,stderr=p.communicate(timeout=35)
except subprocess.TimeoutExpired:
    timeout=True
    os.killpg(p.pid,signal.SIGKILL)
    stdout,stderr=p.communicate(timeout=5)
out.mkdir(parents=True,exist_ok=True)
receipt=dict(argv=cmd,pid=p.pid,exit=p.returncode,timeout=timeout,stdout=stdout.decode('utf-8','replace'),stderr=stderr.decode('utf-8','replace'),started_unix_ns=begin,ended_unix_ns=time.time_ns())
(out/'LAUNCHER.json').write_text(json.dumps(receipt,sort_keys=True,indent=2)+'\n')
print(json.dumps(receipt,sort_keys=True))
raise SystemExit(int(timeout or p.returncode!=0))
