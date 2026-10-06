import json,copy,time
from pathlib import Path
from planner_contract_schema import compile_contract
from compiled_gui_interface_v1 import run
cond=lambda p:[{'predicate':p,'value':True}]
c={'interface_id':'fixture-planner-shaped','symbols':[{'name':'entry','role':'field'},{'name':'commit','role':'submit'}],'actions':[{'name':'write_value','target_symbol':'entry','operation':'enter_token','expected_effect':cond('exact_token_visible')},{'name':'commit_value','target_symbol':'commit','operation':'submit_form','expected_effect':cond('exact_saved_title')}],'method':{'name':'authored','version':'1','initial_state':'start','max_transitions':2,'max_runtime_ms':10000,'states':[{'name':'start','branches':[{'when':cond('target_valid'),'outcome':'action','action':'write_value','next_state':'ready','reason':None}]},{'name':'ready','branches':[{'when':cond('exact_token_visible'),'outcome':'action','action':'commit_value','next_state':'done','reason':None}]},{'name':'done','branches':[{'when':cond('exact_saved_title'),'outcome':'complete','action':None,'next_state':None,'reason':None}]}]}}

def execute_contract(c):
 graph=compile_contract(c,{'field':'minted-field','submit':'minted-submit'},'construction');actions=[];sequence=0
 def observe(p):
  nonlocal sequence
  sequence+=1
  return {'sequence':sequence,'captured_ns':time.perf_counter_ns(),'surface':'integrated-form','predicates':{'target_valid':True,'exact_token_visible':len(actions)>=1,'exact_saved_title':len(actions)>=2},'evidence_ref':str(sequence),'evidence_digest':str(sequence)}
 def admit(p):return {'eligible':True,'status':'revalidated','authorization':'construction-only','expected_sequence':sequence,'valid_until_ns':time.perf_counter_ns()+3000000000}
 def execute(p):
  actions.append(p['operation'])
  return {'status':'completed','action_id':str(len(actions)),'effect_ref':str(len(actions)),'release':{'verified':True,'keys_down':[],'buttons_down':[]}}
 result=run(graph,{'observe':observe,'admit':admit,'execute':execute,'verify_effect':lambda p:{'status':'succeeded','evidence_ref':p['observation']['evidence_ref']},'cancelled':lambda:False})
 return {'receipt':result,'operations':actions,'compiled':graph}
a=execute_contract(c);assert a['receipt']['outcome']=='TASK_SUCCEEDED' and a['operations']==['enter_token','submit_form']
b=copy.deepcopy(c);b['method']['initial_state']='done';b=execute_contract(b);assert b['receipt']['outcome']=='SAFE_YIELD' and b['operations']==[]
d=copy.deepcopy(c);d['method']['states'][1]['branches'][0]['when']=cond('target_valid')
try:compile_contract(d,{'field':'f','submit':'s'},'construction')
except ValueError as e:assert 'submit without token' in str(e)
else:raise AssertionError('unguarded submit accepted')
# Changing names preserves semantic execution; no hard-coded enter/filled/submitted state routing.
n=copy.deepcopy(c);mapping={'start':'fresh_scene','ready':'token_written','done':'receipt_seen','write_value':'alpha','commit_value':'omega'}
n['method']['initial_state']=mapping[n['method']['initial_state']]
for a in n['actions']:a['name']=mapping[a['name']]
for s in n['method']['states']:
 s['name']=mapping[s['name']]
 for branch in s['branches']:
  for key in ['action','next_state']:
   if branch[key] is not None:branch[key]=mapping[branch[key]]
n=execute_contract(n);assert n['receipt']['outcome']=='TASK_SUCCEEDED' and n['operations']==['enter_token','submit_form']
Path('/out/REGRESSION.json').write_text(json.dumps({'scope':'construction/test-double consumption; no model/GUI/provider/task success','authored_graph':a,'changed_initial_state':b,'renamed_graph':n,'unguarded_submit_rejected':True},indent=2))
print('PASS direct graph consumption, changed method refusal, arbitrary names, guard preservation')
