"""One foreground batch with observed exit and bounded owned-group cleanup."""
import hashlib
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time

root=Path(sys.argv[1]).resolve();batch=int(sys.argv[2]);reps=int(sys.argv[3])
root.mkdir(parents=True,exist_ok=True)
with (root/f'consumed-{batch}.json').open('x') as f:
    json.dump({'batch':batch,'started_ns':time.monotonic_ns()},f)
if reps==2 and batch>0:
    prior=root/f'batch-{batch-1}'/'EXECUTION.json'
    receipt=json.loads(prior.read_text());raw=prior.with_name('RAW.json')
    if type(receipt['exit']) is not int or receipt['exit']!=0 or receipt['raw_sha256']!=hashlib.sha256(raw.read_bytes()).hexdigest():
        raise ValueError('PRIOR_BATCH_INCOMPLETE')
out=root/f'batch-{batch}'
cmd=[sys.executable,'-S','-B',str(Path(__file__).with_name('runner.py')),str(out),str(batch),str(reps)]
start=time.monotonic_ns();timed_out=False
p=subprocess.Popen(cmd,stdout=subprocess.PIPE,stderr=subprocess.PIPE,start_new_session=True)
try:
    stdout,stderr=p.communicate(timeout=25)
except subprocess.TimeoutExpired:
    timed_out=True;os.killpg(p.pid,signal.SIGKILL);stdout,stderr=p.communicate(timeout=3)
out.mkdir(exist_ok=True)
(out/'runner.stdout').write_bytes(stdout);(out/'runner.stderr').write_bytes(stderr)
raw=out/'RAW.json'
r={'argv':cmd,'pid':p.pid,'exit':p.returncode,'timed_out':timed_out,'start_ns':start,'end_ns':time.monotonic_ns(),
   'raw_sha256':hashlib.sha256(raw.read_bytes()).hexdigest() if raw.exists() else None}
(out/'EXECUTION.json').write_text(json.dumps(r,sort_keys=True,indent=2)+'\n')
print(json.dumps(r));raise SystemExit(p.returncode if p.returncode else int(timed_out))
