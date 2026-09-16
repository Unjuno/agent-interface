#!/usr/bin/env python3
from __future__ import annotations
import argparse, json, subprocess, sys
from pathlib import Path
HERE=Path(__file__).resolve().parent
SCHEDULE=[('us',''),('de',''),('fr',''),('us','dvorak')]
def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--out',type=Path,required=True); ap.add_argument('--dependency',type=Path,required=True); a=ap.parse_args(); a.out=a.out.resolve(); a.out.mkdir(parents=True,exist_ok=False)
    arms=[]
    for i,(layout,variant) in enumerate(SCHEDULE):
        name=f'{i:02d}-{layout}-{variant or "default"}'; arm=a.out/name
        cmd=['xvfb-run','-a','-s','-screen 0 1024x768x24 -nolisten tcp',sys.executable,str(HERE/'run_arm.py'),'--layout',layout,'--out',str(arm),'--dependency',str(a.dependency.resolve())]
        if variant: cmd += ['--variant',variant]
        r=subprocess.run(cmd,text=True,capture_output=True); (a.out/f'{name}.stdout').write_text(r.stdout); (a.out/f'{name}.stderr').write_text(r.stderr); report=json.loads((arm/'report.json').read_text()) if (arm/'report.json').exists() else {'passed':False}; report['exitcode']=r.returncode; arms.append(report)
    aggregate={'schema':'agent-interface/text-payload-xkb-layout-matrix-v1','schedule':[{'layout':x,'variant':y} for x,y in SCHEDULE],'arms':arms,'passed':all(r.get('passed') and r.get('exitcode')==0 for r in arms)}
    (a.out/'aggregate.json').write_text(json.dumps(aggregate,indent=2,ensure_ascii=False)+'\n'); print(json.dumps({'passed':aggregate['passed'],'arms':[{'layout':r.get('layout'),'variant':r.get('variant'),'accepted':r.get('accepted_count'),'rejected':r.get('rejected_count'),'passed':r.get('passed')} for r in arms]},indent=2)); return 0 if aggregate['passed'] else 1
if __name__=='__main__': raise SystemExit(main())
