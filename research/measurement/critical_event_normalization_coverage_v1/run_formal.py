from __future__ import annotations
import json
from pathlib import Path
from common import load_fixture,evaluate
HERE=Path(__file__).resolve().parent
OUT=HERE/'RESULT.json'
if OUT.exists(): raise RuntimeError('RESULT exists')
f=load_fixture(); r=evaluate(f)
r.update({'schema':'critical_event_normalization_coverage_result_v1','task':f['task'],'formal_invocation':1,'reruns':0,'base':f['base'],'source_git_blobs':{k:v['git_blob'] for k,v in f['sources'].items()},'mapping_evidence_scope':'reachable current-main source/code-search only','authority_actions':0,'model_calls':0,'gui_actions':0,'task_input_actions':0})
OUT.write_text(json.dumps(r,indent=2,sort_keys=True)+'\n')
print(r['decision'])
