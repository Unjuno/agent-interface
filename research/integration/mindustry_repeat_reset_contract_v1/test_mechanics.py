import json
from copy import deepcopy
import sys
from pathlib import Path
HERE=Path(__file__).resolve().parent
BD=HERE.parents[1]/'benchmark_discovery'
if BD.exists(): sys.path.insert(0,str(BD))
from mindustry_single_tile_score_v1 import score
from contract import *
root=HERE
plan_path=(BD/'mindustry_single_tile_plan_v1.json') if BD.exists() else (root/'plan.json')
plan=json.loads(plan_path.read_text()); fixture=json.loads((root/'fixture.json').read_text())
rows=run_valid(plan,fixture)
assert len(rows)==6 and all(r['task_evaluation']['contract_satisfied'] is True for r in rows)
assert all(r['reset']['ok'] is True and r['oracle_leak_free'] for r in rows)
assert [r['layout'] for r in rows]==['A','A','A','B','B','B']
b=canonical_state(plan); bad=positive_after(b,plan,wrong_rotation=True)
assert score(b,bad,plan)['contract_satisfied'] is False
c=canonical_state(plan,101); r=deepcopy(c); r['tick']=102
assert verify_reset(c,r,0,1,plan)['ok']
r2=deepcopy(r); tile_map(r2)[tuple(plan['target'])]['block']='conveyor'
assert verify_reset(c,r2,0,1,plan)['reason']=='target_not_empty'
r3=deepcopy(r); tile_map(r3)[(149,55)]['block']='wall'
assert verify_reset(c,r3,0,1,plan)['reason']=='guard_not_canonical'
r4=deepcopy(r); r4['copper']=99
assert verify_reset(c,r4,0,1,plan)['reason']=='state_not_canonical:copper'
assert verify_reset(c,r,1,1,plan)['reason']=='non_monotonic_epoch'
leak=controller_record(fixture['task_order'][0],plan); leak['copper']=100
assert not no_oracle_leak(leak,fixture)
print('PASS mechanics')
