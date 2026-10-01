from __future__ import annotations
import json, sys
from pathlib import Path
P=Path(__file__).parent
D=json.loads((P/'fixture_case.json').read_text())
E=[]
ids=set()
for s in D['sessions']:
 t=-1; seen={}
 for e in s['events']:
  if e['id'] in ids:E.append('duplicate-id')
  ids.add(e['id'])
  if e['t_ms']<t:E.append('time-order')
  t=e['t_ms']; seen[e['kind']]=e
  if e['kind'] in {'THREAT_CONTACT','KILL_COUNT_INCREASE','MAP_EXIT'} and e.get('controller_visible') is not False:E.append('scorer-leak')
 if s['arm']=='recovery':
  plan=seen.get('PLAN_ADMITTED'); act=seen.get('ACTUATION_ADMITTED')
  if not plan or not act or (plan['plan_id'],plan['step_id'])!=(act['plan_id'],act['step_id']): E.append('lineage')
  for kind in ('KEY_DOWN_ACK','KEY_UP_ACK','OWNER_EMPTY_RELEASE'):
   if kind not in seen:E.append('release-bracket')
exposed={p:all(any(e['kind']=='THREAT_CONTACT' for e in s['events']) for s in D['sessions'] if s['pair']==p) for p in ('P1','P2','P3')}
if len(D['sessions'])!=6 or any(not x for x in exposed.values()):E.append('denominator-or-exposure')
res={'status':'PASS_INDEPENDENT_RAW_AUDIT' if not E else 'FAIL_INDEPENDENT_RAW_AUDIT','errors':sorted(set(E)),'pairs':sorted(exposed),'sessions':len(D['sessions']),'exposure_by_pair':exposed,'causal_credit':False}
print(json.dumps(res,sort_keys=True)); sys.exit(bool(E))
