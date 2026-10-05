"""Bounded planner DSL: representation conversion, never a supplied state graph."""
import copy,hashlib,json
from compiled_gui_interface_v1 import validate
PREDICATES=['target_valid','exact_token_visible','exact_saved_title']
def obj(properties):return {'type':'object','properties':properties,'required':list(properties),'additionalProperties':False}
def array(items,lo,hi):return {'type':'array','items':items,'minItems':lo,'maxItems':hi}
NAME={'type':'string','minLength':1,'maxLength':64}
def enum(values):return {'type':'string','enum':values}
CONDITION=obj({'predicate':enum(PREDICATES),'value':{'type':'boolean'}})
BRANCH=obj({'when':array(CONDITION,1,3),'outcome':enum(['action','complete','yield']),'action':{'type':['string','null']},'next_state':{'type':['string','null']},'reason':{'type':['string','null']}})
CONTRACT=obj({'interface_id':NAME,'symbols':array(obj({'name':NAME,'role':enum(['field','submit'])}),2,2),'actions':array(obj({'name':NAME,'target_symbol':NAME,'operation':enum(['enter_token','submit_form']),'expected_effect':array(CONDITION,1,3)}),2,2),'method':obj({'name':NAME,'version':NAME,'initial_state':NAME,'max_transitions':{'type':'integer','minimum':1,'maximum':4},'max_runtime_ms':{'type':'integer','minimum':1,'maximum':10000},'states':array(obj({'name':NAME,'branches':array(BRANCH,1,1)}),2,4)})})
def pairs(values):
 result={}
 for x in values:
  if x['predicate'] in result:raise ValueError('duplicate condition')
  result[x['predicate']]=x['value']
 return result

def compile_contract(contract,aliases,scope):
 c=copy.deepcopy(contract);symbols={};actions={};states={}
 for s in c['symbols']:
  if s['name'] in symbols:raise ValueError('duplicate symbol')
  symbols[s['name']]={'kind':'target_reference','target_reference':aliases[s['role']],'identity_predicate':'target_valid','dependencies':['target_valid']}
 roles={s['name']:s['role'] for s in c['symbols']}
 if set(roles.values())!={'field','submit'}:raise ValueError('both roles required')
 for a in c['actions']:
  if a['name'] in actions:raise ValueError('duplicate action')
  required_role='field' if a['operation']=='enter_token' else 'submit'
  if roles.get(a['target_symbol'])!=required_role:raise ValueError('operation target role mismatch')
  effect=pairs(a['expected_effect'])
  needed='exact_token_visible' if a['operation']=='enter_token' else 'exact_saved_title'
  if effect.get(needed) is not True:raise ValueError('required effect omitted')
  actions[a['name']]={'target_symbol':a['target_symbol'],'operation':a['operation'],'expected_effect':effect}
 for s in c['method']['states']:
  if s['name'] in states:raise ValueError('duplicate state')
  branches=[]
  for b in s['branches']:
   branch={**b,'when':pairs(b['when'])}
   if branch['outcome']=='complete' and branch['when'].get('exact_saved_title') is not True:raise ValueError('unverified completion')
   if branch['outcome']=='action' and actions.get(branch['action'],{}).get('operation')=='submit_form':
    if branch['when'].get('exact_token_visible') is not True:raise ValueError('submit without token condition')
   branches.append(branch)
  states[s['name']]={'branches':branches}
 method={k:v for k,v in c['method'].items() if k!='states'};method['states']=states
 return validate({'format':'compiled-gui-interface-v1','interface_id':c['interface_id'],'session_scope':scope,'surface':'integrated-form','predicates':PREDICATES,'symbols':symbols,'actions':actions,'method':method})
