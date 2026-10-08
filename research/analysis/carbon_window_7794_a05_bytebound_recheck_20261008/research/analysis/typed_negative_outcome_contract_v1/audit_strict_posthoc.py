"""Postformal audit addendum. Does not alter the frozen first audit or scientific corpus."""
import json,sys
from pathlib import Path
from audit import audit

def schema_errors(formal_path):
    p=json.loads(Path(formal_path).read_text()); errors=[]
    for i,row in enumerate(p.get('rows',[])):
        e=row.get('evidence',{})
        allowed={'IDENTICAL_RETRY_VALID','REQUIRES_CHANGE'} if e.get('family')=='BLOCKED' else {'REQUIRES_CHANGE'}
        if e.get('retry_context') not in allowed: errors.append(f'{i}:retry_context_schema')
        if e.get('freshness') not in {'CURRENT','STALE'}: errors.append(f'{i}:freshness_schema')
        if e.get('completeness') not in {'COMPLETE','INCOMPLETE'}: errors.append(f'{i}:completeness_schema')
        if type(e.get('timeout')) is not bool or type(e.get('contradictory')) is not bool: errors.append(f'{i}:boolean_schema')
    return errors
if __name__=='__main__':
    if len(sys.argv)!=3: raise SystemExit('usage: audit_strict_posthoc.py ROOT FORMAL')
    base=audit(sys.argv[1],sys.argv[2]); extra=schema_errors(sys.argv[2]);
    result={'frozen_audit_errors':base['errors'],'schema_errors':extra,'pass':not base['errors'] and not extra}
    print(json.dumps(result,sort_keys=True,indent=2)); raise SystemExit(not result['pass'])
