#!/usr/bin/env python3
import json,math
from pathlib import Path
R=Path(__file__).resolve().parent; f=json.loads((R/'fixture.json').read_text()); z=json.loads((R/'RESULT.json').read_text()); errors=[]
ret=f['retained']; a=z['arm_totals']
for arm,want in ret['arm_input'].items():
    if a[arm]['input']!=want: errors.append('arm_input:'+arm)
g={k:sum(a[x][k] for x in a) for k in ('input','cached','output','reasoning')}
if g!=ret['global']: errors.append('global_usage')
for arm,want in ret['phase_complete_elapsed_ms'].items():
    if not math.isclose(a[arm]['elapsed_ms'],want,abs_tol=1e-9): errors.append('elapsed:'+arm)
if sum(a[x]['generations'] for x in a)!=ret['all_model_calls']: errors.append('generations')
if sum(1 for r in f['rows'] if r['phase']=='preflight')!=ret['fresh_preflight_calls']: errors.append('preflight_count')
if sum(r['images'] for r in f['rows'])!=ret['image_grounding_calls']: errors.append('images')
if len([r for r in f['rows'] if r['task']!='preflight'])!=ret['exact_tasks']: errors.append('task_rows')
p=a['persistent']
for m in ('input','output','reasoning','generations','images'):
    if not (p[m] < a['plain'][m] and p[m] < a['ephemeral'][m]): errors.append('persistent_not_lower:'+m)
if not (p['local_observations']>a['plain']['local_observations'] and p['durable_calls']>a['plain']['durable_calls']): errors.append('local_tradeoff_missing')
res={'schema':'phase-ledger-audit-v1','decision':'PASS_PHASE_LEDGER_RECONSTRUCTED_SCOPED' if not errors else 'FAIL_INTEGRITY','errors':errors,'global_usage':g,'persistent_local_tradeoff':{'local_observations':p['local_observations'],'plain_local_observations':a['plain']['local_observations'],'durable_calls':p['durable_calls'],'plain_durable_calls':a['plain']['durable_calls']}}
(R/'AUDIT.json').write_text(json.dumps(res,indent=2,sort_keys=True)+'\n'); print(json.dumps(res,sort_keys=True))
