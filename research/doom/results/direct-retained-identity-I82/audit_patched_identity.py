import hashlib,json
from pathlib import Path
root=Path(__file__).resolve().parent
baseline=json.loads((root/'candidate-results.json').read_text(encoding='utf8'))
patched=json.loads((root/'patched-candidate-results.json').read_text(encoding='utf8'))
raw=json.loads((root/'raw-cases.json').read_text(encoding='utf8'))
assert len(raw['cases'])==len(baseline['results'])==len(patched['results'])==8
b={x['case']:x['result'] for x in baseline['results']}; p={x['case']:x['result'] for x in patched['results']}
errors=[]; repaired=[]
for case in raw['cases']:
    name=case['case']; base=b[name]['measurement_ready']; after=p[name]['measurement_ready']
    expected={'valid_nonempty_string':True,'field_absent_both':False,'explicit_null_both':False,'mismatch_nonempty_strings':False,'missing_release_token':False}.get(name,base)
    if after is not expected: errors.append({'case':name,'expected':expected,'actual':after})
    if name in {'field_absent_both','explicit_null_both'} and base and not after: repaired.append(name)
    if name not in {'field_absent_both','explicit_null_both'} and after is not base: errors.append({'case':name,'error':'unintended_readiness_change','before':base,'after':after})
summary={'schema':'pr7356-intent-token-identity-boundary-patched-audit-v1','raw_sha256':hashlib.sha256((root/'raw-cases.json').read_bytes()).hexdigest(),'baseline_results_sha256':hashlib.sha256((root/'candidate-results.json').read_bytes()).hexdigest(),'patched_results_sha256':hashlib.sha256((root/'patched-candidate-results.json').read_bytes()).hexdigest(),'patched_source_sha256':patched['source_sha256'],'cases':8,'identity_false_accepts_repaired':repaired,'other_case_readiness_preserved':6,'errors':errors,'decision':'PASS_NARROW_IDENTITY_GUARD' if not errors and len(repaired)==2 else 'FAIL'}
(root/'patched-audit-result.json').write_text(json.dumps(summary,indent=2)+'\n',encoding='utf8')
print(json.dumps(summary,indent=2))
assert summary['decision']=='PASS_NARROW_IDENTITY_GUARD'
