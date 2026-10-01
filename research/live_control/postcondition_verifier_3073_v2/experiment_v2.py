import hashlib,json
CASES=[
 {'id':'save_ok','target':'file:a','expected_target':'file:a','receipt':True,'fresh':True,'before':'h0','after':'h1','expected':'h1','effect':True,'cleanup':True},
 {'id':'geometry_ok','target':'window:1','expected_target':'window:1','receipt':True,'fresh':True,'before':'100x100','after':'120x100','expected':'120x100','effect':True,'cleanup':True},
 {'id':'typed_transition_ok','target':'calc:1','expected_target':'calc:1','receipt':True,'fresh':True,'before':'idle','after':'saved','expected':'saved','effect':True,'cleanup':True},
 {'id':'accepted_no_effect','target':'file:a','expected_target':'file:a','receipt':True,'fresh':True,'before':'h0','after':'h0','expected':'h1','effect':False,'cleanup':True},
 {'id':'wrong_target','target':'file:b','expected_target':'file:a','receipt':True,'fresh':True,'before':'h0','after':'h1','expected':'h1','effect':True,'cleanup':True},
 {'id':'stale','target':'file:a','expected_target':'file:a','receipt':True,'fresh':False,'before':'h0','after':'h1','expected':'h1','effect':True,'cleanup':True},
 {'id':'ambiguous_receipt','target':'file:a','expected_target':'file:a','receipt':None,'fresh':True,'before':'h0','after':'h1','expected':'h1','effect':True,'cleanup':True},
 {'id':'missing_effect','target':'file:a','expected_target':'file:a','receipt':True,'fresh':True,'before':'h0','after':'h1','expected':'h1','effect':None,'cleanup':True},
 {'id':'pixel_only','target':'file:a','expected_target':'file:a','receipt':True,'fresh':True,'before':'h0','after':'h0','expected':'h0','effect':True,'pixel_changed':True,'cleanup':True},
 {'id':'cleanup_failure','target':'file:a','expected_target':'file:a','receipt':True,'fresh':True,'before':'h0','after':'h1','expected':'h1','effect':True,'cleanup':False},
]
def verdict(c):
 if c.get('target') != c.get('expected_target') or c.get('receipt') is not True or c.get('fresh') is not True: return 'HOLD_UNKNOWN'
 if c.get('pixel_changed') or c.get('effect') is not True or c.get('cleanup') is not True: return 'FAIL_POSTCONDITION' if c.get('effect') is False or c.get('cleanup') is False else 'HOLD_UNKNOWN'
 return 'PASS_POSTCONDITION' if c.get('after') == c.get('expected') else 'FAIL_POSTCONDITION'
def audit(c):
 # Independent field-by-field reconstruction, intentionally no call to verdict().
 if c['target'] != c['expected_target'] or c['receipt'] is not True or c['fresh'] is not True: return 'HOLD_UNKNOWN'
 if c.get('pixel_changed'): return 'HOLD_UNKNOWN'
 if c.get('effect') is None: return 'HOLD_UNKNOWN'
 if c.get('effect') is False or c.get('cleanup') is False: return 'FAIL_POSTCONDITION'
 return 'PASS_POSTCONDITION' if c['after'] == c['expected'] else 'FAIL_POSTCONDITION'
rows=[]
for c in CASES:
 v,a=verdict(c),audit(c); rows.append({'id':c['id'],'verdict':v,'audit':a,'agreement':v==a,'sha256':hashlib.sha256(json.dumps(c,sort_keys=True).encode()).hexdigest()})
corruption=[]
for field in ('target','expected_target','fresh','after','expected','receipt','effect'):
 c=dict(CASES[0]); c[field]=('corrupt' if isinstance(c[field],str) else False); x=verdict(c); corruption.append({'field':field,'verdict':x,'fail_closed':x!='PASS_POSTCONDITION'})
decision='PASS_DETERMINISTIC_POSTCONDITION_BOUNDARY_SCOPED' if all(r['agreement'] for r in rows) and all(x['fail_closed'] for x in corruption) and sum(r['verdict']=='PASS_POSTCONDITION' for r in rows)==3 else 'FAIL_POSTCONDITION_BOUNDARY'
print(json.dumps({'decision':decision,'rows':rows,'corruption':corruption,'rich_agent_calls':0,'model_calls':0,'network_calls':0},sort_keys=True))
