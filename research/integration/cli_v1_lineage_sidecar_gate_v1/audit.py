import json,pathlib,sys

def audit(o):
    e=[]; rows={(r['policy'],r['scenario']):r for r in o.get('rows',[])}
    def raw(sc,status=None,accepted=None,error=None,opens=None):
        r=rows.get(('raw_cli',sc));
        if not r: e.append(['missing','raw_cli',sc]); return
        if status is not None and r['output'].get('status')!=status: e.append(['raw',sc,'status',r['output'].get('status'),status])
        res=r['output'].get('result') or {}
        if accepted is not None and res.get('accepted')!=accepted: e.append(['raw',sc,'accepted',res.get('accepted'),accepted])
        if error is not None and res.get('error')!=error: e.append(['raw',sc,'error',res.get('error'),error])
        if opens is not None and r['open_session_calls']!=opens: e.append(['raw',sc,'opens',r['open_session_calls'],opens])
    def gate(sc,status=None,error=None,cli_accepted=None,cli_error=None,opens=None):
        r=rows.get(('sidecar_gate',sc));
        if not r: e.append(['missing','sidecar_gate',sc]); return
        if status is not None and r['output'].get('status')!=status: e.append(['gate',sc,'status',r['output'].get('status'),status])
        if error is not None and r['output'].get('error')!=error: e.append(['gate',sc,'error',r['output'].get('error'),error])
        cli=(r['output'].get('cli_result') or {}); res=cli.get('result') or {}
        if cli_accepted is not None and res.get('accepted')!=cli_accepted: e.append(['gate',sc,'accepted',res.get('accepted'),cli_accepted])
        if cli_error is not None and res.get('error')!=cli_error: e.append(['gate',sc,'cli_error',res.get('error'),cli_error])
        if opens is not None and r['open_session_calls']!=opens: e.append(['gate',sc,'opens',r['open_session_calls'],opens])
    raw('direct_current','returned',True,None,1)
    raw('hint_stale_numeric','returned',False,'STALE_OBSERVATION',1)
    raw('hint_laundered_current_numeric','returned',True,None,1)
    raw('hint_exact_revalidated','returned',True,None,1)
    raw('stale_revalidation','returned',False,'STALE_OBSERVATION',1)
    raw('expired_lease','returned',False,'LEASE_EXPIRED',1)
    raw('missing_pointer_capability','returned',False,'UNSUPPORTED_CAPABILITY',1)
    raw('invalid_current_request','invalid_request',opens=0)
    gate('direct_current','delegated',cli_accepted=True,opens=1)
    gate('hint_stale_numeric','lineage_rejected','LINEAGE_NOT_CURRENT_ADMISSION',opens=0)
    gate('hint_laundered_current_numeric','lineage_rejected','LINEAGE_NOT_CURRENT_ADMISSION',opens=0)
    gate('hint_exact_revalidated','delegated',cli_accepted=True,opens=1)
    gate('wrong_point_sidecar','lineage_rejected','PROGRAM_POINT_MISMATCH',opens=0)
    gate('wrong_source_sidecar','lineage_rejected','PROGRAM_SOURCE_MISMATCH',opens=0)
    gate('forged_receipt_role','lineage_rejected','EVIDENCE_RECEIPT_DIGEST_MISMATCH',opens=0)
    gate('stale_revalidation','delegated',cli_accepted=False,cli_error='STALE_OBSERVATION',opens=1)
    gate('expired_lease','delegated',cli_accepted=False,cli_error='LEASE_EXPIRED',opens=1)
    gate('missing_pointer_capability','delegated',cli_accepted=False,cli_error='UNSUPPORTED_CAPABILITY',opens=1)
    gate('invalid_current_request','delegated',opens=0)
    if o.get('core_blob')!='a16620b65d22757ca9160d68feb1381306cc6ac3': e.append(['core_blob'])
    if o.get('api_blob')!='58e5489796959f120d973b595f36ed3d808533b3': e.append(['api_blob'])
    if o.get('formal_reruns')!=0: e.append(['reruns'])
    return {'decision':'PASS_CLI_V1_LINEAGE_SIDECAR_GATE_SCOPED' if not e else 'FAIL_INTEGRITY','errors':e,'row_count':len(o.get('rows',[]))}
if __name__=='__main__':
    out=audit(json.loads(pathlib.Path(sys.argv[1]).read_text())); print(json.dumps(out,sort_keys=True,indent=2)); raise SystemExit(0 if not out['errors'] else 1)
