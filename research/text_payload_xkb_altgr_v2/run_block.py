from __future__ import annotations
import argparse, json, subprocess, sys
from pathlib import Path
HERE=Path(__file__).resolve().parent

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('out',type=Path); args=ap.parse_args(); out=args.out.resolve()
    if out.exists(): raise SystemExit('refuse existing output'); out.mkdir(parents=True)
    sched=json.loads((HERE/'schedule.json').read_text()); records=[]
    for rep in range(sched['repetitions']):
        d=out/f'rep-{rep}'; cmd=['xvfb-run','-a','-s','-screen 0 800x600x24',sys.executable,str(HERE/'run_arm.py'),'--rep',str(rep),'--out',str(d)]
        cp=subprocess.run(cmd,capture_output=True,text=True); (out/f'rep-{rep}.stdout').write_text(cp.stdout); (out/f'rep-{rep}.stderr').write_text(cp.stderr); records.append({'rep':rep,'returncode':cp.returncode,'stdout':cp.stdout,'stderr':cp.stderr})
        if cp.returncode!=0: break
    summary={'task':sched['task'],'planned_repetitions':sched['repetitions'],'completed_repetitions':len(records),'arms':records,'runner_complete':len(records)==sched['repetitions'] and all(r['returncode']==0 for r in records)}
    (out/'run_summary.json').write_text(json.dumps(summary,indent=2,sort_keys=True)+'\n'); print(json.dumps(summary,sort_keys=True)); return 0 if summary['runner_complete'] else 1
if __name__=='__main__': raise SystemExit(main())
