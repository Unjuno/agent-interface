import hashlib,itertools,json,sys
from pathlib import Path

BOOLS=(False,True); RESULTS=('NONE','KNOWN','UNKNOWN')

def oracle(s):
    if s['task_active'] is False: d='CANCELED'
    elif s['interrupt_resolved'] is False: d='WAIT_INTERRUPT'
    elif s['pending_result']=='UNKNOWN': d='RECONCILE_RESULT'
    elif s['source_fresh'] is False: d='YIELD_STALE'
    elif s['queue_version_same'] is False: d='REPLAN_QUEUE'
    elif s['target_identity_same'] is False: d='REVALIDATE_TARGET'
    else: d='RESUME'
    return d

def safe(s):
    return (s['task_active'] is True and s['interrupt_resolved'] is True and
            s['pending_result'] in ('NONE','KNOWN') and s['source_fresh'] is True and
            s['queue_version_same'] is True and s['target_identity_same'] is True)

def expected_states():
    rows=[]
    for vals in itertools.product(BOOLS,BOOLS,BOOLS,BOOLS,BOOLS,RESULTS):
        ir,ta,sf,qs,ts,pr=vals
        rows.append({'state_id':len(rows),'interrupt_resolved':ir,'task_active':ta,'source_fresh':sf,
          'queue_version_same':qs,'target_identity_same':ts,'pending_result':pr})
    return rows

def audit(root,formal):
    root=Path(root); p=json.loads(Path(formal).read_text()); errors=[]; checks=0
    freeze=json.loads((root/'FREEZE.json').read_text())
    for name,digest in freeze['sha256'].items():
        checks+=1
        if hashlib.sha256((root/name).read_bytes()).hexdigest()!=digest: errors.append('source_hash:'+name)
    exp=expected_states(); rows=p.get('rows',[])
    checks+=3
    if len(rows)!=96: errors.append('row_count')
    if [r.get('state',{}).get('state_id') for r in rows]!=list(range(96)): errors.append('state_ids')
    if [r.get('state') for r in rows]!=exp: errors.append('state_corpus')
    unsafe={'POP_ONLY':0,'QUEUE_VERSION_ONLY':0,'EVIDENCE_BOUND_RESUME':0}
    safe_resume={'POP_ONLY':0,'QUEUE_VERSION_ONLY':0,'EVIDENCE_BOUND_RESUME':0}
    false_refusal=0; unknown_candidate_resumes=0; authority=0
    candidate_counts={}
    for i,(s,r) in enumerate(zip(exp,rows)):
        truth=safe(s); checks+=9
        if r.get('safe_resume_truth') is not truth: errors.append(f'{i}:truth')
        outs=r.get('outputs',{})
        for name in ('POP_ONLY','QUEUE_VERSION_ONLY','EVIDENCE_BOUND_RESUME'):
            o=outs.get(name,{})
            if o.get('input_authority') is not False: authority+=1; errors.append(f'{i}:{name}:authority')
            resume=o.get('decision')=='RESUME'
            if resume and not truth: unsafe[name]+=1
            if resume and truth: safe_resume[name]+=1
        co=outs.get('EVIDENCE_BOUND_RESUME',{})
        want=oracle(s)
        if co.get('decision')!=want or co.get('resume_eligible')!=(want=='RESUME'):
            errors.append(f'{i}:candidate')
        candidate_counts[want]=candidate_counts.get(want,0)+1
        if truth and co.get('decision')!='RESUME': false_refusal+=1
        if s['task_active'] and s['interrupt_resolved'] and s['pending_result']=='UNKNOWN' and co.get('decision')=='RESUME':
            unknown_candidate_resumes+=1
    checks+=8
    if unsafe['EVIDENCE_BOUND_RESUME']!=0: errors.append('candidate_unsafe_resume')
    if safe_resume['EVIDENCE_BOUND_RESUME']!=2: errors.append('candidate_safe_resume')
    if false_refusal!=0: errors.append('candidate_false_refusal')
    if unsafe['POP_ONLY']<1: errors.append('pop_no_discriminator')
    if unsafe['QUEUE_VERSION_ONLY']<1: errors.append('queue_no_discriminator')
    if unknown_candidate_resumes!=0: errors.append('unknown_result_resumed')
    if p.get('formal_invocations')!=1 or p.get('reruns')!=0 or p.get('replacements')!=0 or p.get('tuning')!=0:
        errors.append('execution_discipline')
    decision='PASS_INTERRUPT_STACK_RESUME_CONTRACT_SCOPED' if not errors else 'FAIL_CONTRACT_OR_INTEGRITY'
    return {'decision':decision,'errors':errors,'checks':checks,'row_count':len(rows),
      'unsafe_resume_counts':unsafe,'safe_resume_counts':safe_resume,'candidate_false_refusal':false_refusal,
      'unknown_candidate_resumes':unknown_candidate_resumes,'authority_violations':authority,
      'candidate_decision_counts':candidate_counts,'formal_sha256':hashlib.sha256(Path(formal).read_bytes()).hexdigest()}

if __name__=='__main__':
    if len(sys.argv)!=3: raise SystemExit('usage: audit.py ROOT FORMAL')
    a=audit(sys.argv[1],sys.argv[2]); print(json.dumps(a,sort_keys=True,indent=2)); raise SystemExit(bool(a['errors']))
