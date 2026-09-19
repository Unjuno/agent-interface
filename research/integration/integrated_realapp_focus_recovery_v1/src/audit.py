import hashlib,json,sys
from pathlib import Path
EXPECTED_SVG='b0242110e0f2df6172c7a7714b95899ddbcc45e012084c601cf8d692d35ac393'

def audit(rows):
    e=[]
    if len(rows)!=8:e.append('rows')
    if len({r['case_id'] for r in rows})!=len(rows):e.append('ids')
    stale=[r for r in rows if r['arm']=='retained_stale_context']; real=[r for r in rows if r['arm']=='real_observe_only']
    if len(stale)!=4 or len(real)!=4:e.append('strata')
    for r in rows:
        if r['source']['role']!='A' or r['admission']['role']!='B':e.append(r['case_id']+':focus_setup')
        b=r.get('baseline_result') or {}
        if b.get('status')!='safe_yield' or b.get('reason')!='execution_failed' or b.get('completed_actions')!=0:e.append(r['case_id']+':baseline')
        if (r.get('last_terminal') or {}).get('reason')!='focus_mismatch':e.append(r['case_id']+':terminal')
        if r['submit_count_total']!=1:e.append(r['case_id']+':submit_shape')
        if r['pre_recovery_actual']['role']!='B' or r['post_recovery_actual']['role']!='B':e.append(r['case_id']+':focus_changed')
        if r['pre_recovery_actual']['raw_surface_xid']!=r['post_recovery_actual']['raw_surface_xid']:e.append(r['case_id']+':surface_changed')
        for k in ('source_input','admission_input','pre_input','post_input'):
            if r[k]['key_bytes_nonzero']!=0 or r[k]['pointer_mask']!=0:e.append(r['case_id']+':input_'+k)
        if r['svg_sha256']!=EXPECTED_SVG:e.append(r['case_id']+':svg')
    for r in stale:
        if r['status']!='recovery_rejected' or r['recovery_rejection']!='stale':e.append(r['case_id']+':stale_not_rejected')
        if r['real_x11_queries']!=0 or r['recovery_queries']!=1:e.append(r['case_id']+':stale_query')
    for r in real:
        if r['status']!='ok':e.append(r['case_id']+':real_status')
        c=(r.get('composed') or {}); z=c.get('result') or {}; rc=z.get('recovery_context') or {}
        if z.get('status')!='safe_yield' or z.get('reason')!='focus_mismatch':e.append(r['case_id']+':real_result')
        if c.get('post_rejection_task_submits')!=0:e.append(r['case_id']+':retry')
        if r['recovery_queries']!=1 or r['real_x11_queries']!=1:e.append(r['case_id']+':real_query')
        if rc.get('focus')!='B' or rc.get('surface')!='B':e.append(r['case_id']+':current')
        if rc.get('authority')!='none' or rc.get('task_input_granted') is not False or rc.get('action_admission_eligible') is not False:e.append(r['case_id']+':authority')
        if (r.get('recovery_raw') or {}).get('role')!='B':e.append(r['case_id']+':raw_current')
    return {'decision':'PASS_INTEGRATED_REALAPP_FOCUS_RECOVERY_SCOPED' if not e else 'FAIL_INTEGRITY_OR_CONTRACT','errors':e,'rows':len(rows)}

if __name__=='__main__':
    rows=json.loads(Path(sys.argv[1]).read_text()); out=audit(rows)
    Path(sys.argv[2]).write_text(json.dumps(out,sort_keys=True,indent=2)+'\n');print(json.dumps(out))
