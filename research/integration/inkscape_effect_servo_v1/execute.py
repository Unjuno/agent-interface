from __future__ import annotations
import hashlib,json,subprocess,sys,time
from pathlib import Path
HERE=Path(__file__).resolve().parent

def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def load(p): return json.loads(p.read_text())
def main():
    if len(sys.argv)!=2: raise SystemExit('usage: execute.py INDEX')
    idx=int(sys.argv[1]); freeze=load(HERE/'FREEZE.json'); sched=load(HERE/'SCHEDULE.json')['cases']
    if not 0<=idx<len(sched): raise SystemExit('bad index')
    for rel,h in freeze['sha256'].items():
        p=HERE/rel
        if not p.exists() or sha(p)!=h: raise SystemExit('FROZEN_SOURCE_MISMATCH:'+rel)
    formal=HERE/'formal'; formal.mkdir(exist_ok=True)
    for j in range(idx):
        r=formal/f'case-{j:02d}'/'CASE.json'
        if not r.exists() or load(r).get('worker_returncode')!=0: raise SystemExit('PRIOR_CASE_INCOMPLETE:'+str(j))
    out=formal/f'case-{idx:02d}'
    if out.exists(): raise SystemExit('OUTPUT_EXISTS')
    c=sched[idx]
    cmd=[sys.executable,'-B',str(HERE/'study.py'),str(out),c['policy'],str(c['first_dx']),str(c['first_dy']),str(c['rep']),'--phase','formal']
    t0=time.monotonic_ns(); p=subprocess.run(cmd,capture_output=True,text=True,timeout=35); t1=time.monotonic_ns()
    receipt={'index':idx,'spec':c,'argv':cmd,'pid_observed_by_parent':p.args is not None,'returncode':p.returncode,'stdout':p.stdout,'stderr':p.stderr,'start_ns':t0,'end_ns':t1,'timeout':False}
    (formal/f'WRAPPER-{idx:02d}.json').write_text(json.dumps(receipt,indent=2,sort_keys=True)+'\n')
    print(json.dumps({'index':idx,'returncode':p.returncode,'stdout':p.stdout.strip(),'stderr':p.stderr.strip()},sort_keys=True),flush=True)
    return p.returncode
if __name__=='__main__': raise SystemExit(main())
