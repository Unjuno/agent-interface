from __future__ import annotations
import argparse,json,subprocess,sys
from pathlib import Path
HERE=Path(__file__).resolve().parent

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--out',type=Path,required=True);ap.add_argument('--sessions',type=int,default=3);a=ap.parse_args();out=a.out.resolve();out.mkdir(parents=True,exist_ok=False);rows=[]
 schedule=[]
 for i in range(a.sessions):schedule += [('positional',i),('activated',i)]
 for j,(policy,i) in enumerate(schedule):
  arm=out/f'{j:02d}-{policy}-{i}';disp=f':{150+j}';pipe=f'aibind{j}'
  p=subprocess.run([sys.executable,str(HERE/'experiment.py'),'--out',str(arm),'--display',disp,'--policy',policy,'--pipe',pipe],text=True,capture_output=True);(out/f'{j:02d}.stdout').write_text(p.stdout);(out/f'{j:02d}.stderr').write_text(p.stderr)
  try:r=json.loads((arm/'report.json').read_text())
  except Exception:r={'policy':policy,'gate_pass':False,'missing_report':True,'exitcode':p.returncode}
  r['exitcode']=p.returncode;rows.append(r)
 summary={'sessions_per_policy':a.sessions,'rows':rows,'positional_gate':sum(bool(r.get('gate_pass')) for r in rows if r.get('policy')=='positional'),'activated_gate':sum(bool(r.get('gate_pass')) for r in rows if r.get('policy')=='activated')}
 summary['passed']=summary['positional_gate']==a.sessions and summary['activated_gate']==a.sessions
 (out/'aggregate.json').write_text(json.dumps(summary,indent=2,ensure_ascii=False)+'\n');print(json.dumps({k:v for k,v in summary.items() if k!='rows'},indent=2));return 0 if summary['passed'] else 1
if __name__=='__main__':raise SystemExit(main())
