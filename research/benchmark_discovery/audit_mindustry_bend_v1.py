"""Replay three engine cases and test invalid direction/window evidence."""
import copy
import hashlib
import json
from pathlib import Path
from mindustry_bend_score_v1 import score

HERE=Path(__file__).resolve().parent;root=HERE/'results/mindustry-bend-01'
read=lambda p:json.loads(p.read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
manifest=read(root/'manifest.json');plan=manifest['plan']
for name,digest in manifest['sources'].items():assert sha(HERE.parent/name)==digest
rows=[]
for case in plan['cases']:
    folder=root/case;r=read(folder/'result.json')
    assert r['ready'] and r['all_owned_processes_exited'] and not r['forced_kill']
    assert sha(folder/'screen.png')==r['screen_sha256']
    before,after=read(folder/'before.json'),read(folder/'after.json')
    result=score(before,after,plan)
    assert result['contract_satisfied'] is plan['expected_success'][case]
    rows.append(dict(case=case,result=result,inputs={n:sha(folder/n) for n in ['before.json','after.json','constructed.json','screen.png']}))
before=read(root/'complete/before.json');after=read(root/'complete/after.json')
controls=[]
for name in ['wrong_direction_positive_delivery','duplicate_direction','missing_direction','nan_window']:
    a,p=copy.deepcopy((after,plan))
    if name=='wrong_direction_positive_delivery':
        next(t for t in a['tiles'] if (t['x'],t['y'])==(139,51))['rotation']=0;expected=False
    elif name=='duplicate_direction':p['rotations'].append(p['rotations'][0]);expected=None
    elif name=='missing_direction':p['rotations'].pop();expected=None
    else:p['simulation_ticks_min']=float('nan');expected=None
    result=score(before,a,p);assert result['contract_satisfied'] is expected
    controls.append(dict(case=name,result=result))
report=dict(passed=True,rows=rows,controls=controls,
    scorer_sha256=sha(HERE/'mindustry_bend_score_v1.py'),audit_sha256=sha(Path(__file__)),
    scope='Engine-authored calibration, not agent construction; scorer created during cohort execution, not a preregistered implementation comparison.')
with (root/'audit.json').open('x') as out:json.dump(report,out,indent=2,allow_nan=False);out.write('\n')
print(json.dumps(dict(passed=True,cases=len(rows),controls=len(controls))))
