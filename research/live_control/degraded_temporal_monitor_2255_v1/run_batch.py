#!/usr/bin/env python3
import argparse, hashlib, json, pathlib, subprocess, sys, time
SCENARIOS=['AB_WITHIN','AB_LATE','A_ONLY','CANCEL_COMPLETE','CANCEL_DROP_DECLARED','CANCEL_DROP_UNDECLARED','REORDER_DECLARED','CROSS_CLOCK_DECLARED']

def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 ap=argparse.ArgumentParser(); ap.add_argument('--batch',type=int,choices=[0,1]); ap.add_argument('--root',type=pathlib.Path,default=pathlib.Path('formal'))
 a=ap.parse_args(); study=pathlib.Path(__file__).resolve().parent
 a.root.mkdir(exist_ok=True)
 marker=a.root/f'BATCH{a.batch}.STARTED'; marker.open('x').write(str(time.time_ns()))
 rows=[]
 for j,sc in enumerate(SCENARIOS):
  idx=a.batch*8+j; out=a.root/f'case-{idx:02d}-{sc.lower()}'
  display=520+idx
  cmd=[sys.executable,'-S','-B',str(study/'case.py'),'--scenario',sc,'--rep',str(a.batch),'--out',str(out),'--display',str(display)]
  t=time.monotonic_ns(); p=subprocess.run(cmd,capture_output=True,text=True,timeout=8); dur=time.monotonic_ns()-t
  rows.append({'index':idx,'scenario':sc,'cmd':cmd,'returncode':p.returncode,'stdout':p.stdout,'stderr':p.stderr,'duration_ns':dur,'case_sha256':sha(out/'CASE.json') if (out/'CASE.json').exists() else None})
  if p.returncode!=0 or not (out/'CASE.json').exists():
   (a.root/f'BATCH{a.batch}.json').write_text(json.dumps({'batch':a.batch,'status':'STOP','rows':rows},indent=2)+'\n'); raise SystemExit(2)
 receipt={'batch':a.batch,'status':'COMPLETE','rows':rows,'completed_ns':time.time_ns()}
 (a.root/f'BATCH{a.batch}.json').write_text(json.dumps(receipt,indent=2,sort_keys=True)+'\n')
 print(json.dumps({'status':'COMPLETE','batch':a.batch,'cases':len(rows)},sort_keys=True))
if __name__=='__main__': main()
