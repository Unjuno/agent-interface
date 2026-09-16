import json, sys
from pathlib import Path

CTX_FIELDS = ('app','client_id','focus_id','surface_kind','transient_for','geometry')

def expected_receipt(ctx, kind):
    return {
        'receipt_kind': kind,
        **{k: ctx[k] for k in CTX_FIELDS},
        'authority': 'none',
        'task_input_granted': False,
        'action_admission_eligible': False,
    }

def audit(fixture, rows):
    errors=[]
    cases={x['case_id']:x for x in fixture['cases']}
    if len(cases)!=8: errors.append('case_count')
    if len(rows)!=32: errors.append('row_count')
    keys={(r['case_id'],r['receipt_kind'],r['validator']) for r in rows}
    if len(keys)!=32: errors.append('matrix_unique')
    for cid,c in cases.items():
        s=c['source']; cur=c['current']
        if s['app']!='INKSCAPE' or cur['app']!='INKSCAPE': errors.append(cid+':app')
        if s['client_id']==cur['client_id']: errors.append(cid+':surface_not_distinct')
        if cur['transient_for']!=s['client_id']: errors.append(cid+':transient')
        rej=c['predecessor_rejection']
        if rej.get('reason')!='focus_surface_mismatch' or rej.get('task_input_admitted') is not False: errors.append(cid+':predecessor')
    idx={(r['case_id'],r['receipt_kind'],r['validator']):r for r in rows}
    for cid,c in cases.items():
        for kind,ctx in (('stale_main',c['source']),('fresh_modal',c['current'])):
            a=idx.get((cid,kind,'app_class_only'))
            b=idx.get((cid,kind,'surface_bound'))
            if not a or not b:
                errors.append(cid+':missing:'+kind)
                continue
            want_receipt=expected_receipt(ctx,kind)
            for name,r in (('coarse',a),('bound',b)):
                if r.get('case_sha256')!=c['case_sha256']: errors.append(cid+':case_sha:'+kind+':'+name)
                if r.get('current')!=c['current']: errors.append(cid+':current_copy:'+kind+':'+name)
                if r.get('receipt')!=want_receipt: errors.append(cid+':receipt_copy:'+kind+':'+name)
                q=r['receipt']
                if q.get('authority')!='none' or q.get('task_input_granted') is not False or q.get('action_admission_eligible') is not False:
                    errors.append(cid+':authority:'+kind+':'+name)
            if a['status']!='accepted' or a.get('reason') is not None: errors.append(cid+':coarse_not_accept:'+kind)
            if kind=='stale_main':
                if b['status']!='rejected' or b.get('reason')!='surface_mismatch': errors.append(cid+':stale_escape')
            else:
                if b['status']!='accepted' or b.get('reason') is not None: errors.append(cid+':fresh_reject')
    return {'decision':'PASS_MODAL_SURFACE_BINDING_REQUIRED_SCOPED' if not errors else 'FAIL_INTEGRITY_OR_CONTRACT','errors':errors,'rows':len(rows)}

if __name__=='__main__':
    fixture=json.loads(Path(sys.argv[1]).read_text()); rows=json.loads(Path(sys.argv[2]).read_text())
    result=audit(fixture,rows); Path(sys.argv[3]).write_text(json.dumps(result,sort_keys=True,indent=2)+'\n'); print(json.dumps(result))
