#!/usr/bin/env python3
from __future__ import annotations
import argparse,json,os,subprocess,sys
from pathlib import Path
HERE=Path(__file__).resolve().parent
SCHEDULE=['compare_set','recheck_set','controllers_lock_set','controllers_lock_set','compare_set','recheck_set','recheck_set','controllers_lock_set','compare_set']
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--out',type=Path,required=True);a=ap.parse_args();out=a.out.resolve();out.mkdir(parents=True,exist_ok=False); rows=[]
 for i,arm in enumerate(SCHEDULE):
  sd=out/f'{i:02d}-{arm}'; env=os.environ.copy();env['AGENT_INTERFACE_PRIVATE_XVFB']='1'
  cmd=['xvfb-run','-a','-s','-screen 0 1024x768x24 -nolisten tcp','env','AGENT_INTERFACE_PRIVATE_XVFB=1',sys.executable,str(HERE/'run_session.py'),'--arm',arm,'--out',str(sd)]
  r=subprocess.run(cmd,env=env,text=True,capture_output=True); (out/f'{i:02d}.stdout').write_text(r.stdout);(out/f'{i:02d}.stderr').write_text(r.stderr)
  if (sd/'report.json').exists(): rows.append(json.loads((sd/'report.json').read_text()))
  else: rows.append({'arm':arm,'passed_negative':False,'missing_report':True,'exitcode':r.returncode})
  if r.returncode!=0: break
 summary={'schema':'agent-interface/writer-uno-serialization-negative-matrix-v1','schedule':SCHEDULE,'rows':rows,'completed':len(rows),'passed':len(rows)==len(SCHEDULE) and all(x.get('passed_negative') for x in rows)}
 (out/'aggregate.json').write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps({'completed':len(rows),'passed':summary['passed']}));return 0 if summary['passed'] else 1
if __name__=='__main__': raise SystemExit(main())
