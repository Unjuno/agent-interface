import hashlib,json
SOURCE_SHA = {'schema.json':'7fe3ad10ab69b0d8786d17ca854e65f90efd213b','runtime/cli_v1/api.py':'5674bd39e3cb2170095f476dac90e2a781f4f77a','runtime/cli_v1/receipt.py':'ebe71a2edfbb524a4288241686b969342a0bfcae','runtime/cli_v1/README.md':'8cafa39718f0d5d66cb73ade3aa99f0f1cce6d6','runtime/golden_desktop_demo_v3.py':'26db03b8400b03fbe5272bd4ae5ad9c3a82d31a2'}
FIELDS={'schema':'derived','program_completed':'unverified','task_success':'unverified','authority_granted':'derived_guard','status':'unverified','partial_effects':'unverified','cleanup_error':'cli_source_backed','lifecycle':'documented_only','usage':'documented_only'}
CLI_STATUSES={'returned','backend_unavailable','runtime_failed'}; GOLDEN_STATUSES={'success','partial','refused','stale_invalidated','cleanup_failed'}
def classify(r):
    if not isinstance(r,dict) or r.get('authority_granted') is not False: return 'REJECT_AUTHORITY'
    s=r.get('status')
    if s not in GOLDEN_STATUSES: return 'REJECT_UNKNOWN_STATUS'
    if s=='cleanup_failed' and not r.get('cleanup_error'): return 'REJECT_CLEANUP_CONTRADICTION'
    if s=='success' and (r.get('program_completed') is not True or r.get('task_success') is not True): return 'REJECT_SUCCESS_CONTRADICTION'
    if s=='partial' and 'partial_effects' not in r: return 'REJECT_MISSING_PARTIAL_EFFECTS'
    return 'ACCEPT_CONTRACT_ONLY'
def main():
    assert len(FIELDS)==9 and CLI_STATUSES=={'returned','backend_unavailable','runtime_failed'}
    f=[{'authority_granted':False,'status':'success','program_completed':True,'task_success':True,'cleanup_error':None},{'authority_granted':False,'status':'partial','program_completed':False,'task_success':False,'partial_effects':['x'],'cleanup_error':None},{'authority_granted':False,'status':'cleanup_failed','program_completed':False,'task_success':False,'partial_effects':[],'cleanup_error':'CLOSE_FAILED'},{'authority_granted':True,'status':'success','program_completed':True,'task_success':True},{'authority_granted':False,'status':'success','program_completed':False,'task_success':True,'cleanup_error':None},{'authority_granted':False,'status':'partial','program_completed':False,'task_success':False,'cleanup_error':None},{'authority_granted':False,'status':'backend_unavailable'}]
    o=[classify(x) for x in f]; e=['ACCEPT_CONTRACT_ONLY']*3+['REJECT_AUTHORITY','REJECT_SUCCESS_CONTRADICTION','REJECT_MISSING_PARTIAL_EFFECTS','REJECT_UNKNOWN_STATUS']; assert o==e
    d=hashlib.sha256(json.dumps({'source_sha':SOURCE_SHA,'fields':FIELDS,'outcomes':o},sort_keys=True).encode()).hexdigest()
    print(json.dumps({'decision':'HOLD_ADAPTER_CONTRACT_NOT_SOURCE_BACKED','fixtures':7,'accepted':3,'rejected':4,'authority_grants':0,'cli_statuses':sorted(CLI_STATUSES),'golden_statuses':sorted(GOLDEN_STATUSES),'unverified_fields':[k for k,v in FIELDS.items() if v=='unverified'],'source_sha':SOURCE_SHA,'digest':d},sort_keys=True))
if __name__=='__main__': main()