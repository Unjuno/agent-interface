import json
from pathlib import Path
R=Path(__file__).resolve().parent
f=json.loads((R/'fixture.json').read_text())
assert f['arms']['persistent']['routes']==['cold','reuse','reuse','repair','reuse','reuse']
for name,a in f['arms'].items():
    assert len(a['task_elapsed_ns'])==6
    assert a['preflight_ns']+sum(a['task_elapsed_ns'])==a['expected_final_ns'], name
p=f['arms']['persistent']['preflight_ns']+f['arms']['persistent']['task_elapsed_ns'][0]
q=f['arms']['plain']['preflight_ns']+f['arms']['plain']['task_elapsed_ns'][0]
assert p>q
print('PASS mechanics')
