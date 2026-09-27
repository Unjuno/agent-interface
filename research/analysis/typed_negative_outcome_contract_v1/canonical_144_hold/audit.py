from __future__ import annotations
import copy, hashlib, json, pathlib, sys

LABELS = {
    'SUCCEEDED','IN_PROGRESS','BLOCKED','AUTHORITY_REQUIRED','TARGET_NOT_FOUND',
    'CAPABILITY_UNSUPPORTED','CONFLICT','IMPOSSIBLE_UNDER_CONSTRAINTS','FAILED_UNKNOWN'
}
REQ = {
    'SUCCEEDED':'NONE','IN_PROGRESS':'WAIT','BLOCKED':'WAIT_OR_RETRY',
    'AUTHORITY_REQUIRED':'ACQUIRE_AUTHORITY','TARGET_NOT_FOUND':'NEW_OBSERVATION_OR_TARGET',
    'CAPABILITY_UNSUPPORTED':'SELECT_DECLARED_FALLBACK','CONFLICT':'REFRESH_STATE',
    'IMPOSSIBLE_UNDER_CONSTRAINTS':'REPLAN_CONSTRAINTS','FAILED_UNKNOWN':'NEW_OBSERVATION'
}


def expected(inp):
    if inp['freshness'] != 'CURRENT' or inp['completeness'] != 'COMPLETE':
        return {'label':'FAILED_UNKNOWN','identical_retry_allowed':False,'required_change':'NEW_OBSERVATION','authority_granted':False}
    label=inp['family']
    return {'label':label,'identical_retry_allowed': label=='BLOCKED' and inp['retry_context']=='IDENTICAL_RETRY_VALID', 'required_change':REQ[label], 'authority_granted':False}

def validate(doc, expected_sha=None):
    errors=[]
    if doc.get('schema')!='agent-interface/typed-negative-outcome-contract-v1': errors.append('schema')
    if doc.get('formal_invocations')!=1 or doc.get('reruns')!=0 or doc.get('replacements')!=0 or doc.get('tuning')!=0: errors.append('allocation_counts')
    rows=doc.get('rows')
    if not isinstance(rows,list) or len(rows)!=144: errors.append('row_count'); return errors
    ids=[x.get('input',{}).get('row_id') for x in rows]
    if len(set(ids))!=144: errors.append('row_ids')
    futile=0; premature=0
    for row in rows:
        inp=row['input']; cand=row['candidate']; comp=row['comparator']
        exp=expected(inp)
        if cand!=exp: errors.append('candidate:'+inp['row_id'])
        if cand.get('authority_granted') is not False: errors.append('authority:'+inp['row_id'])
        if inp['freshness']!='CURRENT' or inp['completeness']!='COMPLETE':
            if cand['label']!='FAILED_UNKNOWN': errors.append('uncertainty:'+inp['row_id'])
        # comparator counterexamples relative to oracle
        if comp.get('identical_retry_allowed') and not exp['identical_retry_allowed']:
            futile += 1
        if comp.get('label')=='IMPOSSIBLE_UNDER_CONSTRAINTS' and exp['label']!='IMPOSSIBLE_UNDER_CONSTRAINTS':
            premature += 1
    if futile<1: errors.append('no_futile_retry_counterexample')
    if premature<1: errors.append('no_premature_terminal_counterexample')
    return errors

def mutation_controls(doc):
    muts=[]
    def check(name,fn):
        d=copy.deepcopy(doc); fn(d); muts.append({'name':name,'rejected':bool(validate(d))})
    check('stale_to_current',lambda d:d['rows'][1]['input'].__setitem__('freshness','CURRENT'))
    check('complete_to_incomplete',lambda d:d['rows'][0]['input'].__setitem__('completeness','INCOMPLETE'))
    check('candidate_label',lambda d:d['rows'][0]['candidate'].__setitem__('label','BLOCKED'))
    check('required_change',lambda d:d['rows'][0]['candidate'].__setitem__('required_change','WAIT'))
    check('authority',lambda d:d['rows'][0]['candidate'].__setitem__('authority_granted',True))
    check('retry',lambda d:d['rows'][0]['candidate'].__setitem__('identical_retry_allowed',True))
    check('duplicate_row',lambda d:d['rows'].__setitem__(1,copy.deepcopy(d['rows'][0])))
    check('missing_row',lambda d:d['rows'].pop())
    check('formal_count',lambda d:d.__setitem__('formal_invocations',2))
    check('rerun_count',lambda d:d.__setitem__('reruns',1))
    check('row_id',lambda d:d['rows'][0]['input'].__setitem__('row_id','r999'))
    check('family',lambda d:d['rows'][0]['input'].__setitem__('family','CONFLICT'))
    return muts

def main(path,out):
    raw=pathlib.Path(path).read_bytes(); doc=json.loads(raw)
    errors=validate(doc)
    controls=mutation_controls(doc)
    if not all(x['rejected'] for x in controls): errors.append('mutation_control')
    audit={'audit_pass':not errors,'errors':errors,'raw_sha256':hashlib.sha256(raw).hexdigest(),'row_count':len(doc.get('rows',[])),'mutation_controls':controls}
    pathlib.Path(out).write_text(json.dumps(audit,indent=2,sort_keys=True)+'\n')
    print(json.dumps(audit,sort_keys=True))
    raise SystemExit(0 if not errors else 1)
if __name__=='__main__':
    if len(sys.argv)!=3: raise SystemExit('usage: audit.py RAW.json AUDIT.json')
    main(sys.argv[1],sys.argv[2])
