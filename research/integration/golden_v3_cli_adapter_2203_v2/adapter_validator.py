import hashlib,json
STATUSES={'success','partial','refused','stale_invalidated','cleanup_failed'}
CLI={'returned','backend_unavailable','runtime_failed'}
FIX=[
 {'schema':'golden-v3-result-v1','program_completed':True,'task_success':True,'authority_granted':False,'status':'success','partial_effects':[],'cleanup_error':None,'lifecycle':['doctor','model_attempt','observation','dispatch','effect','release'],'usage':{}},
 {'schema':'golden-v3-result-v1','program_completed':False,'task_success':False,'authority_granted':False,'status':'partial','partial_effects':['e1'],'cleanup_error':None,'lifecycle':['dispatch','effect','release'],'usage':{}},
 {'schema':'golden-v3-result-v1','program_completed':False,'task_success':False,'authority_granted':False,'status':'refused','partial_effects':[],'cleanup_error':None,'lifecycle':['observation','refusal'],'usage':{}},
 {'schema':'golden-v3-result-v1','program_completed':False,'task_success':False,'authority_granted':False,'status':'stale_invalidated','partial_effects':[],'cleanup_error':None,'lifecycle':['observation','repair','refusal'],'usage':{}},
 {'schema':'golden-v3-result-v1','program_completed':False,'task_success':False,'authority_granted':False,'status':'cleanup_failed','partial_effects':['e1'],'cleanup_error':'CLOSE_FAILED','lifecycle':['effect','cleanup'],'usage':{}},
]
def adapt(x):
    assert x['authority_granted'] is False and x['status'] in STATUSES
    if x['status']=='cleanup_failed': return {'status':'runtime_failed','task_success':False,'partial_effects':x['partial_effects'],'cleanup_error':x['cleanup_error'],'authority_granted':False}
    if x['status'] in ('refused','stale_invalidated'): return {'status':'returned','task_success':False,'partial_effects':x['partial_effects'],'refusal':x['status'],'authority_granted':False}
    return {'status':'returned','task_success':x['task_success'],'partial_effects':x['partial_effects'],'usage':x['usage'],'authority_granted':False}
def main():
    out=[adapt(x) for x in FIX]
    assert {x['status'] for x in out} <= CLI
    assert out[0]['task_success'] is True and out[0]['status']=='returned'
    assert out[1]['partial_effects']==['e1'] and out[1]['task_success'] is False
    assert out[3]['refusal']=='stale_invalidated'
    assert out[4]['status']=='runtime_failed' and out[4]['task_success'] is False
    bad=dict(FIX[0]); bad['authority_granted']=True
    try: adapt(bad)
    except AssertionError: rejected=True
    else: rejected=False
    assert rejected
    digest=hashlib.sha256(json.dumps(out,sort_keys=True).encode()).hexdigest()
    print(json.dumps({'fixtures':5,'mapped_statuses':5,'authority_true_rejected':rejected,'partial_preserved':True,'cleanup_non_success':True,'task_program_separate':True,'digest':digest,'formal':1,'model':0,'gui':0,'input':0},sort_keys=True))
main()
