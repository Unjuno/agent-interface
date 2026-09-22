"""One foreground six-case batch, below the external tool execution ceiling."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('out');p.add_argument('batch',type=int);p.add_argument('--construction',action='store_true');a=p.parse_args()
    root=Path(a.out).resolve();root.mkdir(parents=True,exist_ok=True)
    marker=root/f'CONSUMED-{a.batch:02d}'
    with marker.open('x') as f:f.write('one invocation only\n')
    argv=[sys.executable,'-B',str(Path(__file__).with_name('runner.py')),str(root),str(a.batch)]
    if a.construction:argv.append('--construction')
    start=time.monotonic_ns();proc=subprocess.Popen(argv,stdout=subprocess.PIPE,stderr=subprocess.PIPE,start_new_session=True)
    timeout=False
    try:out,err=proc.communicate(timeout=30)
    except subprocess.TimeoutExpired:
        timeout=True;os.killpg(proc.pid,signal.SIGKILL);out,err=proc.communicate(timeout=2)
    (root/f'OUTER-{a.batch:02d}.stdout').write_bytes(out);(root/f'OUTER-{a.batch:02d}.stderr').write_bytes(err)
    ep=root/f'batch-{a.batch:02d}'/'EXECUTION.json'
    result={'argv':argv,'pid':proc.pid,'returncode':proc.returncode,'timeout':timeout,
            'started_ns':start,'finished_ns':time.monotonic_ns(),
            'stdout_sha256':hashlib.sha256(out).hexdigest(),'stderr_sha256':hashlib.sha256(err).hexdigest(),
            'execution_sha256':hashlib.sha256(ep.read_bytes()).hexdigest() if ep.exists() else None}
    (root/f'OUTER-{a.batch:02d}.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
    print(json.dumps(result)); print(out.decode(),end='');print(err.decode(),end='',file=sys.stderr)
    raise SystemExit(0 if proc.returncode==0 and not timeout else 1)
