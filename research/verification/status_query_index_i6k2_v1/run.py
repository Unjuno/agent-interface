"""Finite supervisor. Existing batch destinations are never reused."""
import argparse
import base64
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time

ROOT=Path(__file__).resolve().parent
SIZES=(256,4096,32768)

def encode(x):return json.dumps(x,sort_keys=True,separators=(',',':')).encode()
def save(path,x):
    with path.open('xb') as f:f.write(encode(x)+b'\n')
def files():
    freeze=json.loads((ROOT/'FREEZE.json').read_text())
    got={n:hashlib.sha256((ROOT/n).read_bytes()).hexdigest() for n in freeze['sha256']}
    if got!=freeze['sha256']:raise RuntimeError('source freeze mismatch')
    return got

def inner(out,batch,phase):
    started=time.monotonic()
    source=files() if phase=='formal' else {}
    out.mkdir(parents=True,exist_ok=False)
    save(out/'START.json',dict(batch=batch,phase=phase,pid=os.getpid(),sources=source))
    schedule=[]
    if batch==3:
        schedule=[(0,0,arm,True) for arm in ('PLAIN','INDEXED')]
    else:
        n=SIZES[batch] if phase=='formal' else 32
        for rep in range(3 if phase=='formal' else 1):
            for arm in (('PLAIN','INDEXED') if rep%2==0 else ('INDEXED','PLAIN')):
                schedule.append((n,rep,arm,False))
    env={'PATH':os.environ.get('PATH','/usr/bin:/bin'),'LANG':'C.UTF-8','LC_ALL':'C.UTF-8',
         'PYTHONDONTWRITEBYTECODE':'1','PYTHONHASHSEED':'0'}
    for i,(n,rep,arm,contract) in enumerate(schedule):
        if time.monotonic()-started>30:raise TimeoutError('batch budget')
        name=f'worker-{i:02d}'
        data=out/(name+'-data')
        cmd=[sys.executable,'-S','-B',str(ROOT/'worker.py'),'--out',str(data),
             '--arm',arm,'--n',str(n),'--rep',str(rep),'--phase',phase]
        if contract:cmd.append('--contracts')
        t0=time.monotonic_ns()
        proc=subprocess.Popen(cmd,cwd=ROOT,env=env,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        timed_out=False
        try:o,e=proc.communicate(timeout=min(8,max(.1,30-(time.monotonic()-started))))
        except subprocess.TimeoutExpired:
            timed_out=True;proc.kill();o,e=proc.communicate()
        row=dict(argv=cmd,pid=proc.pid,exit=proc.returncode,timeout=timed_out,
                 start_ns=t0,end_ns=time.monotonic_ns(),stdout_b64=base64.b64encode(o).decode(),
                 stdout_sha256=hashlib.sha256(o).hexdigest(),stderr_b64=base64.b64encode(e).decode())
        save(out/(name+'.json'),row)
        if proc.returncode or timed_out or e:raise RuntimeError('worker failed:'+name)
        json.loads(o)
    if phase=='formal':files()
    save(out/'END.json',dict(batch=batch,phase=phase,workers=len(schedule),pid=os.getpid()))

def main():
    p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True)
    p.add_argument('--batch',type=int,choices=range(4),required=True)
    p.add_argument('--phase',choices=('construction','formal'),required=True)
    p.add_argument('--inner',action='store_true');a=p.parse_args()
    out=a.out.resolve()
    if a.inner:
        inner(out,a.batch,a.phase);return
    if out.exists() or out.with_suffix('.outer.json').exists():p.error('consumed output')
    out.parent.mkdir(parents=True,exist_ok=True)
    if a.phase=='formal' and a.batch>0:
        prev=out.parent/f'batch-{a.batch-1}'
        if not (prev/'END.json').exists() or json.loads(prev.with_suffix('.outer.json').read_text())['exit']!=0:
            p.error('previous batch incomplete')
    cmd=[sys.executable,'-S','-B',str(Path(__file__).resolve()),'--inner','--out',str(out),
         '--batch',str(a.batch),'--phase',a.phase]
    t0=time.monotonic_ns();proc=subprocess.Popen(cmd,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    timeout=False
    try:o,e=proc.communicate(timeout=35)
    except subprocess.TimeoutExpired:
        timeout=True;proc.kill();o,e=proc.communicate()
    record=dict(argv=cmd,pid=proc.pid,exit=proc.returncode,timeout=timeout,start_ns=t0,end_ns=time.monotonic_ns(),
                stdout_b64=base64.b64encode(o).decode(),stderr_b64=base64.b64encode(e).decode())
    save(out.with_suffix('.outer.json'),record)
    print(json.dumps(dict(batch=a.batch,exit=proc.returncode,timeout=timeout)))
    raise SystemExit(0 if proc.returncode==0 and not timeout else 1)

if __name__=='__main__':main()
