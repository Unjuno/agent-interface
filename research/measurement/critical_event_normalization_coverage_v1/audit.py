from __future__ import annotations
import json
from pathlib import Path
from common import load_fixture,evaluate,EXPECTED_BLOBS
HERE=Path(__file__).resolve().parent
r=json.loads((HERE/'RESULT.json').read_text()); expected=evaluate(load_fixture())
checks={
'decision':r['decision']==expected['decision'],
'counts':(r['required_edges'],r['mapped_required_edges'])==(expected['required_edges'],expected['mapped_required_edges']),
'missing':r['missing_required_edges']==expected['missing_required_edges'],
'formal':(r['formal_invocation'],r['reruns'])==(1,0),
'sources':r['source_git_blobs']==EXPECTED_BLOBS,
'scope':r['mapping_evidence_scope']=='reachable current-main source/code-search only',
'no_actions':all(r[k]==0 for k in ['authority_actions','model_calls','gui_actions','task_input_actions'])}
out={'schema':'critical_event_normalization_coverage_audit_v1','checks':checks,'passed':all(checks.values()),'errors':[k for k,v in checks.items() if not v]}
(HERE/'AUDIT.json').write_text(json.dumps(out,indent=2,sort_keys=True)+'\n'); print('AUDIT_PASS' if out['passed'] else out)
