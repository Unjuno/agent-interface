from copy import deepcopy
from common import load_fixture,validate_fixture,evaluate
f=load_fixture(); assert validate_fixture(f)
r=evaluate(f); assert r['decision']=='HOLD_CRITICAL_NORMALIZATION_MISSING'; assert r['required_edges']==9; assert r['mapped_required_edges']==0
x=deepcopy(f); x['inventory'][0]['executable_mapping']={'path':'adapter.py','kind':'FOCUS_CHANGED'}; assert evaluate(x)['mapped_required_edges']==1
x=deepcopy(f); ordinary=next(r for r in x['inventory'] if r['raw'].get('event')=='input_admission'); ordinary['executable_mapping']={'path':'bad.py','kind':'SAFETY_VIOLATION'}; assert evaluate(x)['decision']=='FAIL_CRITICAL_MISCLASSIFICATION'
print('MECHANICS_PASS')
