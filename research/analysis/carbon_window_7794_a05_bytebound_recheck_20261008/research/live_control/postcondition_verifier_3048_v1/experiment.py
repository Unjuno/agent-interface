import hashlib, json

CASES=[
 {'id':'save_ok','target':'file:a','receipt':True,'fresh':True,'state_before':'h0','state_after':'h1','expected':'h1','effect':True,'cleanup':True},
 {'id':'geometry_ok','target':'window:1','receipt':True,'fresh':True,'state_before':'100x100','state_after':'120x100','expected':'120x100','effect':True,'cleanup':True},
 {'id':'typed_transition_ok','target':'calc:1','receipt':True,'fresh':True,'state_before':'idle','state_after':'saved','expected':'saved','effect':True,'cleanup':True},
 {'id':'accepted_no_effect','target':'file:a','receipt':True,'fresh':True,'state_before':'h0','state_after':'h0','expected':'h1','effect':False,'cleanup':True},
 {'id':'wrong_target','target':'file:b','receipt':True,'fresh':True,'state_before':'h0','state_after':'h1','expected':'h1','effect':True,'cleanup':True},
 {'id':'stale','target':'file:a','receipt':True,'fresh':False,'state_before':'h0','state_after':'h1','expected':'h1','effect':True,'cleanup':True},
 {'id':'ambiguous_receipt','target':'file:a','receipt':None,'fresh':True,'state_before':'h0','state_after':'h1','expected':'h1','effect':True,'cleanup':True},
 {'id':'missing_effect','target':'file:a','receipt':True,'fresh':True,'state_before':'h0','state_after':'h1','expected':'h1','effect':None,'cleanup':True},
 {'id':'pixel_only','target':'file:a','receipt':True,'fresh':True,'state_before':'h0','state_after':'h0','expected':'h0','effect':True,'cleanup':True,'pixel_changed':True},
 {'id':'cleanup_failure','target':'file:a','receipt':True,'fresh':True,'state_before':'h0','state_after':'h1','expected':'h1','effect':True,'cleanup':False},
]
def verify(c):
 if c['target'] not in ('file:a','window:1','calc:1'): return 'HOLD_UNKNOWN'
 if c['receipt'] is not True or c['fresh'] is not True: return 'HOLD_UNKNOWN'
 if c.get('pixel_changed') and c['state_after']==c['expected']: return 'HOLD_UNKNOWN'
 if c['effect'] is not True or c['cleanup'] is not True: return 'FAIL_POSTCONDITION'
 if c['state_after'] != c['expected']: return 'FAIL_POSTCONDITION'
 return 'PASS_POSTCONDITION'
def independent(c):
 # separate implementation: no call to verify and no runtime state mutation
 valid=(c['receipt'] is True and c['fresh'] is True and c['effect'] is True and c['cleanup'] is True and not c.get('pixel_changed') and c['state_after']==c['expected'])
 return 'PASS_POSTCONDITION' if valid else ('FAIL_POSTCONDITION' if c['receipt'] is True and c['fresh'] is True and c['effect'] is not None and c['cleanup'] is not None and not c.get('pixel_changed') else 'HOLD_UNKNOWN')
rows=[]
for c in CASES:
 v=verify(c); a=independent(c); rows.append({'id':c['id'],'verdict':v,'audit':a,'agreement':v==a,'sha256':hashlib.sha256(json.dumps(c,sort_keys=True).encode()).hexdigest()})
corruption=[]
for field in ('target','fresh','state_after','expected','receipt','effect'):
 c=dict(CASES[0]); c[field]=('corrupt' if isinstance(c[field],str) else False); corruption.append({'field':field,'verdict':verify(c),'fail_closed':verify(c)!='PASS_POSTCONDITION'})
decision='PASS_DETERMINISTIC_POSTCONDITION_BOUNDARY_SCOPED' if all(r['agreement'] for r in rows) and all(x['fail_closed'] for x in corruption) and sum(r['verdict']=='PASS_POSTCONDITION' for r in rows)==3 else 'FAIL_POSTCONDITION_BOUNDARY'
print(json.dumps({'decision':decision,'rows':rows,'corruption':corruption,'rich_agent_calls':0,'model_calls':0,'network_calls':0},sort_keys=True))
