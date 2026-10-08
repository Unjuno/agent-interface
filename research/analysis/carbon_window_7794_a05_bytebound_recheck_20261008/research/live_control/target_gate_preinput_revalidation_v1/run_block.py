from __future__ import annotations
import json,subprocess,sys,time
from pathlib import Path
HERE=Path(__file__).resolve().parent
SCHEDULE=[
 ['r01-sn','stable','no_revalidation'],['r01-sr','stable','revalidate'],['r01-xn','swap','no_revalidation'],['r01-xr','swap','revalidate'],
 ['r02-xr','swap','revalidate'],['r02-xn','swap','no_revalidation'],['r02-sr','stable','revalidate'],['r02-sn','stable','no_revalidation'],
 ['r03-sr','stable','revalidate'],['r03-sn','stable','no_revalidation'],['r03-xr','swap','revalidate'],['r03-xn','swap','no_revalidation'],
 ['r04-xn','swap','no_revalidation'],['r04-xr','swap','revalidate'],['r04-sn','stable','no_revalidation'],['r04-sr','stable','revalidate']]
def main():
 out=HERE/'formal-output'
 if out.exists():raise RuntimeError('formal output exists')
 out.mkdir();m={'formal_invocations':1,'reruns':0,'schedule':SCHEDULE,'cases':[],'started_ns':time.perf_counter_ns()};(out/'manifest.json').write_text(json.dumps(m,indent=2,sort_keys=True)+'\n')
 for i,(cid,state,policy) in enumerate(SCHEDULE):
  cp=subprocess.run([sys.executable,str(HERE/'run_case.py'),'--case-id',cid,'--state',state,'--policy',policy,'--display-num',str(560+i),'--out',str(out/cid)],cwd=HERE,text=True,capture_output=True)
  m['cases'].append({'case_id':cid,'state':state,'policy':policy,'returncode':cp.returncode,'stdout':cp.stdout,'stderr':cp.stderr});(out/'manifest.json').write_text(json.dumps(m,indent=2,sort_keys=True)+'\n')
  if cp.returncode:m['stopped_after']=cid;break
 m['finished_ns']=time.perf_counter_ns();(out/'manifest.json').write_text(json.dumps(m,indent=2,sort_keys=True)+'\n')
 if len(m['cases'])!=16 or any(x['returncode'] for x in m['cases']):raise SystemExit(1)
if __name__=='__main__':main()
