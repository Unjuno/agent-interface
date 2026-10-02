"""Retain actual child return and streams; never retry a named batch."""
import json
import subprocess
import sys
import time
from pathlib import Path
root=Path(__file__).resolve().parent.parent
phase,batch=sys.argv[1],sys.argv[2]
receipt=root/phase/('launch-'+batch+'.json')
receipt.parent.mkdir(parents=True,exist_ok=True)
with receipt.open('x') as f: f.write('{"status":"STARTED"}\n')
argv=[sys.executable,'-B',str(root/'source/run.py'),phase,batch]
p=subprocess.Popen(argv,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
t0=time.monotonic_ns()
try:
    stdout,stderr=p.communicate(timeout=25)
    timed_out=False
except subprocess.TimeoutExpired:
    p.terminate(); stdout,stderr=p.communicate(timeout=5); timed_out=True
receipt.write_text(json.dumps({'argv':argv,'pid':p.pid,'started_ns':t0,'ended_ns':time.monotonic_ns(),
 'returncode':p.returncode,'timed_out':timed_out,'stdout':stdout,'stderr':stderr},sort_keys=True,indent=2)+'\n')
print(json.dumps({'batch':batch,'exit':p.returncode,'timed_out':timed_out}))
raise SystemExit(p.returncode or timed_out)
