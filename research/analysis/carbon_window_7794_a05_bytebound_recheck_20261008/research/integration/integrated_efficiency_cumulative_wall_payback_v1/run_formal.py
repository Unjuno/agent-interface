#!/usr/bin/env python3
import json
from pathlib import Path
R=Path(__file__).resolve().parent

def read(): return json.loads((R/'fixture.json').read_text())
def dump(name,x): (R/name).write_text(json.dumps(x,indent=2,sort_keys=True)+'\n')

def cumulative(arm):
    x=arm['preflight_ns']; out=[]
    for value in arm['task_elapsed_ns']:
        x += value; out.append(x)
    return out

def main():
    sentinel=R/'.formal-invoked'
    if sentinel.exists() or (R/'RESULT.json').exists(): raise SystemExit('formal already invoked')
    sentinel.write_text('1\n')
    f=read(); arms=f['arms']
    cumulative_ns={name:cumulative(arm) for name,arm in arms.items()}
    for name,arm in arms.items():
        if cumulative_ns[name][-1] != arm['expected_final_ns']:
            raise SystemExit('final total mismatch '+name)
    p=cumulative_ns['persistent']; q=cumulative_ns['plain']; e=cumulative_ns['ephemeral']
    break_plain=next((i+1 for i,(a,b) in enumerate(zip(p,q)) if a < b),None)
    break_ephemeral=next((i+1 for i,(a,b) in enumerate(zip(p,e)) if a < b),None)
    delta_plain=[a-b for a,b in zip(p,q)]
    delta_ephemeral=[a-b for a,b in zip(p,e)]
    gates={
      'source_identities_declared': f['sources']['report_json']['git_blob']=='57954e7608f823ec031600a12e0062eeceafdcf4' and f['sources']['preflight_wall_result']['git_blob']=='89e8bc08d4d81f93a496eac83437ad77a06f1214',
      'six_tasks_each': all(len(a['task_elapsed_ns'])==6 and len(a['routes'])==6 for a in arms.values()),
      'persistent_route_order': arms['persistent']['routes']==['cold','reuse','reuse','repair','reuse','reuse'],
      'final_totals_exact': all(cumulative_ns[n][-1]==arms[n]['expected_final_ns'] for n in arms),
      'persistent_slower_plain_task1': p[0] > q[0],
      'persistent_faster_plain_task2': p[1] < q[1],
      'persistent_faster_plain_after_repair': p[3] < q[3],
      'persistent_faster_plain_through_task6': all(p[i] < q[i] for i in range(1,6)),
      'persistent_faster_ephemeral_all_tasks': all(a < b for a,b in zip(p,e)),
      'wall_break_even_plain_task2': break_plain==2,
      'token_break_even_retained_task2': f['retained_token_break_even_task']==2
    }
    decision='PASS_CUMULATIVE_WALL_PAYBACK_RECONSTRUCTED_SCOPED' if all(gates.values()) else 'FAIL_PAYBACK_CLAIM'
    rows=[]
    for i in range(6):
        rows.append({
          'task':i+1,
          'persistent_route':arms['persistent']['routes'][i],
          'plain_cumulative_ns':q[i], 'ephemeral_cumulative_ns':e[i], 'persistent_cumulative_ns':p[i],
          'persistent_minus_plain_ns':delta_plain[i], 'persistent_minus_ephemeral_ns':delta_ephemeral[i]
        })
    out={
      'schema':'integrated_efficiency_cumulative_wall_payback_result_v1',
      'task':f['task'],'formal_invocation':1,'formal_reruns':0,'decision':decision,
      'wall_break_even_vs_plain_task':break_plain,'wall_break_even_vs_ephemeral_task':break_ephemeral,
      'retained_token_break_even_task':f['retained_token_break_even_task'],
      'rows':rows,'gates':gates,
      'task6_margin_vs_plain_ns':q[-1]-p[-1],
      'task6_margin_vs_ephemeral_ns':e[-1]-p[-1],
      'scope':'posthoc retained-allocation cumulative wall accounting only; no new live/model/GUI or general speed claim'
    }
    dump('RESULT.json',out)
    print(json.dumps({'decision':decision,'wall_break_even_vs_plain_task':break_plain,'task6_margin_vs_plain_ns':out['task6_margin_vs_plain_ns']},sort_keys=True))
    raise SystemExit(0 if all(gates.values()) else 1)
if __name__=='__main__': main()
