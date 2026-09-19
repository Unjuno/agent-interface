#!/usr/bin/env python3
import argparse, json, subprocess, sys
from pathlib import Path

p=argparse.ArgumentParser(); p.add_argument('--schedule',required=True); p.add_argument('--out',required=True); p.add_argument('--display-base',type=int,default=620); a=p.parse_args()
schedule=json.load(open(a.schedule))
out=Path(a.out); out.mkdir(parents=True,exist_ok=True)
ledger=[]
for i,row in enumerate(schedule['cases']):
    case_out=out/row['case_id']
    if (case_out/'result.json').exists():
        raise RuntimeError(f"refuse rerun existing case {row['case_id']}")
    cp=subprocess.run([sys.executable,str(Path(__file__).with_name('run_case.py')),
        '--trajectory',row['trajectory'],'--policy',row['policy'],'--case-id',row['case_id'],
        '--out',str(case_out),'--display-num',str(a.display_base+i)],capture_output=True,text=True)
    ledger.append({'case_id':row['case_id'],'returncode':cp.returncode,'stdout':cp.stdout,'stderr':cp.stderr})
    (out/'ledger.json').write_text(json.dumps(ledger,indent=2,sort_keys=True)+'\n')
    if cp.returncode != 0:
        raise SystemExit(cp.returncode)
print(json.dumps({'cases_completed':len(ledger),'status':'COMPLETE'},sort_keys=True))
