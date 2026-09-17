from __future__ import annotations
import json, subprocess, sys, time
from pathlib import Path
HERE=Path(__file__).resolve().parent
SCHEDULE=[
 ['p01-stable','stable'],['p01-swap','swap'],
 ['p02-swap','swap'],['p02-stable','stable'],
 ['p03-stable','stable'],['p03-swap','swap'],
 ['p04-swap','swap'],['p04-stable','stable'],
 ['p05-stable','stable'],['p05-swap','swap'],
 ['p06-swap','swap'],['p06-stable','stable']]
def main():
 out=HERE/'formal-output'
 if out.exists():raise RuntimeError('formal output exists')
 out.mkdir(); manifest={'formal_invocations':1,'reruns':0,'schedule':SCHEDULE,'started_ns':time.perf_counter_ns(),'cases':[]}
 (out/'manifest.json').write_text(json.dumps(manifest,indent=2,sort_keys=True)+'\n')
 for i,(cid,arm) in enumerate(SCHEDULE):
  cp=subprocess.run([sys.executable,str(HERE/'run_case.py'),'--case-id',cid,'--arm',arm,'--display-num',str(520+i),'--out',str(out/cid)],cwd=HERE,text=True,capture_output=True)
  manifest['cases'].append({'case_id':cid,'arm':arm,'returncode':cp.returncode,'stdout':cp.stdout,'stderr':cp.stderr});(out/'manifest.json').write_text(json.dumps(manifest,indent=2,sort_keys=True)+'\n')
  if cp.returncode: manifest['stopped_after']=cid;break
 manifest['finished_ns']=time.perf_counter_ns();(out/'manifest.json').write_text(json.dumps(manifest,indent=2,sort_keys=True)+'\n')
 if any(x['returncode'] for x in manifest['cases']) or len(manifest['cases'])!=12:raise SystemExit(1)
if __name__=='__main__':main()
