#!/usr/bin/env python3
import argparse,json,subprocess,sys
from pathlib import Path
HERE=Path(__file__).resolve().parent
CASES=[('us',''),('de',''),('fr','')]
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--out',type=Path,required=True);a=ap.parse_args();out=a.out.resolve();out.mkdir(parents=True,exist_ok=False);rows=[]
 for i,(layout,var) in enumerate(CASES):
  od=out/f'{i:02d}-{layout}';p=subprocess.run(['xvfb-run','-a','-s','-screen 0 1024x768x24 -nolisten tcp',sys.executable,str(HERE/'run_case.py'),'--target-layout',layout,'--target-variant',var,'--out',str(od)],text=True,capture_output=True);rows.append({'layout':layout,'variant':var,'exitcode':p.returncode,'report':json.loads((od/'report.json').read_text()) if (od/'report.json').exists() else None});(out/f'{i:02d}.stdout').write_text(p.stdout);(out/f'{i:02d}.stderr').write_text(p.stderr)
 passed=all(r['exitcode']==0 and r['report'] and r['report']['passed'] for r in rows);agg={'schema':'agent-interface/text-route-keymap-freshness-matrix-v1','cases':rows,'passed':passed};(out/'aggregate.json').write_text(json.dumps(agg,indent=2,ensure_ascii=False)+'\n');print(json.dumps({'passed':passed,'cases':[{'layout':r['layout'],'exit':r['exitcode'],'unsafe':r['report']['unsafe']['actual'] if r['report'] else None,'safe_error':r['report']['safe']['receipt']['error'] if r['report'] else None} for r in rows]},ensure_ascii=False,indent=2));return 0 if passed else 1
if __name__=='__main__':raise SystemExit(main())
