import json
from pathlib import Path
from census import load_fixture,evaluate
H=Path(__file__).resolve().parent
out=evaluate(load_fixture())
out.update({'formal_invocation':1,'reruns':0,'model_calls':0,'gui_actions':0,'task_input_actions':0,'provider_calls':0})
(H/'RESULT.json').write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
print(out['decision'])
