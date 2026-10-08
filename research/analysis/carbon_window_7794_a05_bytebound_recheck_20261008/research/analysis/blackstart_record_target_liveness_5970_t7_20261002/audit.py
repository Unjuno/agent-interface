import hashlib,json
from pathlib import Path
HERE=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    f=json.loads((HERE/'FREEZE.json').read_text());w=json.loads((HERE/'candidate.wrapper.raw.json').read_text());r=w['candidate'];errs=[]
    if w['app_sha256']!=f['t3_derived_app_sha256']:errs.append('T3_APP_HASH_MISMATCH')
    if sha(HERE/'candidate.py')!=f['candidate_sha256'] or sha(HERE/'runner.py')!=f['runner_sha256']:errs.append('T7_FROZEN_SOURCE_HASH_MISMATCH')
    if r.get('input_dispatched') is not False:errs.append('INPUT_DISPATCH_NOT_FALSE')
    q=r.get('target_query',{});target=f['recorded_target_xid']
    if r.get('target_xid')!=target:errs.append('TARGET_XID_MISMATCH')
    if errs:status='HOLD_SOURCE_OR_RAW_MISMATCH'
    elif q.get('result')=='error' and q.get('error_code')==3 and not r.get('target_in_tree'):status='PASS_TARGET_ABSENT_PREINPUT'
    elif q.get('result')=='success' and q.get('map_state')!=2:status='PASS_TARGET_PRESENT_UNMAPPED'
    elif q.get('result')=='success':status='HOLD_TARGET_PRESENT_MAPPED'
    else:status='HOLD_QUERY_ERROR_OTHER'
    result={'schema':'blackstart-record-target-liveness-t7-audit-v1','status':status,'errors':errs,'target_xid':target,'input_dispatched':r.get('input_dispatched'),'target_in_tree':r.get('target_in_tree'),'target_query':q,'tree':r.get('tree',[]),'scope':'one no-input source-derived Tk fixture in private Xvfb; no event-routing or recovery causality claim'}
    (HERE/'audit.raw.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n');print(json.dumps(result,indent=2));return 0
if __name__=='__main__':raise SystemExit(main())
