import json
from pathlib import Path
from census import load_fixture,evaluate
H=Path(__file__).resolve().parent
r=json.loads((H/'RESULT.json').read_text()); e=evaluate(load_fixture())
checks={
 'decision':r['decision']==e['decision'],
 'checks':r['checks']==e['checks'],
 'failed_requirements':r['failed_requirements']==e['failed_requirements'],
 'sources':r['sources']==e['sources'],
 'formal':(r['formal_invocation'],r['reruns'])==(1,0),
 'no_actions':all(r[k]==0 for k in ('model_calls','gui_actions','task_input_actions','provider_calls')),
 'final_effect_not_operation_oracle':r['observed']['independent_final_effect_oracle'] is True and r['observed']['independent_operation_target_semantic_oracle'] is False,
 'stale_binding_not_relabelled':r['observed']['stale_binding_negative_events']==1 and r['observed']['stale_binding_negative_is_operation_label'] is False,
}
o={'schema':'operation_target_retained_data_census_audit_v1','checks':checks,'passed':all(checks.values()),'errors':[k for k,v in checks.items() if not v]}
(H/'AUDIT.json').write_text(json.dumps(o,indent=2,sort_keys=True)+'\n')
print('AUDIT_PASS' if o['passed'] else o)
