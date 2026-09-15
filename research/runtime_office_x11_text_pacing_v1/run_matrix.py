#!/usr/bin/env python3
from __future__ import annotations
import argparse, json, subprocess, sys, time
from pathlib import Path
HERE=Path(__file__).resolve().parent
ORDER=[0,12,2,8,1,4]
def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--out',type=Path,required=True); ap.add_argument('--display-base',type=int,default=230); a=ap.parse_args(); a.out.mkdir(parents=True,exist_ok=False)
    rows=[]
    for idx,p in enumerate(ORDER):
        arm=a.out/f'{p:02d}ms'; start=time.perf_counter_ns(); r=subprocess.run([sys.executable,str(HERE/'run_arm.py'),'--out',str(arm),'--display',f':{a.display_base+idx}','--pacing-ms',str(p)],text=True,capture_output=True); end=time.perf_counter_ns()
        (a.out/f'{p:02d}ms.stdout').write_text(r.stdout); (a.out/f'{p:02d}ms.stderr').write_text(r.stderr); (a.out/f'{p:02d}ms.exitcode').write_text(str(r.returncode)+'\n')
        report=json.loads((arm/'report.json').read_text()) if (arm/'report.json').exists() else {'passed':False}
        score=json.loads((arm/'score.json').read_text()) if (arm/'score.json').exists() else {'mismatches':[{'error':'missing'}]}
        ex=json.loads((arm/'execution'/'execution.json').read_text()) if (arm/'execution'/'execution.json').exists() else {}
        rows.append({'pacing_ms':p,'passed':r.returncode==0 and report.get('passed') is True,'mismatch_count':len(score.get('mismatches',[])),'mismatches':score.get('mismatches',[]),'arm_wall_ns':end-start,'task_elapsed_ns':ex.get('task_elapsed_ns'),'backend_emissions':ex.get('backend_emissions'),'release_verified':ex.get('release_verified')})
    passing=sorted(r['pacing_ms'] for r in rows if r['passed'])
    summary={'schema':'agent-interface/office-x11-text-pacing-matrix-v1','order':ORDER,'rows':rows,'minimum_passing_tested_ms':passing[0] if passing else None,'passed':bool(passing)}
    (a.out/'matrix.json').write_text(json.dumps(summary,indent=2)+'\n'); print(json.dumps(summary,indent=2)); return 0 if passing else 1
if __name__=='__main__': raise SystemExit(main())
