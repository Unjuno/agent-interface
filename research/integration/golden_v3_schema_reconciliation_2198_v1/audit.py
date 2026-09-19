import hashlib,json
fields=['schema','program_completed','task_success','authority_granted','status','partial_effects','cleanup_error','lifecycle','usage']
source_backed={'schema':'derived','program_completed':'unverified','task_success':'unverified','authority_granted':'derived_guard','status':'unverified','partial_effects':'unverified','cleanup_error':'cli_source_backed','lifecycle':'documented_only','usage':'documented_only'}
def main():
    assert set(source_backed)==set(fields)
    assert any(v=='unverified' for v in source_backed.values())
    assert source_backed['task_success']=='unverified' and source_backed['partial_effects']=='unverified'
    digest=hashlib.sha256(json.dumps(source_backed,sort_keys=True).encode()).hexdigest()
    print(json.dumps({'decision':'HOLD_PROPOSED_SCHEMA_NOT_SOURCE_BACKED','fields':9,'unverified':[k for k,v in source_backed.items() if v=='unverified'],'digest':digest,'runtime':0,'adapter':0},sort_keys=True))
main()
