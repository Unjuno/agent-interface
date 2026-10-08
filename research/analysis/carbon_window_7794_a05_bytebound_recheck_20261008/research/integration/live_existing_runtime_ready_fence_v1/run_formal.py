#!/usr/bin/env python3
import argparse,json,subprocess,sys,time
from pathlib import Path

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--artifact-root',type=Path,required=True);ap.add_argument('--artifact-zip',type=Path,required=True);ap.add_argument('--experiment-dir',type=Path,required=True);ap.add_argument('--out',type=Path,required=True)
    a=ap.parse_args();a.out.mkdir(parents=True,exist_ok=False)
    marker=a.out/'FORMAL_INVOCATION.json'
    marker.write_text(json.dumps({'formal_invocations':1,'started_ns':time.perf_counter_ns()},sort_keys=True)+'\n')
    schedule=json.loads((a.experiment_dir/'schedule.json').read_text())
    rows=[]
    for row in schedule['cases']:
        cmd=[sys.executable,str(a.experiment_dir/'run_case.py'),'--case-id',row['case_id'],'--policy',row['policy'],'--seed',str(row['seed']),'--artifact-root',str(a.artifact_root),'--artifact-zip',str(a.artifact_zip),'--experiment-dir',str(a.experiment_dir),'--out-root',str(a.out)]
        p=subprocess.run(cmd,text=True,capture_output=True,timeout=30)
        rows.append({'case_id':row['case_id'],'returncode':p.returncode,'stdout':p.stdout,'stderr':p.stderr})
        if p.returncode!=0:
            (a.out/'runner-summary.json').write_text(json.dumps(rows,indent=2,sort_keys=True)+'\n')
            raise SystemExit(f"formal stopped at {row['case_id']} rc={p.returncode}")
    (a.out/'runner-summary.json').write_text(json.dumps(rows,indent=2,sort_keys=True)+'\n')
    print(json.dumps({'formal_invocations':1,'cases':len(rows),'failures':sum(r['returncode']!=0 for r in rows)},sort_keys=True))
if __name__=='__main__':main()
