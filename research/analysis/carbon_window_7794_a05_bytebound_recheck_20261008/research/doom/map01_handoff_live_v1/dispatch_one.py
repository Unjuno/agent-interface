"""Exactly one scheduled first-outcome case per invocation. No retries."""
from pathlib import Path
import argparse, json, subprocess, sys, time

def main():
    a=argparse.ArgumentParser();a.add_argument('index',type=int);a.add_argument('--source',required=True)
    a.add_argument('--runtime',required=True);a.add_argument('--output',required=True);x=a.parse_args()
    src=Path(x.source).resolve();root=Path(x.output).resolve();root.mkdir(exist_ok=True)
    schedule=json.loads((src/'prereg.json').read_text())['schedule']
    if not 0<=x.index<len(schedule):raise SystemExit('invalid index')
    if (root/'STOP.json').exists():raise SystemExit('stopped allocation')
    sys.path.insert(0,str(src));from audit import check_row
    for earlier in schedule[:x.index]:
        path=root/earlier['id']/'result.json'
        if not path.exists():raise SystemExit('missing preceding result')
        errors,_=check_row(json.loads(path.read_text()),earlier,path.parent)
        if errors:raise SystemExit('preceding invalid result:'+str(errors))
    spec=schedule[x.index];mark=root/(spec['id']+'.invocation.json')
    with mark.open('x') as f:json.dump({'spec':spec,'started_ns':time.perf_counter_ns(),'formal_invocations':1},f)
    cmd=[sys.executable,str(src/'run_case.py'),'--out',str(root/spec['id']),'--scenario',spec['scenario'],
         '--policy',spec['policy'],'--seed',str(spec['seed']),'--source',x.runtime]
    with (root/(spec['id']+'.log')).open('x') as log:
        try:r=subprocess.run(cmd,stdout=log,stderr=subprocess.STDOUT,timeout=33);rc=r.returncode
        except subprocess.TimeoutExpired:rc=124
    if rc:
        (root/'STOP.json').write_text(json.dumps({'case':spec,'returncode':rc}));raise SystemExit(rc)
    path=root/spec['id']/'result.json';errors,row=check_row(json.loads(path.read_text()),spec,path.parent)
    if errors:
        (root/'STOP.json').write_text(json.dumps({'case':spec,'errors':errors}));print(errors);raise SystemExit(1)
    print(json.dumps({'index':x.index,'audit':'PASS','row':row}))

if __name__=='__main__':main()
