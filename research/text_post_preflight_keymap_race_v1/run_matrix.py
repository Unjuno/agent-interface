#!/usr/bin/env python3
import argparse,json,subprocess,sys
from pathlib import Path
HERE=Path(__file__).resolve().parent
CASES=[('us',''),('de',''),('fr','')]
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--out',type=Path,required=True);a=ap.parse_args();out=a.out.resolve();out.mkdir(parents=True,exist_ok=False);cases=[]
 for i,(layout,var) in enumerate(CASES):
  od=out/f'{i:02d}-{layout}';p=subprocess.run(['xvfb-run','-a','-s','-screen 0 1024x768x24 -nolisten tcp',sys.executable,str(HERE/'run_case.py'),'--target-layout',layout,'--target-variant',var,'--out',str(od)],text=True,capture_output=True);(out/f'{i:02d}.stdout').write_text(p.stdout);(out/f'{i:02d}.stderr').write_text(p.stderr);cases.append({'layout':layout,'variant':var,'exitcode':p.returncode,'report':json.loads((od/'report.json').read_text()) if (od/'report.json').exists() else None})
 passed=all(c['exitcode']==0 and c['report'] and c['report']['passed'] for c in cases);agg={'schema':'agent-interface/text-post-preflight-keymap-race-matrix-v1','cases':cases,'passed':passed};(out/'aggregate.json').write_text(json.dumps(agg,indent=2,ensure_ascii=False)+'\n');print(json.dumps({'passed':passed,'cases':[{'layout':c['layout'],'actual':c['report']['actual'] if c['report'] else None,'timing':c['report']['gates']['timing'] if c['report'] else None} for c in cases]},ensure_ascii=False,indent=2));return 0 if passed else 1
if __name__=='__main__':raise SystemExit(main())
