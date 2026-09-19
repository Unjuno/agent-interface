from __future__ import annotations

from decimal import Decimal
from pathlib import Path
import hashlib,json
ROOT=Path(__file__).resolve().parent
ARMS=('plain','ephemeral','persistent')
PHASES={1:'acquisition',2:'repeat_A',3:'repeat_A',4:'layout_change',5:'repeat_B',6:'repeat_B'}
FIELDS=('input_tokens','cached_input_tokens','output_tokens','reasoning_output_tokens','planner_generations','model_visible_images','local_observations','durable_calls')

def main():
    f=json.loads((ROOT/'fixture.json').read_text()); r=json.loads((ROOT/'RESULT.json').read_text())
    checks={}
    global_usage={k:0 for k in FIELDS[:4]}; calls=images=exact=old=0
    for arm in ARMS:
        rows=[f['arms'][arm]['preflight']]+f['arms'][arm]['tasks']
        totals={k:sum(int(x[k]) for x in rows) for k in FIELDS}
        elapsed=sum(Decimal(str(x['elapsed_ms'])) for x in rows)
        got=r['arm_ledgers'][arm]['total']
        checks[f'{arm}_total_counts']=all(int(got[k])==totals[k] for k in FIELDS)
        checks[f'{arm}_total_elapsed']=got['elapsed_ms']==format(elapsed,'f')
        checks[f'{arm}_input_expected']=totals['input_tokens']==f['expected']['arm_input_tokens'][arm]
        checks[f'{arm}_local_expected']=totals['local_observations']==f['expected']['local_observations'][arm] and totals['durable_calls']==f['expected']['durable_calls'][arm]
        for k in global_usage: global_usage[k]+=totals[k]
        calls+=totals['planner_generations']; images+=totals['model_visible_images']
        exact+=sum(int(t['exact']) for t in f['arms'][arm]['tasks'])
        old+=sum(int(t['old_target_pointer_admissions']) for t in f['arms'][arm]['tasks'])
        for phase in ('preflight','acquisition','repeat_A','layout_change','repeat_B'):
            if phase=='preflight': selected=[f['arms'][arm]['preflight']]
            else: selected=[t for t in f['arms'][arm]['tasks'] if PHASES[int(t['task_id'].split('-')[1])]==phase]
            expected={k:sum(int(x[k]) for x in selected) for k in FIELDS}
            expected_elapsed=sum(Decimal(str(x['elapsed_ms'])) for x in selected)
            gp=r['arm_ledgers'][arm]['phases'][phase]
            checks[f'{arm}_{phase}_exact']=all(int(gp[k])==expected[k] for k in FIELDS) and gp['elapsed_ms']==format(expected_elapsed,'f')
    checks['global_usage']=global_usage==f['expected']['global_usage']==r['global_usage']
    checks['global_counts']=calls==f['expected']['model_calls']==r['model_calls'] and images==f['expected']['image_grounding_calls']==r['image_grounding_calls'] and exact==18==r['exact_tasks'] and old==0==r['old_target_pointer_admissions']
    p=r['arm_ledgers']['persistent']['total']
    checks['persistent_model_side_lower']=all(int(p[m])<int(r['arm_ledgers'][c]['total'][m]) for m in ('input_tokens','output_tokens','reasoning_output_tokens','planner_generations','model_visible_images') for c in ('plain','ephemeral'))
    checks['local_tradeoff_visible']=all(int(p[m])>int(r['arm_ledgers'][c]['total'][m]) for m in ('local_observations','durable_calls') for c in ('plain','ephemeral'))
    checks['decision']=r['decision']=='PASS_PHASE_LEDGER_RECONSTRUCTED_SCOPED'
    passed=all(checks.values())
    out={'schema':'integrated_efficiency_phase_ledger_audit_v1','passed':passed,'checks':checks,'result_sha256':hashlib.sha256((ROOT/'RESULT.json').read_bytes()).hexdigest()}
    (ROOT/'AUDIT.json').write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
    print(json.dumps({'passed':passed,'failed':[k for k,v in checks.items() if not v]},indent=2))
    if not passed: raise SystemExit(1)
if __name__=='__main__': main()
