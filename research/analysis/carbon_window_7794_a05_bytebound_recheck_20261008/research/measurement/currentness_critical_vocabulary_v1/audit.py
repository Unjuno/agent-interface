import json
from pathlib import Path
from common import load,evaluate
H=Path(__file__).resolve().parent; r=json.loads((H/'RESULT.json').read_text()); f=load(); e=evaluate(f)
checks={'decision':r['decision']==e['decision'],'cases':r['required_cases']==e['required_cases'],'controls':r['controls']==e['controls'],'gap':r['gap_retained']==e['gap_retained'],'formal':(r['formal_invocation'],r['reruns'])==(1,0),'sources':r['source_git_blobs']==f['sources'],'no_actions':all(r[k]==0 for k in ['model_calls','gui_actions','task_input_actions','authority_actions'])}
o={'schema':'currentness_critical_vocabulary_audit_v1','checks':checks,'passed':all(checks.values()),'errors':[k for k,v in checks.items() if not v]}; (H/'AUDIT.json').write_text(json.dumps(o,indent=2,sort_keys=True)+'\n'); print('AUDIT_PASS' if o['passed'] else o)
