from __future__ import annotations
import argparse, json, subprocess, sys, time
from pathlib import Path

TASK='TEMPORAL-CONTRACT-X11-PROPERTYNOTIFY-R1-20260918-001'
SCENARIOS=['POSITIVE','EXPIRE','NO_RESTART']

def write_progress(path, phase, rows, workers, stopped=None):
    payload={'task':TASK,'phase':phase,'rows':rows,'workers':workers,'stopped':stopped}
    path.write_text(json.dumps(payload,indent=2,sort_keys=True)+'\n')

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--phase',choices=['construction','formal'],required=True)
    ap.add_argument('--out',required=True)
    ap.add_argument('--root',required=True)
    ap.add_argument('--progress',required=True)
    a=ap.parse_args()
    out=Path(a.out); progress=Path(a.progress); root=Path(a.root)
    assert not out.exists(); assert not progress.exists(); root.mkdir(parents=True,exist_ok=False)
    schedule=SCENARIOS if a.phase=='construction' else SCENARIOS*4
    rows=[]; workers=[]
    script=Path(__file__).resolve().parent/'case_worker.py'
    for i,scenario in enumerate(schedule):
        cid=f'{a.phase}-{i:02d}-{scenario}'
        case_dir=root/f'{i:02d}-{scenario.lower()}'
        row_file=root/f'row-{i:02d}.json'
        started=time.perf_counter_ns()
        try:
            cp=subprocess.run(
                [sys.executable,'-B',str(script),'--root',str(case_dir),'--scenario',scenario,'--case-id',cid,'--out',str(row_file)],
                cwd=str(script.parent),capture_output=True,text=True,timeout=6,check=False)
            rec={'index':i,'case_id':cid,'scenario':scenario,'returncode':cp.returncode,
                 'stdout':cp.stdout,'stderr':cp.stderr,'elapsed_ns':time.perf_counter_ns()-started}
            workers.append(rec)
            if cp.returncode!=0 or not row_file.exists():
                write_progress(progress,a.phase,rows,workers,{'index':i,'reason':'worker_failure'})
                raise SystemExit(70)
            row=json.loads(row_file.read_text()); rows.append(row)
            write_progress(progress,a.phase,rows,workers,None)
        except subprocess.TimeoutExpired as e:
            workers.append({'index':i,'case_id':cid,'scenario':scenario,'timeout_s':6,'stdout':e.stdout or '',
                            'stderr':e.stderr or '','elapsed_ns':time.perf_counter_ns()-started})
            write_progress(progress,a.phase,rows,workers,{'index':i,'reason':'worker_timeout'})
            raise SystemExit(71)
    result={'task':TASK,'phase':a.phase,'formal_invocations':1 if a.phase=='formal' else 0,
            'reruns':0,'replacements':0,'tuning':0,'rows':rows,'workers':workers}
    out.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
    print(json.dumps({'phase':a.phase,'rows':len(rows),'worker_exits':[w.get('returncode') for w in workers]},sort_keys=True))
if __name__=='__main__': main()
