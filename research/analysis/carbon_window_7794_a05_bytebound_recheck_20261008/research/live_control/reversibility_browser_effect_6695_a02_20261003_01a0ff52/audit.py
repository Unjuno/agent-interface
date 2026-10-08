"""Independent raw-only reconstruction; imports neither controller nor application."""
import argparse,collections,json,pathlib

def check(specs,truth,servers,controllers):
 errors=[];rows=[]
 try:
  assert type(specs) is list and type(truth) is dict and type(servers) is list and type(controllers) is list
  sm={s['case_id']:s for s in specs};expected={k+'_'+p.lower() for k in sm for p in ('STAGE','WAIT')}
  assert len(sm)==len(specs) and set(truth)==set(sm) and all(v in ('A','B') for v in truth.values())
  assert len(servers)==len(controllers)==len(expected)
  sr={x['trial_id']:x for x in servers};cr={x['trial_id']:x for x in controllers}
  assert set(sr)==set(cr)==expected
 except (AssertionError,KeyError,TypeError) as e:return dict(errors=['coverage/schema:'+str(e)],rows=[],counts={'STAGE':{},'WAIT':{}})
 for trial_id in sorted(expected):
  try:
   c=cr[trial_id];r=sr[trial_id];case=c['case_id'];spec=sm[case];policy=c['policy']
   assert set(c)=={'trial_id','case_id','policy','status','signal','error','blocked_external_requests'}
   assert policy in ('STAGE','WAIT') and trial_id==case+'_'+policy.lower()
   assert c['error'] is None and type(c['blocked_external_requests']) is int and c['blocked_external_requests']==0
   assert set(r)=={'trial_id','events','effects'} and type(r['events']) is list and type(r['effects']) is list
   events=r['events'];assert all(type(e) is dict and type(e.get('ns')) is int and e['ns']>=0 for e in events)
   assert [e['ns'] for e in events]==sorted(e['ns'] for e in events)
   by=collections.defaultdict(list)
   schemas={'start':{'event','ns'},'signal':{'event','ns','value'},'prepare_start':{'event','ns','target'},
    'prepare_end':{'event','ns','target'},'edit_start':{'event','ns','target'},'edit_end':{'event','ns','target'},
    'commit':{'event','ns','target','status'}}
   for e in events:assert e['event'] in schemas and set(e)==schemas[e['event']];by[e['event']].append(e)
   assert all(len(by[k])==1 for k in ('start','signal','prepare_start','prepare_end','commit'))
   assert events[0]=={'event':'start','ns':0} and events[-1]['event']=='commit'
   sig,ps,pe,commit=(by[k][0] for k in ('signal','prepare_start','prepare_end','commit'))
   assert sig['value']==c['signal']==spec['signal'] and sig['ns']>=spec['signal_ms']*1_000_000
   target='B' if spec['signal']=='B' else 'A'
   prepared=target if policy=='WAIT' else 'A'
   assert ps['target']==pe['target']==prepared and pe['ns']-ps['ns']>=spec['preparation_ms']*1_000_000
   if policy=='WAIT':assert ps['ns']>=sig['ns']
   else:assert ps['ns']<sig['ns'] or spec['signal_ms']==0
   edits=policy=='STAGE' and target=='B'
   assert len(by['edit_start'])==len(by['edit_end'])==int(edits)
   ready=pe['ns']
   if edits:
    es,ee=by['edit_start'][0],by['edit_end'][0]
    assert es['target']==ee['target']=='B' and es['ns']>=max(sig['ns'],pe['ns'])
    assert ee['ns']-es['ns']>=spec['edit_ms']*1_000_000;ready=ee['ns']
   assert commit['ns']>=max(ready,sig['ns']) and commit['target']==target
   deadline=spec['deadline_ms']*1_000_000
   status='committed' if commit['ns']<=deadline else 'deadline'
   assert commit['status']==status and c['status']==status.upper()
   for effect in r['effects']:
    assert type(effect) is dict and set(effect)=={'ns','target'} and type(effect['ns']) is int
   assert r['effects']==([{'ns':commit['ns'],'target':target}] if status=='committed' else [])
   outcome='deadline' if status=='deadline' else 'correct' if target==truth[case] else 'wrong'
   rows.append(dict(trial_id=trial_id,case_id=case,policy=policy,outcome=outcome,
    ready_ns=ready,commit_ns=commit['ns'],preparation_ns=pe['ns']-ps['ns'],
    edit_ns=by['edit_end'][0]['ns']-by['edit_start'][0]['ns'] if edits else 0,signal_ns=sig['ns']))
  except (AssertionError,KeyError,TypeError,IndexError) as e:errors.append(trial_id+':'+str(e))
 counts={p:dict(collections.Counter(r['outcome'] for r in rows if r['policy']==p)) for p in ('STAGE','WAIT')}
 return dict(errors=errors,rows=rows,counts=counts)

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('spec',type=pathlib.Path);p.add_argument('truth',type=pathlib.Path)
 p.add_argument('run',type=pathlib.Path);p.add_argument('output',type=pathlib.Path);a=p.parse_args()
 result=check(json.loads(a.spec.read_text()),json.loads(a.truth.read_text()),
  [json.loads(x) for x in (a.run/'server.jsonl').read_text().splitlines()],
  [json.loads(x) for x in (a.run/'controller.jsonl').read_text().splitlines()])
 lookup={(r['case_id'],r['policy']):r['outcome'] for r in result['rows']}
 result['status']='HOLD_METHOD' if result['errors'] else 'PASS_METHOD_SCOPED'
 result['directional_gate']=all(lookup.get(k)==v for k,v in {
  ('c00','STAGE'):'correct',('c00','WAIT'):'deadline',('c01','STAGE'):'deadline',('c01','WAIT'):'correct'}.items())
 result['H_status']='HOLD' if result['errors'] else 'H_PASS_SCOPED' if result['directional_gate'] else 'H_FAIL_SCOPED'
 with a.output.open('x') as f:json.dump(result,f,indent=2,sort_keys=True);f.write('\n')
 print(json.dumps({'status':result['status'],'H_status':result['H_status'],'rows':len(result['rows']),'errors':result['errors'],'counts':result['counts']}))
 raise SystemExit(bool(result['errors']))
