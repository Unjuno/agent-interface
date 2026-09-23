import json
from pathlib import Path
OUT=Path(__file__).resolve().parent
interface={
 'predicates':['field_pixels_changed','field_target_present','submit_target_present','submission_pixels_changed'],
 'symbols':{
   'value_field': {'deps':['field_target_present','field_pixels_changed']},
   'submit_control': {'deps':['submit_target_present','field_pixels_changed']},
 },
 'actions':{
   'enter_token': {'symbol':'value_field','expected':{'field_pixels_changed':True}},
   'submit_form': {'symbol':'submit_control','expected':{'submission_pixels_changed':True}},
 },
 'states':{
   'empty': {'when':{'field_pixels_changed':False,'field_target_present':True},'action':'enter_token','next':'filled'},
   'filled': {'when':{'field_pixels_changed':True,'submit_target_present':True},'action':'submit_form','next':'submitted'},
   'submitted': {'when':{'submission_pixels_changed':True},'action':None,'next':None},
 }
}
positive=[
 {'state':'empty','sequence':12,'digest':'d53d94f380ee0893bf459ee416f46d296d80f381b244301799d88f1210c3dbd9','ref':'runtime/012.png','predicates':{'field_pixels_changed':False,'field_target_present':True,'submit_target_present':False,'submission_pixels_changed':'unknown'}},
 {'state':'filled','sequence':19,'digest':'b2d710b5cb6778196b041e2606707e99f72c869411415a252384cb0c6cff01f5','ref':'runtime/015.png','predicates':{'field_pixels_changed':True,'field_target_present':False,'submit_target_present':True,'submission_pixels_changed':'unknown'}},
 {'state':'submitted','sequence':24,'digest':'af6c143fb60fa1079562cebb516b7934b0963a0bbcb94264bbb8a41edf335f86','ref':'runtime/021.png','predicates':{'field_pixels_changed':True,'field_target_present':False,'submit_target_present':False,'submission_pixels_changed':True}},
]
changed=[
 {'state':'empty','sequence':11,'digest':'59a5aafd8766f57844abd2ebac9e940b5f9d566f4574e16e5eb0c3a2c4de9c5b','ref':'runtime/010.png','predicates':{'field_pixels_changed':False,'field_target_present':True,'submit_target_present':False,'submission_pixels_changed':'unknown'}},
 {'state':'filled','sequence':24,'digest':'e8604b0d5a3ebd996896b24bb850d83510cf21c9d9b3e6bea257d5accaddaca9','ref':'runtime/021.png','predicates':{'field_pixels_changed':True,'field_target_present':False,'submit_target_present':False,'submission_pixels_changed':'unknown'}},
]
def required(state,pending=None):
    spec=interface['states'][state]; keys=set(spec['when'])
    if spec['action']:
        action=interface['actions'][spec['action']]; keys.update(interface['symbols'][action['symbol']]['deps'])
    if pending: keys.update(pending['expected'])
    return sorted(keys)
def project(obs,state,pending=None,omit=None):
    keys=required(state,pending)
    if omit in keys: keys.remove(omit)
    return {**obs,'predicates':{k:obs['predicates'][k] for k in keys if k in obs['predicates']},'required':keys}
def replay(observations,mode='full',omit_by_state=None):
    state='empty'; pending=None; prev_digest=None; transitions=0; events=[]; sizes=[]
    for raw in observations:
        assert raw['state']==state
        obs={**raw,'required':interface['predicates']} if mode=='full' else project(raw,state,pending,(omit_by_state or {}).get(state))
        sizes.append(len(json.dumps(obs['predicates'],sort_keys=True,separators=(',',':'))))
        if pending is not None:
            if obs['digest']==prev_digest:return {'outcome':'SAFE_YIELD','reason':'no_progress','transitions':transitions,'events':events,'sizes':sizes}
            expected=pending['expected']; p=obs['predicates']
            unknown=any(k not in p or p.get(k)=='unknown' for k in expected); mismatch=any(p.get(k)!=v for k,v in expected.items())
            if unknown or mismatch:return {'outcome':'SAFE_YIELD','reason':'effect_unavailable' if unknown else 'effect_failed','transitions':transitions,'events':events,'sizes':sizes}
            events.append(['effect_succeeded',pending['action'],obs['sequence']]); pending=None
        spec=interface['states'][state]; p=obs['predicates']
        if not all(p.get(k)==v for k,v in spec['when'].items()):return {'outcome':'SAFE_YIELD','reason':'unknown_state','transitions':transitions,'events':events,'sizes':sizes}
        if spec['action'] is None:return {'outcome':'TASK_SUCCEEDED','reason':'method_complete','transitions':transitions,'events':events,'sizes':sizes}
        action=interface['actions'][spec['action']]; deps=interface['symbols'][action['symbol']]['deps']
        if any(k not in p for k in deps):return {'outcome':'SAFE_YIELD','reason':'authority_unavailable','transitions':transitions,'events':events,'sizes':sizes}
        events.append(['action',spec['action'],obs['sequence']]); transitions+=1; pending={'action':spec['action'],'expected':action['expected']}; prev_digest=obs['digest']; state=spec['next']
    return {'outcome':'INCOMPLETE','reason':'trace_exhausted','transitions':transitions,'events':events,'sizes':sizes}
results={}
for name,trace in [('positive',positive),('changed',changed)]:
    results[name]={m:replay(trace,m) for m in ('full','scoped')}
    assert {k:results[name]['full'][k] for k in ('outcome','reason','transitions','events')}=={k:results[name]['scoped'][k] for k in ('outcome','reason','transitions','events')}
omits=[]
for state in ('empty','filled','submitted'):
    pend={'action':'enter_token','expected':{'field_pixels_changed':True}} if state=='filled' else {'action':'submit_form','expected':{'submission_pixels_changed':True}} if state=='submitted' else None
    for k in required(state,pend):
        r=replay(positive,'scoped',{state:k}); base=results['positive']['scoped']
        omits.append({'state':state,'omitted':k,'outcome':r['outcome'],'reason':r['reason'],'changed_from_baseline':(r['outcome'],r['reason'],r['transitions'])!=(base['outcome'],base['reason'],base['transitions'])})
assert all(x['changed_from_baseline'] for x in omits)
def norm_size(obs,preds):
    x={'sequence':obs['sequence'],'surface':'chromium-private-form','predicates':preds,'evidence_ref':obs['ref'],'evidence_digest':obs['digest']}; return len(json.dumps(x,separators=(',',':'),sort_keys=True))
bytes_rows=[]
for name,trace in [('positive',positive),('changed',changed)]:
  state='empty'; pending=None
  for obs in trace:
    fullp=obs['predicates']; scopedp=project(obs,state,pending)['predicates']; bytes_rows.append({'case':name,'state':state,'full_predicate_bytes':len(json.dumps(fullp,separators=(',',':'),sort_keys=True)),'scoped_predicate_bytes':len(json.dumps(scopedp,separators=(',',':'),sort_keys=True)),'full_normalized_bytes':norm_size(obs,fullp),'scoped_normalized_bytes':norm_size(obs,scopedp)})
    spec=interface['states'][state]
    if spec['action']:
      a=interface['actions'][spec['action']]; pending={'action':spec['action'],'expected':a['expected']}; state=spec['next']
    else: pending=None
summary={'results':results,'required':{s:required(s,({'action':'enter_token','expected':{'field_pixels_changed':True}} if s=='filled' else {'action':'submit_form','expected':{'submission_pixels_changed':True}} if s=='submitted' else None)) for s in interface['states']},'omission_ablation':omits,'bytes':bytes_rows}
(OUT/'chromium_v5_replay_results.json').write_text(json.dumps(summary,indent=2)+'\n'); print(json.dumps(summary,indent=2))
