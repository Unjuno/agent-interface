from copy import deepcopy
from common import load_fixture,evaluate
f=load_fixture(); controls=[]
def rec(name,fn):
    try: fn(); controls.append({'name':name,'rejected':False})
    except Exception: controls.append({'name':name,'rejected':True})
rec('source_blob_drift',lambda: (lambda x: evaluate(x))(dict(f,sources={**f['sources'],'input_owner':{**f['sources']['input_owner'],'git_blob':'bad'}})))
rec('unknown_kind',lambda: (lambda x: evaluate(x))(dict(f,queue_critical_kinds=f['queue_critical_kinds']+['MADE_UP'])))
x=deepcopy(f); x['inventory'][0]['executable_mapping']={'path':'adapter.py','kind':'FOCUS_CHANGED'}; assert evaluate(x)['mapped_required_edges']==1; controls.append({'name':'invented_mapping_changes_count','rejected':True})
x=deepcopy(f); row=next(r for r in x['inventory'] if r['raw'].get('event')=='input_admission'); row['executable_mapping']={'path':'bad.py','kind':'SAFETY_VIOLATION'}; assert evaluate(x)['decision']=='FAIL_CRITICAL_MISCLASSIFICATION'; controls.append({'name':'ordinary_promotion','rejected':True})
x=deepcopy(f); row=next(r for r in x['inventory'] if r['raw'].get('result')=='visible_change'); row['must_preserve']=True; row['candidate_kind']='EFFECT_VERIFIED'; assert evaluate(x)['required_edges']==10; controls.append({'name':'pixel_change_laundered_to_effect','rejected':True})
assert all(c['rejected'] for c in controls); print('CORRUPTION_PASS',len(controls))
