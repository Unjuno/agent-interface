import hashlib, json
from pathlib import Path
root=Path(__file__).resolve().parent
raw=json.loads((root/'raw-cases.json').read_text(encoding='utf8'))
candidate=json.loads((root/'candidate-results.json').read_text(encoding='utf8'))
assert candidate['source_sha256']==raw['source_sha256']
by_candidate={r['case']:r['result'] for r in candidate['results']}
violations=[]; checks=[]
for case in raw['cases']:
    name=case['case']; result=by_candidate[name]
    if name=='valid_nonempty_string': expected=True
    elif name in {'field_absent_both','explicit_null_both','mismatch_nonempty_strings','missing_release_token'}: expected=False
    else: continue # token type/empty policy is not explicit in the source contract
    passed=(result.get('measurement_ready') is expected)
    checks.append({'case':name,'expected_ready':expected,'actual_ready':result.get('measurement_ready'),'pass':passed})
    if not passed: violations.append({'case':name,'expected_ready':expected,'actual':result})
summary={'schema':'pr7356-intent-token-identity-boundary-audit-v1','raw_sha256':hashlib.sha256((root/'raw-cases.json').read_bytes()).hexdigest(),'candidate_sha256':hashlib.sha256((root/'candidate-results.json').read_bytes()).hexdigest(),'source_sha256':raw['source_sha256'],'case_count':len(raw['cases']),'contract_scoped_checks':len(checks),'contract_scoped_passes':sum(c['pass'] for c in checks),'violations':violations,'exploratory_untyped_cases':sorted(set(by_candidate)-{c['case'] for c in checks}),'decision':'FAIL_IDENTITY_ABSENCE_ACCEPTED' if violations else 'PASS'}
(root/'audit-result.json').write_text(json.dumps(summary,indent=2)+'\n',encoding='utf8')
print(json.dumps(summary,indent=2))
assert len(violations)==2 and {v['case'] for v in violations}=={'field_absent_both','explicit_null_both'}
