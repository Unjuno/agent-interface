#!/usr/bin/env python3
import argparse, hashlib, json, subprocess, sys, time
from pathlib import Path
POLICIES=['BASELINE','KEY_UP_RECEIPT']
SCHEDULES=['ORDINARY_SINGLE','ORDINARY_MULTI','CANCEL_AFTER_HELD','CANCEL_DURING_ADMISSION']

def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 ap=argparse.ArgumentParser(); ap.add_argument('--out',required=True); ap.add_argument('--reps',type=int,default=3); a=ap.parse_args(); out=Path(a.out); out.mkdir(parents=True,exist_ok=False)
 src=Path(__file__).resolve().parent; rows=[]; idx=0
 for rep in range(a.reps):
  order=POLICIES[rep%2:]+POLICIES[:rep%2]
  for schedule in SCHEDULES:
   for policy in order:
    case=f'r{rep}-{schedule.lower()}-{policy.lower()}'; cdir=out/'cases'/case; cdir.parent.mkdir(parents=True,exist_ok=True)
    cmd=[sys.executable,str(src/'case_worker.py'),'--policy',policy,'--schedule',schedule,'--index',str(idx),'--out',str(cdir)]
    t0=time.perf_counter_ns(); p=subprocess.run(cmd,text=True,capture_output=True,timeout=8); t1=time.perf_counter_ns()
    row={'case':case,'rep':rep,'schedule':schedule,'policy':policy,'index':idx,'cmd':cmd,'returncode':p.returncode,'stdout':p.stdout,'stderr':p.stderr,'wall_ns':t1-t0}
    rows.append(row); (out/'rows.json').write_text(json.dumps(rows,indent=2)+'\n')
    if p.returncode!=0: raise SystemExit(f'case failed {case}: {p.stderr}')
    idx+=1
 receipt={'cases':len(rows),'source_sha256':{'case_worker.py':sha(src/'case_worker.py'),'run_matrix.py':sha(src/'run_matrix.py')},'all_zero':all(r['returncode']==0 for r in rows)}
 (out/'EXECUTION.json').write_text(json.dumps(receipt,indent=2,sort_keys=True)+'\n')
 print(json.dumps(receipt,sort_keys=True))
if __name__=='__main__': main()
