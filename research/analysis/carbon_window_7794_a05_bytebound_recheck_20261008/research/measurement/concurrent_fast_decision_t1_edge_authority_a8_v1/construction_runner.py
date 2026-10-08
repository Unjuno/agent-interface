from __future__ import annotations
import argparse,json,subprocess,sys
from pathlib import Path
from formal_runner import ARMS,TASK
SCENARIO='TRANSIENT_28'

def run(root_path,out_path):
    root=Path(root_path); out=Path(out_path)
    if root.exists() or out.exists(): raise SystemExit('output exists')
    root.mkdir(); cases=[]; runs=[]
    for pos,arm in enumerate(ARMS):
        cid=f'excluded-transient28-{pos}-{arm}'; row=root/f'{cid}.json'; cr=root/cid
        cp=subprocess.run([sys.executable,str(Path(__file__).with_name('formal_runner.py')),'child','--case-id',cid,'--arm',arm,'--scenario',SCENARIO,'--root',str(cr),'--out',str(row)],capture_output=True,text=True)
        runs.append({'case_id':cid,'returncode':cp.returncode,'stdout':cp.stdout,'stderr':cp.stderr})
        if row.exists(): cases.append(json.loads(row.read_text()))
    result={'task':TASK,'phase':'construction','formal_invocations':0,'construction_invocations':1,'reruns':0,'replacements':0,'tuning':0,'excluded':True,'scenario':SCENARIO,'pairs':1,'cases':cases,'child_runs':runs}
    out.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
    print(json.dumps({'rows':len(cases),'child_exit':[x['returncode'] for x in runs]},sort_keys=True))
    return 0 if len(cases)==2 and all(x['returncode']==0 for x in runs) else 3

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--root',required=True);ap.add_argument('--out',required=True);a=ap.parse_args();return run(a.root,a.out)
if __name__=='__main__':raise SystemExit(main())
