#!/usr/bin/env python3
import json,shutil,subprocess,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parent

def run(name,mut):
    with tempfile.TemporaryDirectory() as td:
        d=Path(td)/'x';shutil.copytree(ROOT,d,ignore=shutil.ignore_patterns('.formal-invoked','AUDIT.json','CORRUPTION.json','__pycache__'));p=d/'RESULT.json';r=json.loads(p.read_text());mut(r);p.write_text(json.dumps(r,indent=2,sort_keys=True)+'\n');q=subprocess.run(['python3',str(d/'audit.py'),str(d)],capture_output=True,text=True);return {'name':name,'rejected':q.returncode!=0,'returncode':q.returncode}
def main():
    cs=[]
    cs.append(run('reset_before_score',lambda r:r['events'].insert(2,{'event':'reset_witness','epoch':1})))
    cs.append(run('control_plane_leak',lambda r:r['controller_projection'].append({'event':'reset_witness','epoch':1})))
    cs.append(run('geometry_removed',lambda r:r.__setitem__('events',[x for x in r['events'] if x.get('event')!='geometry_mutation'])))
    cs.append(run('formal_count',lambda r:r.__setitem__('formal_invocation',2)))
    out={'schema':'mindustry_repeat_fixture_protocol_corruption_v1','controls':cs,'all_rejected':all(x['rejected'] for x in cs)};(ROOT/'CORRUPTION.json').write_text(json.dumps(out,indent=2,sort_keys=True)+'\n');print(json.dumps(out,sort_keys=True));raise SystemExit(0 if out['all_rejected'] else 1)
if __name__=='__main__':main()
