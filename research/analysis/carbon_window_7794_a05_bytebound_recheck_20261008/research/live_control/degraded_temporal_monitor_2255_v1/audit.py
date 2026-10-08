#!/usr/bin/env python3
import hashlib, json, pathlib, sys
SCENARIOS=['AB_WITHIN','AB_LATE','A_ONLY','CANCEL_COMPLETE','CANCEL_DROP_DECLARED','CANCEL_DROP_UNDECLARED','REORDER_DECLARED','CROSS_CLOCK_DECLARED']

def sem(events):
 pending=None
 for e in events:
  if e['phase']=='A': pending=(e['epoch'],e['server_ms'])
  elif e['phase']=='CANCEL' and pending and pending[0]==e['epoch']: pending=None
  elif e['phase']=='B' and pending and pending[0]==e['epoch']:
   dt=(e['server_ms']-pending[1]) & 0xffffffff
   return 'SATISFIED' if dt<=80 else 'NOT_SATISFIED'
 return 'NOT_SATISFIED'

def expected_packet(sc,raw):
 ev=[dict(x) for x in raw]; cov=ordc=clk=True
 if sc in {'CANCEL_DROP_DECLARED','CANCEL_DROP_UNDECLARED'}:
  ev=[x for x in ev if x['phase']!='CANCEL']; cov=sc!='CANCEL_DROP_DECLARED'
 elif sc=='REORDER_DECLARED': ev=list(reversed(ev)); ordc=False
 elif sc=='CROSS_CLOCK_DECLARED':
  for x in ev:
   if x['phase']=='B': x['clock_domain']='foreign-clock'
  clk=False
 return {'events':ev,'coverage_complete':cov,'order_complete':ordc,'clock_coherent':clk,'scope':'title-contract-v1'}

def validate(root,study):
 errors=[]; checks=0
 run=json.loads((root/'RUN.json').read_text()); checks+=1
 if len(run.get('cases',[]))!=16: errors.append('denominator')
 freeze=json.loads((study/'FREEZE.json').read_text())
 for name,want in freeze['sources'].items():
  p=study/name; checks+=1
  if hashlib.sha256(p.read_bytes()).hexdigest()!=want: errors.append('source:'+name)
 counts={'NAIVE_COMPILED':{},'FAIL_CLOSED':{}}; false_sat_undeclared=0; candidate_unknown_declared=0; candidate_false_sat_declared=0
 for row in run.get('cases',[]):
  sc=row['scenario']; checks+=10
  if sc not in SCENARIOS: errors.append('scenario')
  if row.get('app_exit')!=0 or row.get('observer_exit')!=0 or row.get('xvfb_exit')!=0: errors.append('exit:'+sc+str(row.get('rep')))
  if len(row['raw_events']) != len([x for x in row['commands']]): errors.append('event_count:'+sc)
  packet=expected_packet(sc,row['raw_events'])
  if row['delivery_packet']!=packet: errors.append('packet:'+sc)
  oracle=sem(row['raw_events'])
  if row['oracle']['status']!=oracle: errors.append('oracle:'+sc)
  pol={p['mode']:p['decision'] for p in row['policies']}
  for mode,d in pol.items(): counts[mode][d['status']]=counts[mode].get(d['status'],0)+1
  # Independent expected candidate gate.
  if not packet['coverage_complete']: want='UNKNOWN'
  elif not packet['order_complete']: want='UNKNOWN'
  elif not packet['clock_coherent']: want='UNKNOWN'
  else: want=sem(packet['events'])
  if pol['FAIL_CLOSED']['status']!=want: errors.append('candidate:'+sc)
  if pol['NAIVE_COMPILED']['status']!=sem(packet['events']): errors.append('naive:'+sc)
  if sc in {'CANCEL_DROP_DECLARED','REORDER_DECLARED','CROSS_CLOCK_DECLARED'}:
   if pol['FAIL_CLOSED']['status']=='UNKNOWN': candidate_unknown_declared+=1
   if pol['FAIL_CLOSED']['status']=='SATISFIED' and oracle!='SATISFIED': candidate_false_sat_declared+=1
  if sc=='CANCEL_DROP_UNDECLARED' and pol['FAIL_CLOSED']['status']=='SATISFIED' and oracle!='SATISFIED': false_sat_undeclared+=1
  last=row['commands'][-1]['cmd']; expected_text=f"{last['epoch']}:{last['phase']}:{last.get('tag',0)}"
  if row['snapshot']['text']!=expected_text or row['snapshot']['title']!=expected_text: errors.append('effect:'+sc)
 if candidate_unknown_declared!=6: errors.append('declared_unknown_count')
 if candidate_false_sat_declared!=0: errors.append('declared_false_sat')
 if false_sat_undeclared!=2: errors.append('undeclared_limit_not_exposed')
 decision='PASS_DECLARED_DEGRADATION_FAIL_CLOSED_SCOPED' if not errors else 'FAIL_AUDIT'
 return {'decision':decision,'cases':len(run.get('cases',[])),'checks':checks,'errors':errors,'candidate_unknown_declared':candidate_unknown_declared,'undeclared_false_satisfied':false_sat_undeclared,'counts':counts,'formal_reruns':run.get('formal_reruns')}
if __name__=='__main__':
 root=pathlib.Path(sys.argv[1]); study=pathlib.Path(sys.argv[2])
 print(json.dumps(validate(root,study),indent=2,sort_keys=True))
 raise SystemExit(0 if validate(root,study)['errors']==[] else 1)
