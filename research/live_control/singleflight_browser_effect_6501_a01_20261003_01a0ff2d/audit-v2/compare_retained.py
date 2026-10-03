"""Finite ordinary before/after diagnostics on independent copies of retained A01."""
import hashlib,json,sys
from pathlib import Path
from regressions import CLIENT,SERVER,apply,extra_copies,load,specifications
root=Path(__file__).resolve().parent
before=load(root/'inputs/audit_v1.py');after=load(root/'audit_v2.py')
baseline_before=before.audit(CLIENT,SERVER);baseline_after=after.audit(CLIENT,SERVER)
assert not baseline_before['errors'] and not baseline_after['errors']
assert all(baseline_before[k]==baseline_after[k] for k in ('rows','waiters','summary','cohort_elapsed_ns','equivalent_cohort_latency_gain_observed'))
specs=specifications();rows=[]
for spec in specs:
    c,s=apply(spec)
    old=before.audit(c,s);new=after.audit(c,s)
    rows.append({'specification':spec,'before_errors':old['errors'],'after_errors':new['errors'],
                 'before_latency_claim':old['equivalent_cohort_latency_gain_observed'],'after_latency_claim':new['equivalent_cohort_latency_gain_observed']})
assert sum(not r['before_errors'] for r in rows)==72
assert all(r['after_errors'] and r['after_latency_claim'] is None for r in rows)
extra=[]
for label,c,s in extra_copies():
    old=before.audit(c,s);new=after.audit(c,s)
    extra.append({'label':label,'before_errors':old['errors'],'after_errors':new['errors'],
                  'client_copy_sha256':hashlib.sha256(json.dumps(c,sort_keys=True,separators=(',',':'),ensure_ascii=True).encode()).hexdigest(),
                  'server_copy_sha256':hashlib.sha256(json.dumps(s,sort_keys=True,separators=(',',':'),ensure_ascii=True).encode()).hexdigest()})
assert sum(not r['before_errors'] for r in extra)==10 and all(r['after_errors'] for r in extra)
controls_before=before.controls(CLIENT,SERVER);controls_after=after.controls(CLIENT,SERVER)
assert all(r['rejected'] for r in controls_before+controls_after)
result={'schema':'6920-browser-retained-audit-repair-v2','kind':'ordinary retained-data correction, not a new browser trial',
 'input_sha256':{name:hashlib.sha256((root/'inputs'/name).read_bytes()).hexdigest() for name in ('client.json','server.json','audit_v1.py')},
 'after_source_sha256':hashlib.sha256((root/'audit_v2.py').read_bytes()).hexdigest(),
 'specification_sha256':hashlib.sha256(json.dumps(specs,sort_keys=True,separators=(',',':'),ensure_ascii=True).encode()).hexdigest(),
 'original_before':baseline_before,'original_after':baseline_after,'review_family':rows,'extra_regressions':extra,
 'original_controls_before':controls_before,'original_controls_after':controls_after,
 'baseline_accepted_review_copies':72,'candidate_rejected_review_copies':72,'baseline_accepted_extra_copies':10,
 'candidate_rejected_extra_copies':12,'original_formal_outcomes_changed':False,'consumed_producer_replayed':False}
with Path(sys.argv[1]).open('x',encoding='utf-8') as out:json.dump(result,out,indent=2);out.write('\n')
print(json.dumps({k:v for k,v in result.items() if k not in ('review_family','extra_regressions','original_controls_before','original_controls_after','original_before','original_after')}))
