#!/usr/bin/env python3
import json,sys
from pathlib import Path
R=Path(__file__).resolve().parent
f=json.loads((R/'fixture.json').read_text()); r=json.loads((R/'RESULT.json').read_text())
def cumulative(arm):
    x=arm['preflight_ns']; out=[]
    for value in arm['task_elapsed_ns']: x+=value; out.append(x)
    return out
c={k:cumulative(v) for k,v in f['arms'].items()}; p,q,e=c['persistent'],c['plain'],c['ephemeral']
bp=next((i+1 for i,(a,b) in enumerate(zip(p,q)) if a<b),None)
be=next((i+1 for i,(a,b) in enumerate(zip(p,e)) if a<b),None)
checks={
 'decision':r['decision']=='PASS_CUMULATIVE_WALL_PAYBACK_RECONSTRUCTED_SCOPED',
 'formal':r['formal_invocation']==1 and r['formal_reruns']==0,
 'source':f['sources']['report_json']['git_blob']=='57954e7608f823ec031600a12e0062eeceafdcf4' and f['sources']['preflight_wall_result']['git_blob']=='89e8bc08d4d81f93a496eac83437ad77a06f1214',
 'routes':f['arms']['persistent']['routes']==['cold','reuse','reuse','repair','reuse','reuse'],
 'totals':all(c[n][-1]==f['arms'][n]['expected_final_ns'] for n in c),
 'break_even':bp==r['wall_break_even_vs_plain_task']==2 and be==r['wall_break_even_vs_ephemeral_task']==1,
 'relations':p[0]>q[0] and all(p[i]<q[i] for i in range(1,6)) and all(a<b for a,b in zip(p,e)),
 'rows':all(row['persistent_cumulative_ns']==p[i] and row['plain_cumulative_ns']==q[i] and row['ephemeral_cumulative_ns']==e[i] and row['persistent_route']==f['arms']['persistent']['routes'][i] for i,row in enumerate(r['rows'])),
 'margins':r['task6_margin_vs_plain_ns']==q[-1]-p[-1] and r['task6_margin_vs_ephemeral_ns']==e[-1]-p[-1]
}
out={'schema':'integrated_efficiency_cumulative_wall_payback_audit_v1','passed':all(checks.values()),'checks':checks,'decision':r['decision']}
(R/'AUDIT.json').write_text(json.dumps(out,indent=2,sort_keys=True)+'\n'); print(json.dumps(out,sort_keys=True)); sys.exit(0 if out['passed'] else 1)
