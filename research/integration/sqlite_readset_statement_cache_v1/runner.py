"""Bounded foreground batching. All child exit codes are observed, never inferred."""
import argparse
import hashlib
import json
import os
import signal
from pathlib import Path
import subprocess
import sqlite3
import sys
import time


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    p=argparse.ArgumentParser(); p.add_argument('out'); p.add_argument('batch',type=int)
    p.add_argument('--construction',action='store_true')
    a=p.parse_args(); here=Path(__file__).resolve().parent
    rows=json.loads((here/'SCHEDULE.json').read_text())
    if a.construction:
        rows=[dict(x,id='build-'+x['id']) for x in rows[:30]]
        batch_size=6
    else:
        batch_size=6
        freeze=json.loads((here/'FREEZE.json').read_text())
        for name,sha in freeze['sources'].items():
            if digest(here/name)!=sha: raise RuntimeError('SOURCE_MISMATCH:'+name)
        env=json.loads((here/'ENVIRONMENT.json').read_text())
        if sys.version!=env['python'] or sqlite3.sqlite_version!=env['sqlite']:
            raise RuntimeError('RUNTIME_VERSION_MISMATCH')
        for name,expected in env['binary_sha256'].items():
            if digest(Path(name))!=expected:raise RuntimeError('RUNTIME_BINARY_MISMATCH:'+name)
    total_batches=(len(rows)+batch_size-1)//batch_size
    if not 0<=a.batch<total_batches: raise ValueError('INVALID_BATCH')
    out=Path(a.out).resolve(); out.mkdir(parents=True,exist_ok=True)
    start=a.batch*batch_size; stop=min(start+batch_size,len(rows))
    previous=None
    if a.batch:
        prev=out/f'batch-{a.batch-1:02d}'/'EXECUTION.json'
        prior=json.loads(prev.read_text())
        if prior['status']!='COMPLETE': raise RuntimeError('PRIOR_BATCH_INCOMPLETE')
        if prior['range'][1]!=start: raise RuntimeError('PRIOR_BATCH_RANGE')
        previous=digest(prev)
    b=out/f'batch-{a.batch:02d}'; b.mkdir(exist_ok=False)
    begin=time.monotonic_ns(); records=[]; status='STOP'
    try:
        for row in rows[start:stop]:
            spec=b/(row['id']+'.json'); spec.write_text(json.dumps(row,sort_keys=True)+'\n')
            argv=[sys.executable,'-B',str(here/'worker.py'),str(spec),str(b/row['id'])]
            t=time.monotonic_ns()
            try:
                child=subprocess.Popen(argv,stdout=subprocess.PIPE,stderr=subprocess.PIPE,
                                       start_new_session=True)
                stdout,stderr=child.communicate(timeout=12)
                code=child.returncode
            except subprocess.TimeoutExpired as e:
                os.killpg(child.pid,signal.SIGKILL)
                stdout,stderr=child.communicate(timeout=2)
                code=child.returncode
            (b/(row['id']+'.stdout')).write_bytes(stdout)
            (b/(row['id']+'.stderr')).write_bytes(stderr)
            receipt={'id':row['id'],'argv':argv,'returncode':code,'started_ns':t,
                     'finished_ns':time.monotonic_ns(),'stdout_sha256':hashlib.sha256(stdout).hexdigest(),
                     'stderr_sha256':hashlib.sha256(stderr).hexdigest()}
            records.append(receipt)
            (b/'PROGRESS.json').write_text(json.dumps(records,indent=2)+'\n')
            if code != 0: raise RuntimeError('CASE_EXIT_OR_TIMEOUT:'+row['id'])
            bound=json.loads(stdout)
            if bound['id']!=row['id'] or bound['raw_sha256']!=digest(b/row['id']/'RAW.json'):
                raise RuntimeError('RAW_STDOUT_BINDING')
        status='COMPLETE'
    finally:
        result={'status':status,'pid':os.getpid(),'range':[start,stop],'planned':stop-start,
                'completed':sum(type(x['returncode']) is int and x['returncode']==0 for x in records),
                'construction':a.construction,'previous_execution_sha256':previous,
                'started_ns':begin,'finished_ns':time.monotonic_ns(),'workers':records}
        (b/'EXECUTION.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
        print(json.dumps({'batch':a.batch,'status':status,'completed':result['completed']}))

if __name__=='__main__':main()
