import json, copy, sys
from pathlib import Path
root=Path(__file__).resolve().parent
R=json.loads((root/'RESULT.json').read_text())
errors=[]
if R['rows']!=250000: errors.append('rows')
if R['formal_invocations']!=1 or R['reruns']!=0 or R['replacements']!=0 or R['tuning']!=0: errors.append('invocation')
if R['candidate_oracle_mismatch']!=0: errors.append('mismatch')
if R['unsafe_naive_suppressions']<=0: errors.append('no_discriminator')
if R['local_resolutions'] != R['categories']['CURRENT_TRUE']+R['categories']['CURRENT_FALSE']: errors.append('local_count')
if R['escalations'] != R['rows']-R['local_resolutions']: errors.append('escalation_count')
if R['decision']!='PASS_O4_LOCAL_VERIFY_ESCALATION_CONTRACT_SCOPED': errors.append('decision')
expected={'true':'LOCAL_TRUE','false':'LOCAL_FALSE','unknown':'ESCALATE_UNKNOWN','stale':'ESCALATE_STALE_OBSERVATION','intent':'ESCALATE_INTENT_MISMATCH','missing':'ESCALATE_MISSING','forged':'ESCALATE_AUTHORITY_INVALID'}
for name,a,b in R['directed']:
    if a!=expected[name] or b!=expected[name]: errors.append('directed:'+name)
def ok(x):
    if x['rows']!=250000 or x['formal_invocations']!=1 or x['reruns']!=0 or x['replacements']!=0 or x['tuning']!=0: return False
    if x['candidate_oracle_mismatch']!=0 or x['unsafe_naive_suppressions']<=0: return False
    if x['local_resolutions'] != x['categories']['CURRENT_TRUE']+x['categories']['CURRENT_FALSE']: return False
    if x['escalations'] != x['rows']-x['local_resolutions']: return False
    if x['decision']!='PASS_O4_LOCAL_VERIFY_ESCALATION_CONTRACT_SCOPED': return False
    return all(a==expected[n] and b==expected[n] for n,a,b in x['directed'])
controls={}
for name,fn in {
 'mismatch':lambda x:x.__setitem__('candidate_oracle_mismatch',1),
 'unsafe_zero':lambda x:x.__setitem__('unsafe_naive_suppressions',0),
 'local_count':lambda x:x.__setitem__('local_resolutions',x['local_resolutions']+1),
 'decision':lambda x:x.__setitem__('decision','FAIL'),
 'invocation':lambda x:x.__setitem__('formal_invocations',2),
}.items():
    x=copy.deepcopy(R); fn(x); controls[name]=not ok(x)
if not all(controls.values()): errors.append('corruption')
A={'pass':not errors,'errors':errors,'corruption_controls':controls,'checked_rows':R['rows'],'result_digest':R['digest']}
(root/'AUDIT.json').write_text(json.dumps(A,indent=2,sort_keys=True)+'\n')
print(json.dumps(A,indent=2,sort_keys=True))
raise SystemExit(0 if A['pass'] else 1)
