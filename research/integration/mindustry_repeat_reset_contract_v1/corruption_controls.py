#!/usr/bin/env python3
import json,shutil,subprocess,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parent

def run(name, mutate):
    with tempfile.TemporaryDirectory() as td:
        d=Path(td)/'x'; shutil.copytree(ROOT,d,ignore=shutil.ignore_patterns('.formal-invoked','AUDIT.json','CORRUPTION.json','__pycache__'))
        p=d/'RESULT.json'; r=json.loads(p.read_text()); mutate(r); p.write_text(json.dumps(r,indent=2,sort_keys=True)+'\n')
        q=subprocess.run(['python3',str(d/'audit.py'),str(d)],capture_output=True,text=True)
        return {'name':name,'rejected':q.returncode!=0,'returncode':q.returncode}

def main():
    cs=[]
    cs.append(run('launder_wrong_effect',lambda r:r['rows'][0]['task_evaluation'].__setitem__('contract_satisfied',False)))
    cs.append(run('bad_reset_escape',lambda r:r['controls']['target_occupied_reset'].__setitem__('ok',True)))
    cs.append(run('oracle_leak_escape',lambda r:r['rows'][0]['controller_visible'].__setitem__('copper',100)))
    cs.append(run('formal_count',lambda r:r.__setitem__('formal_invocation',2)))
    out={'schema':'mindustry_repeat_reset_contract_corruption_v1','controls':cs,'all_rejected':all(x['rejected'] for x in cs)}
    (ROOT/'CORRUPTION.json').write_text(json.dumps(out,indent=2,sort_keys=True)+'\n'); print(json.dumps(out,sort_keys=True))
    raise SystemExit(0 if out['all_rejected'] else 1)
if __name__=='__main__':main()
