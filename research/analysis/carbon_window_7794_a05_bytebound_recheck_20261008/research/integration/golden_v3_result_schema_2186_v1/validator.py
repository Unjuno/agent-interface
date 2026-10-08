import hashlib,json
FIELDS={'schema':str,'program_completed':bool,'task_success':bool,'authority_granted':bool,'status':str,'partial_effects':list,'cleanup_error':(str,type(None)),'lifecycle':list,'usage':dict}
STATES={'doctor','model_attempt','observation','dispatch','refusal','effect','repair','release','cleanup'}
FIX=[
 {'schema':'golden-v3-result-v1','program_completed':True,'task_success':True,'authority_granted':False,'status':'success','partial_effects':[],'cleanup_error':None,'lifecycle':['doctor','model_attempt','observation','dispatch','effect','release'],'usage':{'input':1}},
 {'schema':'golden-v3-result-v1','program_completed':False,'task_success':False,'authority_granted':False,'status':'partial','partial_effects':['effect-1'],'cleanup_error':None,'lifecycle':['doctor','dispatch','effect','release'],'usage':{}},
 {'schema':'golden-v3-result-v1','program_completed':False,'task_success':False,'authority_granted':False,'status':'refused','partial_effects':[],'cleanup_error':None,'lifecycle':['doctor','observation','refusal'],'usage':{}},
 {'schema':'golden-v3-result-v1','program_completed':False,'task_success':False,'authority_granted':False,'status':'stale_invalidated','partial_effects':[],'cleanup_error':None,'lifecycle':['observation','repair','refusal'],'usage':{}},
 {'schema':'golden-v3-result-v1','program_completed':False,'task_success':False,'authority_granted':False,'status':'cleanup_failed','partial_effects':['effect-1'],'cleanup_error':'CLOSE_FAILED','lifecycle':['dispatch','effect','cleanup'],'usage':{}},
]
def validate(x):
    assert set(FIELDS)<=set(x)
    for k,t in FIELDS.items(): assert isinstance(x[k],t)
    assert set(x['lifecycle'])<=STATES and not x['authority_granted']
    if x['cleanup_error'] is not None: assert x['status']=='cleanup_failed' and not x['task_success']
    if x['status']=='success': assert x['program_completed'] and x['task_success']
    if x['status']=='partial': assert not x['program_completed'] or not x['task_success']
def main():
    for x in FIX: validate(x)
    bad=dict(FIX[0]); bad['cleanup_error']='CLOSE_FAILED'; bad['status']='success'
    try: validate(bad)
    except AssertionError: rejected=True
    else: rejected=False
    assert rejected and {s for x in FIX for s in x['lifecycle']}==STATES
    digest=hashlib.sha256(json.dumps(FIX,sort_keys=True).encode()).hexdigest()
    print(json.dumps({'fixtures':5,'states':9,'accepted':5,'cleanup_promotion_rejected':rejected,'authority_grants':0,'digest':digest,'validator':'PASS','model':0,'gui':0,'input':0},sort_keys=True))
main()
