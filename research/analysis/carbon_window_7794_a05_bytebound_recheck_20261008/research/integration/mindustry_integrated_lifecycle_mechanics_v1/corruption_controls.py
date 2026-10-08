from __future__ import annotations
import json,shutil,subprocess,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parent

def run(name, mutate):
    with tempfile.TemporaryDirectory() as td:
        d=Path(td)/'x'; shutil.copytree(ROOT,d,ignore=shutil.ignore_patterns('AUDIT.json','CORRUPTION.json','__pycache__'))
        p=d/'RESULT.json'; j=json.loads(p.read_text()); mutate(j); p.write_text(json.dumps(j,indent=2,sort_keys=True)+'\n')
        q=subprocess.run(['python3',str(d/'audit.py')],cwd=d,capture_output=True,text=True)
        return {'name':name,'rejected':q.returncode!=0,'returncode':q.returncode}

def main():
    cases=[]
    cases.append(run('stale_escape',lambda j: j['controls']['stale_W1_after_repair'].update(status='EFFECT_VERIFIED',effect_id='forged')))
    cases.append(run('palette_mutated',lambda j: j['valid_trace'][4]['versions_after'].__setitem__('palette','P2')))
    cases.append(run('extra_reuse_generation',lambda j: j['valid_trace'][5].__setitem__('logical_generation_charge',1)))
    cases.append(run('duplicate_second_effect',lambda j: j['controls']['duplicate_effect_replay'].update(status='EFFECT_VERIFIED',effect_id='second')))
    out={'schema':'mindustry_integrated_lifecycle_mechanics_corruption_v1','controls':cases,'all_rejected':all(x['rejected'] for x in cases)}
    (ROOT/'CORRUPTION.json').write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
    print(json.dumps(out,indent=2)); raise SystemExit(0 if out['all_rejected'] else 1)
if __name__=='__main__': main()
