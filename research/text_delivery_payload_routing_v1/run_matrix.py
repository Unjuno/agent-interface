#!/usr/bin/env python3
from __future__ import annotations
import argparse,json,os,subprocess,sys
from pathlib import Path
HERE=Path(__file__).resolve().parent
ARMS=[('us',''),('de',''),('fr',''),('us','dvorak')]
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--out',type=Path,required=True);a=ap.parse_args();out=a.out.resolve();out.mkdir(parents=True,exist_ok=False);arms=[]
 for i,(layout,variant) in enumerate(ARMS):
  arm=out/f'{i:02d}-{layout}-{variant or "default"}';cmd=['xvfb-run','-a','-s','-screen 0 1024x768x24 -nolisten tcp',sys.executable,str(HERE/'run_arm.py'),'--layout',layout,'--variant',variant,'--out',str(arm)];p=subprocess.run(cmd,text=True,capture_output=True);(out/f'{i:02d}.stdout').write_text(p.stdout);(out/f'{i:02d}.stderr').write_text(p.stderr);arms.append({'layout':layout,'variant':variant,'exitcode':p.returncode,'report':json.loads((arm/'report.json').read_text()) if (arm/'report.json').exists() else None})
 total=sum(x['report']['trial_count'] for x in arms if x['report']);mismatch=sum(x['report']['coarse_mismatch_count'] for x in arms if x['report']);routes={k:sum(x['report']['route_counts'][k] for x in arms if x['report']) for k in ['direct_keys','clipboard_utf8','none']};passed=all(x['exitcode']==0 and x['report'] and x['report']['passed'] for x in arms) and total==104
 aggregate={'schema':'agent-interface/text-delivery-payload-routing-matrix-v1','order':ARMS,'trial_count':total,'route_counts':routes,'coarse_mismatch_count':mismatch,'arms':arms,'passed':passed};(out/'aggregate.json').write_text(json.dumps(aggregate,indent=2,ensure_ascii=False)+'\n');print(json.dumps({'trial_count':total,'route_counts':routes,'coarse_mismatch_count':mismatch,'passed':passed},indent=2));return 0 if passed else 1
if __name__=='__main__':raise SystemExit(main())
