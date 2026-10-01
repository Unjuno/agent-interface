from __future__ import annotations

from collections import defaultdict
from decimal import Decimal
from pathlib import Path
import json

ROOT=Path(__file__).resolve().parent
FIX=ROOT/'fixture.json'
OUT=ROOT/'RESULT.json'
ARMS=('plain','ephemeral','persistent')
PHASES={1:'acquisition',2:'repeat_A',3:'repeat_A',4:'layout_change',5:'repeat_B',6:'repeat_B'}
COUNT_FIELDS=('input_tokens','cached_input_tokens','output_tokens','reasoning_output_tokens','planner_generations','model_visible_images','local_observations','durable_calls')


def add(dst, src):
    for k in COUNT_FIELDS:
        dst[k]+=int(src[k])
    dst['elapsed_ms']+=Decimal(str(src['elapsed_ms']))


def pack(d):
    return {**{k:int(d[k]) for k in COUNT_FIELDS},'elapsed_ms':format(d['elapsed_ms'],'f')}


def main():
    if OUT.exists():
        raise SystemExit('formal output already exists; rerun forbidden')
    f=json.loads(FIX.read_text())
    exp=f['expected']
    integrity=[]
    arms_out={}
    global_usage={k:0 for k in ('input_tokens','cached_input_tokens','output_tokens','reasoning_output_tokens')}
    model_calls=image_calls=exact_tasks=old_target=0
    for arm in ARMS:
        ad=f['arms'][arm]
        tasks=ad['tasks']
        integrity.append(len(tasks)==6)
        integrity.append([t['task_id'] for t in tasks]==[f'task-{i}' for i in range(1,7)])
        total=defaultdict(int); total['elapsed_ms']=Decimal('0')
        phases={p:defaultdict(int) for p in ('preflight','acquisition','repeat_A','layout_change','repeat_B')}
        for p in phases.values(): p['elapsed_ms']=Decimal('0')
        add(total,ad['preflight']); add(phases['preflight'],ad['preflight'])
        model_calls += int(ad['preflight']['planner_generations'])
        for t in tasks:
            n=int(t['task_id'].split('-')[1])
            add(total,t); add(phases[PHASES[n]],t)
            model_calls += int(t['planner_generations'])
            image_calls += int(t['model_visible_images'])
            exact_tasks += int(bool(t['exact']))
            old_target += int(t['old_target_pointer_admissions'])
        arms_out[arm]={'total':pack(total),'phases':{p:pack(v) for p,v in phases.items()},'routes':[t['route'] for t in tasks]}
        integrity.append(total['input_tokens']==exp['arm_input_tokens'][arm])
        integrity.append(format(total['elapsed_ms'],'f')==exp['phase_complete_elapsed_ms'][arm])
        integrity.append(total['local_observations']==exp['local_observations'][arm])
        integrity.append(total['durable_calls']==exp['durable_calls'][arm])
        for k in global_usage: global_usage[k]+=int(total[k])
    integrity.extend([
        global_usage==exp['global_usage'], model_calls==exp['model_calls'], image_calls==exp['image_grounding_calls'],
        exact_tasks==exp['exact_tasks'], old_target==exp['old_target_pointer_admissions']
    ])
    p=arms_out['persistent']['total']
    reductions={metric:{c:int(p[metric])<int(arms_out[c]['total'][metric]) for c in ('plain','ephemeral')}
                for metric in ('input_tokens','output_tokens','reasoning_output_tokens','planner_generations','model_visible_images')}
    local_tradeoff={metric:{c:int(p[metric])>int(arms_out[c]['total'][metric]) for c in ('plain','ephemeral')}
                    for metric in ('local_observations','durable_calls')}
    if not all(integrity): decision='FAIL_INTEGRITY'
    elif not all(v for m in reductions.values() for v in m.values()): decision='HOLD_INCOMPLETE_PHASE_LEDGER'
    else: decision='PASS_PHASE_LEDGER_RECONSTRUCTED_SCOPED'
    result={
      'schema':'integrated_efficiency_phase_ledger_result_v1','task':f['task'],'base':f['base'],'formal_invocation':1,
      'decision':decision,'source_git_blobs':f['source_git_blobs'],'cached_input_semantics':f['cached_input_semantics'],
      'arm_ledgers':arms_out,'global_usage':global_usage,'model_calls':model_calls,'image_grounding_calls':image_calls,
      'exact_tasks':exact_tasks,'old_target_pointer_admissions':old_target,'persistent_model_side_reduction':reductions,
      'persistent_local_work_increase':local_tradeoff,'integrity_ok':all(integrity),
      'interpretation':["model-side and local-work units are reported separately and are not arithmetically combined",
                        "cached input is a subset diagnostic, not an additive token total",
                        "control-arm repeat_A/repeat_B labels are schedule phases, not claims of warm reuse",
                        "single retained Chromium allocation; no population, human-tempo, monetary-cost or second-domain claim"]}
    OUT.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
    print(json.dumps({'decision':decision,'totals':{a:arms_out[a]['total'] for a in ARMS},'global_usage':global_usage,'model_calls':model_calls,'image_calls':image_calls},indent=2))

if __name__=='__main__': main()
