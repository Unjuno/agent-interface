import hashlib,json,sys
from pathlib import Path

def audit(rows, source_hashes=None, root=None):
    errors=[]
    if len(rows)!=6: errors.append('row_count')
    ids=[r['case_id'] for r in rows]
    if len(ids)!=len(set(ids)): errors.append('duplicate_ids')
    b=[r for r in rows if r['policy']=='current_generic_yield']
    c=[r for r in rows if r['policy']=='focus_recovery_adapter']
    if len(b)!=3 or len(c)!=3: errors.append('strata')
    for r in b:
        z=r['result']
        if z.get('status')!='safe_yield' or z.get('reason')!='execution_failed':errors.append('baseline_result')
        if r['recovery_queries']!=0:errors.append('baseline_recovery')
        if r['post_rejection_task_submits']!=0:errors.append('baseline_retry')
        if r['original_submit_delta']!=1:errors.append('baseline_submit_shape')
    for r in c:
        z=r['result']; rc=z.get('recovery_context',{})
        if z.get('status')!='safe_yield' or z.get('reason')!='focus_mismatch':errors.append('candidate_result')
        if r['recovery_queries']!=1:errors.append('candidate_recovery_count')
        if r['post_rejection_task_submits']!=0:errors.append('candidate_retry')
        if r['original_submit_delta']!=1:errors.append('candidate_submit_shape')
        if rc.get('focus')!='B' or rc.get('surface')!='B':errors.append('candidate_stale')
        if rc.get('authority')!='none' or rc.get('task_input_granted') is not False:errors.append('candidate_authority')
    if source_hashes is not None:
        for rel,want in source_hashes.items():
            got=hashlib.sha256((Path(root)/rel).read_bytes()).hexdigest()
            if got!=want:errors.append('source:'+rel)
    return {'decision':'PASS_INTEGRATED_FOCUS_RECOVERY_RESULT_SCOPED' if not errors else 'FAIL_INTEGRITY','errors':errors,'rows':len(rows)}

def main():
    rows=json.loads(Path(sys.argv[1]).read_text()); freeze=json.loads(Path(sys.argv[2]).read_text())
    out=audit(rows,freeze['source_sha256'],freeze['source_root'])
    Path(sys.argv[3]).write_text(json.dumps(out,indent=2,sort_keys=True)+'\n');print(json.dumps(out))
if __name__=='__main__':main()
