#!/usr/bin/env python3
from __future__ import annotations
import argparse,json,subprocess,sys
from pathlib import Path
HERE=Path(__file__).resolve().parent
SCHEDULE=[('us',''),('de',''),('fr',''),('us','dvorak')]
def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--out',type=Path,required=True); ap.add_argument('--dependency',type=Path,required=True); a=ap.parse_args(); a.out=a.out.resolve(); a.out.mkdir(parents=True,exist_ok=False); arms=[]
    for i,(layout,variant) in enumerate(SCHEDULE):
        name=f'{i:02d}-{layout}-{variant or "default"}'; arm=a.out/name; cmd=['xvfb-run','-a','-s','-screen 0 1024x768x24 -nolisten tcp',sys.executable,str(HERE/'run_arm_v2.py'),'--layout',layout,'--out',str(arm),'--dependency',str(a.dependency.resolve())]
        if variant: cmd+=['--variant',variant]
        r=subprocess.run(cmd,text=True,capture_output=True); (a.out/f'{name}.stdout').write_text(r.stdout); (a.out/f'{name}.stderr').write_text(r.stderr); rep=json.loads((arm/'report.json').read_text()) if (arm/'report.json').exists() else {'passed':False}; rep['exitcode']=r.returncode; arms.append(rep)
    agg={'schema':'agent-interface/text-payload-xkb-disposable-matrix-v2','schedule':[{'layout':x,'variant':y} for x,y in SCHEDULE],'arms':arms,'passed':all(x.get('passed') and x.get('exitcode')==0 for x in arms)}; (a.out/'aggregate.json').write_text(json.dumps(agg,indent=2,ensure_ascii=False)+'\n'); print(json.dumps({'passed':agg['passed'],'arms':[{'layout':x.get('layout'),'variant':x.get('variant'),'accepted':x.get('accepted_count'),'rejected':x.get('rejected_count'),'passed':x.get('passed'),'exitcode':x.get('exitcode')} for x in arms]},indent=2)); return 0 if agg['passed'] else 1
if __name__=='__main__': raise SystemExit(main())
