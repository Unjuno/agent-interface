import hashlib,json,sys
from pathlib import Path
from regressions import CLIENT,SERVER,apply,load,specifications
root=Path(__file__).resolve().parent
family=sys.argv[1];prefix={'cohort':'cohort-zero/','generation':'close-','delivery':'delivery-absent/'}[family]
candidate=load(root/'audit_v2.py')
baseline=candidate.audit(CLIENT,SERVER);assert not baseline['errors']
results=[]
for spec in specifications():
    if spec['label'].startswith(prefix):
        result=candidate.audit(*apply(spec));assert result['errors'],spec['label']
        results.append({'label':spec['label'],'errors':result['errors'],'latency_claim':result['equivalent_cohort_latency_gain_observed']})
record={'family':family,'candidate_sha256':hashlib.sha256((root/'audit_v2.py').read_bytes()).hexdigest(),'original_errors':baseline['errors'],'rejected':len(results),'results':results}
out=root/'evidence'/('family-'+family+'.json')
with out.open('x',encoding='utf-8') as f:json.dump(record,f,indent=2);f.write('\n')
with (root/'evidence'/('family-'+family+'-source.py')).open('xb') as f:f.write((root/'audit_v2.py').read_bytes())
print(json.dumps({k:v for k,v in record.items() if k!='results'}))
