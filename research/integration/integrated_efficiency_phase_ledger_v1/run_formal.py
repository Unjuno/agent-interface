#!/usr/bin/env python3
import json
from collections import defaultdict
from pathlib import Path
R=Path(__file__).resolve().parent
out=R/'RESULT.json'
if out.exists(): raise SystemExit('REFUSE_RERUN')
f=json.loads((R/'fixture.json').read_text()); rows=f['rows']; metrics=['input','cached','output','reasoning','generations','images','local_observations','durable_calls','elapsed_ms']
def zero(): return {k:0 for k in metrics}
arm=defaultdict(zero); phase=defaultdict(zero)
for r in rows:
    for k in metrics:
        arm[r['arm']][k]+=r[k]; phase[(r['arm'],r['phase'])][k]+=r[k]
result={'schema':'integrated-efficiency-phase-ledger-result-v1','formal_invocations':1,'formal_reruns':0,'source_blobs':f['source_blobs'],'row_count':len(rows),'arm_totals':dict(arm),'phase_totals':{a+'::'+p:v for (a,p),v in phase.items()},'persistent_routes':{r['task']:r['route'] for r in rows if r['arm']=='persistent' and r['task']!='preflight'}}
out.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n'); print(json.dumps({'rows':len(rows),'arms':list(arm)}))
