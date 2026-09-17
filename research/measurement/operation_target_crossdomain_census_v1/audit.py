import json
from pathlib import Path
from census import load,evaluate
H=Path(__file__).resolve().parent; r=json.loads((H/'RESULT.json').read_text()); e=evaluate(load())
checks={
 'decision':r['decision']==e['decision'], 'checks':r['checks']==e['checks'],
 'potential':r['potential_program_opportunities']==21,
 'qualified':r['oracle_qualified_positive_rows']==0,
 'negatives':r['semantic_negative_rows']==0,
 'ops':r['raw_operation_families']==e['raw_operation_families'] and not r['oracle_qualified_operation_families'],
 'split_units':r['independent_episode_units']==6,
 'nonlabels':r['nonlabels']==e['nonlabels'], 'sources':r['sources']==e['sources'],
 'formal':(r['formal_invocation'],r['reruns'])==(1,0),
 'no_actions':all(r[k]==0 for k in ('model_calls','provider_calls','gui_actions','task_input_actions'))}
o={'schema':'operation_target_crossdomain_census_audit_v1','checks':checks,'passed':all(checks.values()),'errors':[k for k,v in checks.items() if not v]}
(H/'AUDIT.json').write_text(json.dumps(o,indent=2,sort_keys=True)+'\n'); print('AUDIT_PASS' if o['passed'] else o)
