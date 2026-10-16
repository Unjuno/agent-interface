"""Synchronous bounded batch launcher with immutable per-batch consumption."""
from __future__ import annotations
import argparse, hashlib, json, os, signal, subprocess, sys, time
from pathlib import Path
HERE=Path(__file__).resolve().parent

def dump(path,obj):
    with path.open('x') as f:json.dump(obj,f,sort_keys=True,indent=2);f.write('\n');f.flush();os.fsync(f.fileno())

def main():
    p=argparse.ArgumentParser();p.add_argument('index',type=int);p.add_argument('root',type=Path);a=p.parse_args()
    if a.index not in range(3):raise ValueError('out-of-schedule batch')
    root=a.root.resolve();root.mkdir(parents=True,exist_ok=True)
    freeze=json.loads((HERE/'FREEZE.json').read_text()); fh=hashlib.sha256((HERE/'FREEZE.json').read_bytes()).hexdigest()
    for name,h in freeze['sha256'].items():
        if hashlib.sha256((HERE/name).read_bytes()).hexdigest()!=h:raise RuntimeError('STOP_SOURCE_CHANGED:'+name)
    if a.index:
        prev=json.loads((root/f'batch{a.index-1}.execution.json').read_text())
        if prev['status']!='COMPLETE' or type(prev['returncode']) is not int or prev['returncode']!=0 or prev['freeze_sha256']!=fh:
            raise RuntimeError('STOP_PREVIOUS_BATCH_INCOMPLETE')
        for name,h in prev['evidence_sha256'].items():
            if hashlib.sha256((root/f'batch{a.index-1}'/name).read_bytes()).hexdigest()!=h:raise RuntimeError('STOP_PREVIOUS_BYTES_CHANGED')
    dump(root/f'batch{a.index}.CONSUMED.json',{'index':a.index,'allocation':freeze['allocation'],'freeze_sha256':fh,'started_ns':time.monotonic_ns()})
    target=root/f'batch{a.index}';cmd=[sys.executable,'-B',str(HERE/'run_batch.py'),'--index',str(a.index),'--out',str(target)]
    rec={'index':a.index,'command':cmd,'freeze_sha256':fh,'started_ns':time.monotonic_ns(),'status':'STARTED'}
    with (root/f'batch{a.index}.stdout').open('xb') as stdout,(root/f'batch{a.index}.stderr').open('xb') as stderr:
        child=subprocess.Popen(cmd,stdout=stdout,stderr=stderr,start_new_session=True);rec['pid']=child.pid
        try:rc=child.wait(timeout=12)
        except subprocess.TimeoutExpired:
            rec['status']='STOP_TIMEOUT';os.killpg(child.pid,signal.SIGTERM)
            try:rc=child.wait(timeout=2)
            except subprocess.TimeoutExpired:os.killpg(child.pid,signal.SIGKILL);rc=child.wait(timeout=2)
    rec['returncode']=rc;rec['ended_ns']=time.monotonic_ns()
    if rec['status']=='STARTED':rec['status']='COMPLETE' if rc==0 else 'STOP_CHILD_EXIT'
    rec['evidence_sha256']={str(p.relative_to(target)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(target.rglob('*')) if p.is_file()}
    dump(root/f'batch{a.index}.execution.json',rec);print(json.dumps({'batch':a.index,'status':rec['status'],'returncode':rc}))
    return 0 if rec['status']=='COMPLETE' else 2
if __name__=='__main__':sys.exit(main())
