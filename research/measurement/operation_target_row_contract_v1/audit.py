import json
from pathlib import Path
H=Path(__file__).resolve().parent;r=json.loads((H/'RESULT.json').read_text())
checks={'decision':r['decision']=='PASS_OPERATION_TARGET_ROW_CONTRACT_SCOPED','rows':r['rows']==120000 and r['valid_rows']>0 and r['invalid_rows']>0,'agreement':r['candidate_oracle_mismatches']==0 and r['invalid_accepted']==0,'dataset':r['dataset_cases']==20000 and r['dataset_mismatches']==0 and r['split_leakage_accepted']==0,'authority':r['authority_errors']==0,'formal':(r['formal_invocation'],r['reruns'])==(1,0),'no_actions':all(r[k]==0 for k in ('model_calls','gui_actions','task_input_actions')),'no_real_claim':r['real_rows_counted_toward_1015']==0}
o={'schema':'operation_target_row_contract_audit_v1','checks':checks,'passed':all(checks.values()),'errors':[k for k,v in checks.items() if not v]};(H/'AUDIT.json').write_text(json.dumps(o,indent=2,sort_keys=True)+'\n');print('AUDIT_PASS' if o['passed'] else o)
