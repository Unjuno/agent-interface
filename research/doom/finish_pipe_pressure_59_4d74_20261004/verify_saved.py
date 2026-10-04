"""Read-only verification of retained construction bytes and measured boundary."""
from pathlib import Path
import hashlib,json
root=Path(__file__).resolve().parent
manifest=json.loads((root/'FILES.json').read_bytes())['members']
for name,pin in manifest.items():
    data=(root/name).read_bytes()
    assert len(data)==pin['bytes'] and hashlib.sha256(data).hexdigest()==pin['sha256'],name
freeze=json.loads((root/'run/FREEZE.json').read_bytes())
for name,digest in freeze['files'].items():
    assert hashlib.sha256((root/'run'/name).read_bytes()).hexdigest()==digest,name
before=json.loads((root/'run/BEFORE_EXTERNAL_RELEASE.json').read_bytes())
after=json.loads((root/'run/AFTER_EXTERNAL_RELEASE.json').read_bytes())
assert before['filled_pipe_bytes']==65536
assert before['observation_interval_s']==.5
assert before['cleanup_thread_alive'] and before['child_poll'] is None
assert before['wait_calls']==[] and not before['planner_closed'] and before['helper_result']=={}
assert not after['cleanup_thread_alive'] and after['child_exit']==-9 and after['planner_closed']
assert after['result']=={'error_type':'ValueError','error':'original controller fault'}
assert json.loads((root/'run/RESULT.json').read_bytes())['exit_code']==0
print('PASS_SAVED_COUNTEREXAMPLE_CUSTODY',len(manifest),'members; cleanup reachability FAIL retained')
