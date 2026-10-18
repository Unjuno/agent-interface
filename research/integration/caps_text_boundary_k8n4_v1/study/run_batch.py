"""Run one finite six-case batch, preserving first process outputs."""
import argparse, hashlib, json, subprocess, sys, time
from pathlib import Path

def main():
    p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True)
    p.add_argument('--batch',type=int,choices=range(4),required=True);a=p.parse_args()
    root=a.root.resolve(); freeze=json.loads((root/'FREEZE.json').read_text())
    for rel,digest in freeze['files'].items():
        if hashlib.sha256((root/rel).read_bytes()).hexdigest()!=digest: raise RuntimeError('frozen source differs: '+rel)
    out=root/'formal'/f'batch{a.batch}';out.mkdir(parents=True,exist_ok=False)
    conditions=['OFF','INITIAL_ON','PROGRAM_ON','PROGRAM_OFF','PROGRAM_ROUNDTRIP','ON_DIGITS']
    arm=['CURRENT','TEXT_LOCK_GUARD'][a.batch%2];rep=a.batch//2
    rows=[]
    for condition in conditions:
        session=f'k8n4-r{rep}-{arm.lower()}-{condition.lower()}'
        command=[sys.executable,'-B',str(root/'study/case.py'),'--source',str(root/('current_source' if arm=='CURRENT' else 'candidate_source')),
                 '--out',str(out/condition),'--condition',condition,'--arm',arm,'--session',session]
        start=time.monotonic_ns()
        with (out/(condition+'.stdout')).open('xb') as stdout, (out/(condition+'.stderr')).open('xb') as stderr:
            process=subprocess.Popen(command,stdout=stdout,stderr=stderr)
            process.wait(timeout=25)
        rows.append({'session':session,'condition':condition,'argv':command,'pid':process.pid,
                     'exit':process.returncode,'started_ns':start,'ended_ns':time.monotonic_ns()})
        (out/'BATCH.json').write_text(json.dumps({'batch':a.batch,'arm':arm,'rep':rep,'rows':rows,'complete':len(rows)==6},indent=2)+'\n')
        if process.returncode: return 1
    return 0
if __name__=='__main__': raise SystemExit(main())
