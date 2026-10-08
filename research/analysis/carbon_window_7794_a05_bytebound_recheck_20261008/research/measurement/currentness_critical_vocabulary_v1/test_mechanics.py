from copy import deepcopy
from common import load,evaluate
f=load(); r=evaluate(f); assert r['decision']=='PASS_CURRENTNESS_VOCABULARY_GAP_SCOPED'; assert all(not x['admissible'] for x in r['required_cases']); assert r['controls_ok']
x=deepcopy(f); x['kind_predicates']['AUTHORITY_REVOKED']=['currentness_invalidated']; assert evaluate(x)['decision']=='PASS_EXISTING_KIND_SUFFICIENT_SCOPED'
x=deepcopy(f); x['controls'][0]['facts']['safety_violation']=True; assert 'SAFETY_VIOLATION' in evaluate(x)['controls'][0]['admissible']
print('MECHANICS_PASS')
