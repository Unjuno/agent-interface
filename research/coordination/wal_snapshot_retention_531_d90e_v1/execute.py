"""One-shot bounded subprocess wrapper. Never treats a marker as an observed exit."""
from __future__ import annotations
import argparse,hashlib,json,os,signal,subprocess,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parent

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--mode',choices=['construction','formal'],required=True)
    ap.add_argument('--batch',type=int,default=0);a=ap.parse_args()
    key=f'{a.mode}-{a.batch:02d}';receipt=ROOT/(key+'-execution.json')
    if a.mode=='formal':
        freeze=json.loads((ROOT/'FREEZE.json').read_text())
        for f,h in freeze['files'].items():
            if hashlib.sha256((ROOT/f).read_bytes()).hexdigest()!=h:raise RuntimeError('SOURCE_MISMATCH:'+f)
        if a.batch not in (0,1):raise ValueError('BATCH_RANGE')
        if a.batch:
            prev=json.loads((ROOT/f'formal-{a.batch-1:02d}-execution.json').read_text())
            if prev['returncode']!=0 or prev['timeout']:raise RuntimeError('PRIOR_INCOMPLETE')
    marker=ROOT/(key+'-CONSUMED')
    with marker.open('x') as f:f.write(str(time.monotonic_ns()))
    command=[sys.executable,'-B',str(ROOT/'run.py'),'--mode',a.mode,'--batch',str(a.batch)]
    start=time.monotonic_ns();timedout=False
    with open(ROOT/(key+'.stdout'),'wb') as out,open(ROOT/(key+'.stderr'),'wb') as err:
        proc=subprocess.Popen(command,stdout=out,stderr=err,start_new_session=True)
        try:rc=proc.wait(timeout=25)
        except subprocess.TimeoutExpired:
            timedout=True;os.killpg(proc.pid,signal.SIGTERM)
            try:rc=proc.wait(timeout=2)
            except subprocess.TimeoutExpired:os.killpg(proc.pid,signal.SIGKILL);rc=proc.wait(timeout=2)
    result={'command':command,'pid':proc.pid,'started_ns':start,'ended_ns':time.monotonic_ns(),
            'timeout':timedout,'returncode':rc,'stdout_sha256':hashlib.sha256((ROOT/(key+'.stdout')).read_bytes()).hexdigest(),
            'stderr_sha256':hashlib.sha256((ROOT/(key+'.stderr')).read_bytes()).hexdigest()}
    receipt.write_text(json.dumps(result,sort_keys=True,indent=2)+'\n');print(json.dumps(result))
    sys.exit(1 if timedout else rc)
if __name__=='__main__':main()
