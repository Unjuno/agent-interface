from __future__ import annotations
import json, statistics, sys
from pathlib import Path
rows=[json.loads(s) for s in Path(sys.argv[1]).read_text().splitlines() if s.strip()]
errors=[]; paired=[]
for pair in sorted({r['pair'] for r in rows}):
    group=[r for r in rows if r['pair']==pair]
    if len(group)!=2 or {r['arm'] for r in group}!={'control','instrumented'}: errors.append({'pair':pair,'check':'pair_shape'}); continue
    by={r['arm']:r for r in group}
    for arm,r in by.items():
        if r.get('setup_status')!='ok' or not r.get('cleanup',{}).get('game_closed'): errors.append({'pair':pair,'arm':arm,'check':'setup_cleanup'})
        if r.get('passive_read_count',0)<400 or r.get('wall_ns',0)<5_900_000_000: errors.append({'pair':pair,'arm':arm,'check':'window_or_poll_count'})
        api=r.get('api_tic_values',[])
        if not api or min(api)<1 or max(api)>350: errors.append({'pair':pair,'arm':arm,'check':'passive_api_tic_range'})
        if arm=='instrumented' and r.get('engine_entry_count',0)<150: errors.append({'pair':pair,'arm':arm,'check':'instrumented_trace_short'})
        if arm=='control' and r.get('counter_opcode_hits')!=0: errors.append({'pair':pair,'arm':arm,'check':'control_opcode_gate'})
        if arm=='instrumented' and r.get('counter_opcode_hits')!=1: errors.append({'pair':pair,'arm':arm,'check':'instrumented_opcode_gate'})
    if set(by)=={'control','instrumented'}:
        c=by['control']['cpu_wall_ratio']; i=by['instrumented']['cpu_wall_ratio']
        ir=by['instrumented']; viz=ir.get('engine_viz_time_range',[]); wall=ir.get('wall_ns',0)
        derived_rate=(viz[1]-viz[0])*1e9/wall if len(viz)==2 and wall>0 else None
        paired.append({'pair':pair,'control_cpu_wall_ratio':c,'instrumented_cpu_wall_ratio':i,'difference':i-c,
          'relative_cpu_increase':(i-c)/c if c else None,'instrumented_engine_viztime_rate_hz':derived_rate,
          'instrumented_entry_count':ir.get('engine_entry_count'),
          'control_passive_api_tics':by['control'].get('api_tic_values'),
          'instrumented_passive_api_tics':ir.get('api_tic_values')})
deltas=[x['difference'] for x in paired]
out={'schema':'issue3453-construction-clock49-audit-v1','decision':'PASS_CONSTRUCTION_ONLY_CPU_COST_COMPARISON' if len(paired)==4 and not errors else 'HOLD_OR_FAIL','formal_allocation':False,
 'rows':len(rows),'pairs':paired,'median_cpu_wall_difference':statistics.median(deltas) if deltas else None,'errors':errors,
 'limitations':[
 'Process CPU / wall time is a coarse CPU-cost outcome, not a bound on per-tic scheduling perturbation or event timestamp error.',
 'Passive API tic advanced from 1 to 2 in one control session; this makes snapshot progression variable across fresh episodes, and uninstrumented engine tic rate is not independently observed.',
 'Pair00 pilot raw field `engine_entry_hz` used counter ticks as nanoseconds; the audit ignores that mislabeled field and derives an approximate VIZtime delta per measured wall interval from the retained range. Future rows use `engine_viztime_rate_hz`.',
 'Four paired construction pairs do not constitute the frozen 120-row phase allocation.']}
print(json.dumps(out,indent=2,sort_keys=True))
