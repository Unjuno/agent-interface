from copy import deepcopy
from census import load_fixture,evaluate
f=load_fixture(); controls=[]
def check(name,mutator,expected):
    x=deepcopy(f); mutator(x); got=evaluate(x)['decision']; controls.append({'name':name,'rejected':got==expected})
check('fake_32_rows',lambda x:x['observed_contract'].__setitem__('positive_rows',32),'BLOCKED_DATA')
check('stale_binding_as_negative',lambda x:x['observed_contract'].__setitem__('semantic_negative_rows',32),'BLOCKED_DATA')
check('invent_operation_oracle',lambda x:x['observed_contract'].__setitem__('independent_operation_target_semantic_oracle',True),'BLOCKED_DATA')
check('invent_split',lambda x:x['observed_contract'].__setitem__('independent_split_units',2),'BLOCKED_DATA')
check('invent_everything',lambda x:x['observed_contract'].update({'positive_rows':32,'semantic_negative_rows':32,'operation_classes':['CLICK','TYPE_TEXT'],'target_alternatives_per_operation':2,'yield_or_no_local_action_negative_rows':32,'independent_operation_target_semantic_oracle':True,'independent_split_units':2}),'READY_OPERATION_TARGET_SHADOW_CORPUS')
assert all(c['rejected'] for c in controls)
print('CORRUPTION_PASS',len(controls))
