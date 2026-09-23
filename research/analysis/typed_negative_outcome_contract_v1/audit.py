import hashlib,json,sys
from pathlib import Path

def oracle(e):
    if e['freshness']!='CURRENT' or e['completeness']!='COMPLETE' or e.get('contradictory') is True:
        return {'label':'FAILED_UNKNOWN','retryable':False,'required_change':'refresh_evidence','authority_granted':False}
    f=e['family']
    table={
      'SUCCEEDED':(False,'none'),'IN_PROGRESS':(False,'wait_for_completion'),
      'AUTHORITY_REQUIRED':(False,'obtain_authority'),'TARGET_NOT_FOUND':(False,'change_target_or_observe'),
      'CAPABILITY_UNSUPPORTED':(False,'change_capability_or_route'),'CONFLICT':(False,'resolve_conflict'),
      'IMPOSSIBLE_UNDER_CONSTRAINTS':(False,'relax_constraints'),'FAILED_UNKNOWN':(False,'gather_more_evidence')}
    if f=='BLOCKED':
        r=e['retry_context']=='IDENTICAL_RETRY_VALID'; ch='none' if r else 'wait_for_blocker_change'
    else: r,ch=table[f]
    return {'label':f,'retryable':r,'required_change':ch,'authority_granted':False}

def comparator_expected(e):
    if e['status']=='ok': return ('SUCCEEDED',False)
    if e['status']=='working': return ('IN_PROGRESS',False)
    if e['timeout']: return ('BLOCKED',True)
    return ('IMPOSSIBLE_UNDER_CONSTRAINTS',False)

def audit(root_path,formal_path):
    root=Path(root_path); p=json.loads(Path(formal_path).read_text()); errors=[]; checks=0
    fr=json.loads((root/'FREEZE.json').read_text())
    for name,digest in fr['sha256'].items():
        checks+=1
        if hashlib.sha256((root/name).read_bytes()).hexdigest()!=digest: errors.append('source_hash:'+name)
    expected=json.loads((root/'corpus.json').read_text()); rows=p.get('rows',[])
    checks+=1
    if len(rows)!=len(expected): errors.append('row_count')
    if [r.get('row_id') for r in rows] != list(range(len(expected))): errors.append('row_order')
    futile=premature=0
    for i,(e,row) in enumerate(zip(expected,rows)):
        checks+=5
        if row.get('evidence')!=e: errors.append(f'{i}:evidence')
        o=oracle(e)
        if row.get('candidate')!=o: errors.append(f'{i}:candidate')
        if row.get('candidate',{}).get('authority_granted') is not False: errors.append(f'{i}:authority')
        ce=comparator_expected(e); c=row.get('comparator',{})
        if (c.get('label'),c.get('retryable'))!=ce: errors.append(f'{i}:comparator')
        if e['freshness']!='CURRENT' or e['completeness']!='COMPLETE' or e.get('contradictory') is True:
            if o['label']!='FAILED_UNKNOWN': errors.append(f'{i}:uncertainty')
        if c.get('retryable') and not o['retryable']: futile+=1
        if c.get('label')=='IMPOSSIBLE_UNDER_CONSTRAINTS' and o['label'] not in ('IMPOSSIBLE_UNDER_CONSTRAINTS','SUCCEEDED'): premature+=1
    checks+=5
    if futile<1: errors.append('missing_futile_retry')
    if premature<1: errors.append('missing_premature_terminal')
    if p.get('formal_invocations')!=1 or p.get('reruns')!=0 or p.get('replacements')!=0 or p.get('tuning')!=0: errors.append('execution_discipline')
    return {'decision':'PASS_TYPED_NEGATIVE_OUTCOME_CONTRACT_SCOPED' if not errors else 'FAIL_CONTRACT_OR_INTEGRITY',
            'errors':errors,'checks':checks,'row_count':len(rows),'futile_retry_counterexamples':futile,
            'premature_terminal_counterexamples':premature,'formal_sha256':hashlib.sha256(Path(formal_path).read_bytes()).hexdigest()}
if __name__=='__main__':
    if len(sys.argv)!=3: raise SystemExit('usage: audit.py ROOT FORMAL')
    a=audit(sys.argv[1],sys.argv[2]); print(json.dumps(a,sort_keys=True,indent=2)); raise SystemExit(bool(a['errors']))
