#!/usr/bin/env python3
import json
from decimal import Decimal
from pathlib import Path
R=Path(__file__).resolve().parent; f=json.loads((R/'fixture.json').read_text(),parse_float=Decimal); rows=f['rows']; ret=f['retained']; errors=[]
arms={}
for name in ('plain','ephemeral','persistent'):
    rs=[r for r in rows if r['arm']==name]
    arms[name]={k:sum(r[k] for r in rs) for k in ['input','cached','output','reasoning','generations','images','local_observations','durable_calls','elapsed_ms']}
if {a:arms[a]['input'] for a in arms}!=ret['arm_input']: errors.append('arm_input')
G={k:sum(arms[a][k] for a in arms) for k in ('input','cached','output','reasoning')}
if G!=ret['global']: errors.append('global')
for a,v in ret['phase_complete_elapsed_ms'].items():
    if arms[a]['elapsed_ms']!=v: errors.append('elapsed:'+a)
phase={}
for a in arms:
    for p in ('preflight','acquisition','repeated_A','invalidation_repair','repeated_B'):
        rs=[r for r in rows if r['arm']==a and r['phase']==p]
        phase[a+'::'+p]={k:sum(r[k] for r in rs) for k in ('input','output','reasoning','generations','images','local_observations','durable_calls','elapsed_ms')}
out={'schema':'phase-ledger-independent-verifier-v1','pass':not errors,'errors':errors,'arm_totals':arms,'phase_totals':phase}
(R/'VERIFY.json').write_text(json.dumps(out,indent=2,sort_keys=True,default=str)+'\n'); print(json.dumps({'pass':not errors,'errors':errors}))
