#!/usr/bin/env python3
import json
from copy import deepcopy
import sys
from pathlib import Path
HERE=Path(__file__).resolve().parent
BD=HERE.parents[1]/'benchmark_discovery'
if BD.exists(): sys.path.insert(0,str(BD))
from mindustry_single_tile_score_v1 import score
from contract import canonical_state, positive_after, tile_map, verify_reset, controller_record, no_oracle_leak, run_valid
ROOT=HERE

def read(n): return json.loads((ROOT/n).read_text())
def dump(n,v): (ROOT/n).write_text(json.dumps(v,indent=2,sort_keys=True)+'\n')

def main():
    sentinel=ROOT/'.formal-invoked'
    if sentinel.exists() or (ROOT/'RESULT.json').exists(): raise SystemExit('formal already invoked')
    sentinel.write_text('1\n')
    plan=json.loads(((BD/'mindustry_single_tile_plan_v1.json') if BD.exists() else (ROOT/'plan.json')).read_text()); fixture=read('fixture.json')
    rows=run_valid(plan,fixture)
    base=canonical_state(plan,100,100); reset_canonical=canonical_state(plan,101,100)
    good_reset=deepcopy(reset_canonical); good_reset['tick']=102
    occupied=deepcopy(good_reset); tile_map(occupied)[tuple(plan['target'])]['block']='conveyor'
    collateral=deepcopy(good_reset); tile_map(collateral)[(149,55)]['block']='wall'
    bad_copper=deepcopy(good_reset); bad_copper['copper']=99
    wrong_after=positive_after(base,plan,wrong_rotation=True)
    leak=controller_record(fixture['task_order'][0],plan); leak['evaluation']={'contract_satisfied':True}
    controls={
      'missing_reset': {'reset_ok':False,'next_task_authority':False,'reason':'reset_missing'},
      'target_occupied_reset': verify_reset(reset_canonical,occupied,0,1,plan),
      'collateral_reset': verify_reset(reset_canonical,collateral,0,1,plan),
      'copper_not_restored': verify_reset(reset_canonical,bad_copper,0,1,plan),
      'wrong_rotation_task': score(base,wrong_after,plan),
      'duplicate_epoch': verify_reset(reset_canonical,good_reset,1,1,plan),
      'oracle_leak': {'leak_free':no_oracle_leak(leak,fixture)}
    }
    gates={
      'six_tasks': len(rows)==6,
      'task_scores': len(rows)==6 and all(r['task_evaluation'].get('contract_satisfied') is True for r in rows),
      'resets': len(rows)==6 and all(r['reset'].get('ok') is True for r in rows),
      'order': [r['task_id'] for r in rows]==['A1','A2','A3','B1','B2','B3'] and [r['layout'] for r in rows]==['A','A','A','B','B','B'],
      'no_oracle_leak': len(rows)==6 and all(r['oracle_leak_free'] is True for r in rows),
      'missing_reset_stops': controls['missing_reset']['next_task_authority'] is False,
      'occupied_rejected': controls['target_occupied_reset']['ok'] is False,
      'collateral_rejected': controls['collateral_reset']['ok'] is False,
      'copper_rejected': controls['copper_not_restored']['ok'] is False,
      'wrong_effect_rejected': controls['wrong_rotation_task']['contract_satisfied'] is False,
      'duplicate_epoch_rejected': controls['duplicate_epoch']['ok'] is False,
      'leak_rejected': controls['oracle_leak']['leak_free'] is False
    }
    decision='PASS_MINDUSTRY_REPEAT_RESET_CONTRACT_SCOPED' if all(gates.values()) else 'FAIL_MINDUSTRY_REPEAT_RESET_CONTRACT'
    out={'schema':'mindustry_repeat_reset_contract_result_v1','task':'MINDUSTRY-REPEAT-RESET-CONTRACT-20260917-001',
         'formal_invocation':1,'formal_reruns':0,'decision':decision,'gates':gates,'rows':rows,'controls':controls,
         'scope':'deterministic benchmark reset/scoring contract only; no live Mindustry/model/token/latency claim'}
    dump('RESULT.json',out); print(json.dumps({'decision':decision,'gates':gates},sort_keys=True))
    raise SystemExit(0 if all(gates.values()) else 1)
if __name__=='__main__': main()
