#!/usr/bin/env python3
from __future__ import annotations
import argparse,json,subprocess,sys
from pathlib import Path
HERE=Path(__file__).resolve().parent
ORDER=['fresh','stale_uid','wrong_doc','focus_drift','stale_age','text_changed']
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--out',type=Path,required=True);ap.add_argument('--display-base',type=int,default=151);ap.add_argument('--pipe-prefix',default='aidurable');a=ap.parse_args();out=a.out.resolve();out.mkdir(parents=True,exist_ok=False);rows=[]
 for i,c in enumerate(ORDER):
  arm=out/c;cmd=[sys.executable,str(HERE/'run_session.py'),'--condition',c,'--display',f':{a.display_base+i}','--pipe',f'{a.pipe_prefix}_{i}','--out',str(arm)]
  p=subprocess.run(cmd,text=True,capture_output=True);(out/f'{c}.stdout').write_text(p.stdout);(out/f'{c}.stderr').write_text(p.stderr)
  row={'condition':c,'exitcode':p.returncode};
  if (arm/'report.json').exists():row['report']=json.loads((arm/'report.json').read_text())
  rows.append(row)
 summary={'order':ORDER,'sessions':rows,'passed':len(rows)==len(ORDER) and all(r['exitcode']==0 and r.get('report',{}).get('gate_pass') for r in rows)}
 (out/'aggregate.json').write_text(json.dumps(summary,indent=2,ensure_ascii=False)+'\n');print(json.dumps(summary,ensure_ascii=False));return 0 if summary['passed'] else 1
if __name__=='__main__':raise SystemExit(main())
