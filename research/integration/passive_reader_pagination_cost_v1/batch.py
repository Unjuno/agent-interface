"""Execute one immutable batch; no replacement, implicit retry or background work."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time
ROOT = Path(__file__).resolve().parent

def digest(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()

def dump(p, value):
    p.write_text(json.dumps(value, sort_keys=True, separators=(',', ':'))+'\n')

def main():
    p = argparse.ArgumentParser()
    p.add_argument('out', type=Path)
    p.add_argument('index', type=int, choices=range(4))
    a = p.parse_args()
    freeze = json.loads((ROOT/'FREEZE.json').read_text())
    for rel, value in freeze['sha256'].items():
        if digest(ROOT/rel) != value:
            raise RuntimeError('SOURCE_FREEZE_MISMATCH:'+rel)
    if a.index:
        prev = a.out/f'batch-{a.index-1}'/'SUPERVISOR.json'
        x = json.loads(prev.read_text())
        if x['exit_code'] != 0 or x['index'] != a.index-1:
            raise RuntimeError('PREVIOUS_BATCH_INCOMPLETE')
        prior_sha = digest(prev)
    else:
        a.out.mkdir(parents=True, exist_ok=False)
        prior_sha = None
    dest = a.out/f'batch-{a.index}'
    dest.mkdir(exist_ok=False)
    n = [128,256,512,1024][a.index]
    planned = []
    for rep in range(3):
        pages = [1,8,32]
        pages = pages[rep:] + pages[:rep]
        for page in pages:
            planned.append([f'n{n}-p{page}-r{rep}', '--n',str(n),'--page',str(page),'--rep',str(rep)])
    if a.index == 3:
        planned.append(['capacity','--capacity'])
    receipts = []
    for row in planned:
        command = [sys.executable,'-B',str(ROOT/'study.py'),str(dest/row[0]),*row[1:]]
        started = time.perf_counter_ns()
        child = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                 env=dict(os.environ,PYTHONHASHSEED='0',PYTHONDONTWRITEBYTECODE='1'))
        timeout = False
        try:
            stdout, stderr = child.communicate(timeout=10)
        except subprocess.TimeoutExpired:
            timeout = True
            child.kill()
            stdout,stderr = child.communicate()
        (dest/(row[0]+'.stdout')).write_bytes(stdout)
        (dest/(row[0]+'.stderr')).write_bytes(stderr)
        receipt = {'name':row[0],'command':command,'pid':child.pid,'exit_code':child.returncode,
                   'timeout':timeout,'wall_start_ns':started,'wall_end_ns':time.perf_counter_ns(),
                   'stdout_sha256':hashlib.sha256(stdout).hexdigest(),
                   'stderr_sha256':hashlib.sha256(stderr).hexdigest()}
        receipts.append(receipt)
        dump(dest/'PROCESSES.json',receipts)
        if timeout or child.returncode != 0:
            raise RuntimeError('STOP_WORKER:'+row[0])
    result={'index':a.index,'n':n,'pid':os.getpid(),'previous_supervisor_sha256':prior_sha,
            'processes':len(receipts),'process_receipts_sha256':digest(dest/'PROCESSES.json'),
            'freeze_sha256':digest(ROOT/'FREEZE.json'),'status':'completed'}
    dump(dest/'BATCH.json',result)
    print(json.dumps(result),flush=True)

if __name__=='__main__':
    main()
