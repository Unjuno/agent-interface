import json, pathlib, sys

def audit(obj):
    errs=[]; rows={(r['policy'],r['scenario']):r for r in obj.get('rows',[])}
    def chk(pol,sc,bridge=None,berr=None,accepted=None,cerr=None):
        r=rows.get((pol,sc))
        if not r: errs.append(['missing',pol,sc]); return
        if bridge is not None and r['bridge_status']!=bridge: errs.append([pol,sc,'bridge',r['bridge_status'],bridge])
        if berr is not None and r['bridge_error']!=berr: errs.append([pol,sc,'bridge_error',r['bridge_error'],berr])
        if accepted is not None:
            got=None if r['core_admission'] is None else r['core_admission']['accepted']
            if got!=accepted: errs.append([pol,sc,'accepted',got,accepted])
        if cerr is not None:
            got=None if r['core_admission'] is None else r['core_admission']['error']
            if got!=cerr: errs.append([pol,sc,'core_error',got,cerr])
    chk('naive','direct_current','PROGRAM_CONSTRUCTED',accepted=True)
    chk('typed','direct_current','PROGRAM_CONSTRUCTED',accepted=True)
    chk('naive','hint_stale_numeric','PROGRAM_CONSTRUCTED',accepted=False,cerr='STALE_OBSERVATION')
    chk('typed','hint_stale_numeric','BRIDGE_REJECTED','HINT_REQUIRES_CURRENT_REVALIDATION')
    chk('naive','hint_laundered_current_numeric','PROGRAM_CONSTRUCTED',accepted=True)
    chk('typed','hint_laundered_current_numeric','BRIDGE_REJECTED','HINT_REQUIRES_CURRENT_REVALIDATION')
    chk('typed','hint_exact_revalidated','PROGRAM_CONSTRUCTED',accepted=True)
    chk('typed','hint_wrong_source_revalidation','BRIDGE_REJECTED','REVALIDATION_SOURCE_MISMATCH')
    chk('typed','hint_wrong_target_revalidation','BRIDGE_REJECTED','REVALIDATION_TARGET_MISMATCH')
    chk('typed','hint_stale_revalidation_observation','PROGRAM_CONSTRUCTED',accepted=False,cerr='STALE_OBSERVATION')
    chk('typed','hint_stale_revalidation_binding','PROGRAM_CONSTRUCTED',accepted=False,cerr='STALE_BINDING')
    chk('typed','forged_inplace_role_currentness','BRIDGE_REJECTED','RECEIPT_DIGEST_MISMATCH')
    chk('naive','forged_inplace_role_currentness','BRIDGE_REJECTED','RECEIPT_DIGEST_MISMATCH')
    chk('typed','direct_current_expired_lease','PROGRAM_CONSTRUCTED',accepted=False,cerr='LEASE_EXPIRED')
    chk('typed','direct_current_missing_pointer_capability','PROGRAM_CONSTRUCTED',accepted=False,cerr='UNSUPPORTED_CAPABILITY')
    if obj.get('core_blob')!='a16620b65d22757ca9160d68feb1381306cc6ac3': errs.append(['core_blob'])
    if obj.get('formal_reruns')!=0: errs.append(['reruns'])
    return {'decision':'PASS_CORE_V1_HINT_LINEAGE_BRIDGE_SCOPED' if not errs else 'FAIL_INTEGRITY','errors':errs,'row_count':len(obj.get('rows',[]))}

if __name__=='__main__':
    obj=json.loads(pathlib.Path(sys.argv[1]).read_text()); out=audit(obj); print(json.dumps(out,sort_keys=True,indent=2)); raise SystemExit(0 if not out['errors'] else 1)
