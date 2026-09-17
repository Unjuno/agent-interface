from __future__ import annotations
import json, subprocess, sys, time
from pathlib import Path
HERE=Path(__file__).resolve().parent
SCHEDULE=[
 ['r01-stable-single','stable','single_gate'],['r01-stable-reval','stable','preinput_revalidate'],['r01-swap-single','swap','single_gate'],['r01-swap-reval','swap','preinput_revalidate'],
 ['r02-swap-reval','swap','preinput_revalidate'],['r02-swap-single','swap','single_gate'],['r02-stable-reval','stable','preinput_revalidate'],['r02-stable-single','stable','single_gate'],
 ['r03-stable-reval','stable','preinput_revalidate'],['r03-stable-single','stable','single_gate'],['r03-swap-reval','swap','preinput_revalidate'],['r03-swap-single','swap','single_gate'],
 ['r04-swap-single','swap','single_gate'],['r04-swap-reval','swap','preinput_revalidate'],['r04-stable-single','stable','single_gate'],['r04-stable-reval','stable','preinput_revalidate']]
def main():
 out=HERE/'formal-output'
 if out.exists(): raise RuntimeError('formal output exists')
 out.mkdir(); manifest={'formal_invocations':1,'reruns':0,'schedule':SCHEDULE,'started_ns':time.perf_counter_ns(),'cases':[]}
 (out/'manifest.json').write_text(json.dumps(manifest,indent=2,sort_keys=True)+'\n')
 for i,(cid,mutation,policy) in enumerate(SCHEDULE):
  cp=subprocess.run([sys.executable,str(HERE/'run_case.py'),'--case-id',cid,'--mutation',mutation,'--policy',policy,'--display-num',str(620+i),'--out',str(out/cid)],cwd=HERE,text=True,capture_output=True)
  manifest['cases'].append({'case_id':cid,'mutation':mutation,'policy':policy,'returncode':cp.returncode,'stdout':cp.stdout,'stderr':cp.stderr}); (out/'manifest.json').write_text(json.dumps(manifest,indent=2,sort_keys=True)+'\n')
  if cp.returncode: manifest['stopped_after']=cid; break
 manifest['finished_ns']=time.perf_counter_ns(); (out/'manifest.json').write_text(json.dumps(manifest,indent=2,sort_keys=True)+'\n')
 if any(x['returncode'] for x in manifest['cases']) or len(manifest['cases'])!=16: raise SystemExit(1)
if __name__=='__main__': main()
