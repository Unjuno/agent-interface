import json
from pathlib import Path
H=Path(__file__).resolve().parent; r=json.loads((H/'RESULT.json').read_text())
checks={'decision':r['decision']=='PASS_CURRENTNESS_INVALIDATED_KIND_SCOPED','mixed':r['mixed_streams']==100000 and r['mixed_mismatches']==0,'old':r['parent_domain_streams']==50000 and r['parent_regressions']==0,'new_retained':r['new_kind_events']>0 and r['new_kind_loss_cases']==0,'authority':r['authority_promotions']==0,'formal':(r['formal_invocation'],r['reruns'])==(1,0),'sources':r['source_git_blobs']=={'parent_contract':'404a452aa304b4bde73ec0182450d241e2a744af','#1051_RESULT':'ecae38ae21361ec9696c6ef604841846364dce5b'},'no_actions':all(r[k]==0 for k in ['model_calls','gui_actions','task_input_actions'])}
o={'schema':'currentness_invalidated_kind_audit_v1','checks':checks,'passed':all(checks.values()),'errors':[k for k,v in checks.items() if not v]}; (H/'AUDIT.json').write_text(json.dumps(o,indent=2,sort_keys=True)+'\n'); print('AUDIT_PASS' if o['passed'] else o)
