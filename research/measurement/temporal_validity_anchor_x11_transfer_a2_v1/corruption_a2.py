import copy,json
from pathlib import Path
from audit_a2 import verify
HERE=Path(__file__).resolve().parent
r=json.loads((HERE/'RESULT.json').read_text()); controls=[]
def t(name,mut):
 x=copy.deepcopy(r);mut(x);o=verify(x);controls.append({'name':name,'rejected':not o['audit_pass'],'errors':o['errors']})
t('drop_batch_manifest',lambda x:x['batch_manifest'].pop())
t('fake_batch_invocations',lambda x:x.__setitem__('formal_batch_invocations',7))
t('source_effect',lambda x:x.__setitem__('source_effects',1))
t('drop_evidence_effect',lambda x:x.__setitem__('evidence_effects',23))
t('negative_admit',lambda x:x.__setitem__('negative_admissions',1))
t('duration_false',lambda x:x.__setitem__('durations_exact',False))
t('latency_over_gate',lambda x:x.__setitem__('future_to_effect_p95_ns',10_000_001))
assert all(x['rejected'] for x in controls),controls
(HERE/'CORRUPTION_A2.json').write_text(json.dumps({'controls':controls,'rejected':sum(x['rejected'] for x in controls),'total':len(controls)},indent=2,sort_keys=True)+'\n')
print(json.dumps(controls,indent=2))
