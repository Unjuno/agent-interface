from copy import deepcopy
from census import load,evaluate
f=load(); cs=[]
def rec(name,mut,expected='BLOCKED_DATA'):
 x=deepcopy(f); mut(x); cs.append({'name':name,'rejected':evaluate(x)['decision']==expected})
rec('final_oracle_not_decision_oracle',lambda x:[y.__setitem__('episode_final_oracle',True) for y in x['families']])
rec('operation_diversity_not_labels',lambda x:x['families'][0].__setitem__('operation_families',['CLICK','TYPE_TEXT','SCROLL']))
rec('schema_rejection_not_semantic_negative',lambda x:x['families'][1].__setitem__('semantic_negative_rows',32))
rec('duplicate_trajectory_rows_not_enough',lambda x:[y.__setitem__('program_opportunities',64) for y in x['families']])
def all_ready(x):
 for y in x['families']:
  y['decision_operation_target_oracle']=True
  y['program_opportunities']=32
  y['target_alternatives_per_state']=2
 x['families'][0]['semantic_negative_rows']=32
 x['families'][0]['explicit_yield_no_action_rows']=32
rec('all_requirements_counterfactual',all_ready,'READY_CROSSDOMAIN_OPERATION_TARGET_CORPUS')
assert all(c['rejected'] for c in cs); print('CORRUPTION_PASS',len(cs))
