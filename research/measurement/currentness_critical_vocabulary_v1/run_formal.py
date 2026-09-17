import json
from pathlib import Path
from common import load,evaluate
H=Path(__file__).resolve().parent; O=H/'RESULT.json'
if O.exists(): raise RuntimeError('RESULT exists')
f=load(); r=evaluate(f); r.update({'schema':'currentness_critical_vocabulary_result_v1','task':f['task'],'base':f['base'],'formal_invocation':1,'reruns':0,'source_git_blobs':f['sources'],'model_calls':0,'gui_actions':0,'task_input_actions':0,'authority_actions':0}); O.write_text(json.dumps(r,indent=2,sort_keys=True)+'\n'); print(r['decision'])
