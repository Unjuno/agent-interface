#!/usr/bin/env python3
import argparse,json,subprocess,sys
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--schedule',required=True);p.add_argument('--out',required=True);p.add_argument('--chunk',type=int,choices=[1,2,3,4],required=True);p.add_argument('--display-base',type=int,default=960);a=p.parse_args()
rows=[r for r in json.load(open(a.schedule))['cases'] if r['chunk']==a.chunk]
out=Path(a.out);out.mkdir(parents=True,exist_ok=True); ledger=out/f'ledger_chunk_{a.chunk}.json'
if ledger.exists(): raise RuntimeError('refuse rerun ledger')
L=[]
for j,r in enumerate(rows):
 d=out/r['case_id']
 if d.exists(): raise RuntimeError(f"refuse rerun {r['case_id']}")
 cp=subprocess.run([sys.executable,str(Path(__file__).with_name('run_case.py')),'--out',str(d),'--context',r['context'],'--policy',r['policy'],'--display',str(a.display_base+(a.chunk-1)*10+j)],capture_output=True,text=True)
 L.append({'case_id':r['case_id'],'returncode':cp.returncode,'stdout':cp.stdout,'stderr':cp.stderr});ledger.write_text(json.dumps(L,indent=2,sort_keys=True)+'\n')
 if cp.returncode: raise SystemExit(cp.returncode)
print(json.dumps({'chunk':a.chunk,'status':'COMPLETE'}))
