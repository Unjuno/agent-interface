from copy import deepcopy
from common import load,evaluate
f=load(); cs=[]
x=deepcopy(f); x['kind_predicates']['AUTHORITY_REVOKED']=['currentness_invalidated']; cs.append({'name':'launder_currentness_to_revocation','rejected':evaluate(x)['decision']!='PASS_CURRENTNESS_VOCABULARY_GAP_SCOPED'})
x=deepcopy(f); x['kind_predicates']['ACTION_REJECTED']=['requires_new_decision']; cs.append({'name':'launder_decision_need_to_rejection','rejected':evaluate(x)['decision']!='PASS_CURRENTNESS_VOCABULARY_GAP_SCOPED'})
x=deepcopy(f); x['required_guard_cases'][0]['facts']['effect_verified']=True; cs.append({'name':'inject_effect_fact','rejected':'EFFECT_VERIFIED' in evaluate(x)['required_cases'][0]['admissible']})
x=deepcopy(f); x['controls'][-1]['facts']['effect_verified']=True; cs.append({'name':'pixel_change_launder_effect','rejected':evaluate(x)['controls_ok'] is False})
x=deepcopy(f); x['kind_predicates']['MADE_UP']=['currentness_invalidated']
try: evaluate(x); ok=False
except AssertionError: ok=True
cs.append({'name':'invent_kind','rejected':ok}); assert all(c['rejected'] for c in cs); print('CORRUPTION_PASS',len(cs))
