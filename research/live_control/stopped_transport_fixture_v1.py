"""Synthetic blocked capture runtime for an actual private-socket transport probe."""
import json
import sys
import time
from pathlib import Path
from types import SimpleNamespace
from executor_v8 import Executor
from executor_v3 import DecisionRequired

root=Path(sys.argv[1])
def emit(e):
    e['fixture_emitted_ns']=time.perf_counter_ns()
    with (root/'events.jsonl').open('a') as f:f.write(json.dumps(e)+'\n')
    print(json.dumps(e),flush=True)
class Backend:
    sequence=1
    decoder=SimpleNamespace(frame=b'fixture')
    observed_pointer={'focus':2,'surface':2}
    def validate(self,steps):assert steps==[{'op':'fault'},{'op':'tail'}]
    def execute(self,step,lease,identifier,index):
        assert index==0,'tail must not execute'
        lease.record_interruption(dict(event='owner_release',reason='focus_changed',verified=True))
        raise DecisionRequired()
    def release_all(self):return dict(verified=True,keys_down=[],buttons_down=[])
    def snapshot(self,identifier,index):
        (root/'capture-entered').write_text('entered')
        end=time.monotonic()+10
        while not (root/'release-capture').exists():
            if time.monotonic()>end:raise TimeoutError('probe gate expired')
            time.sleep(.005)
        self.sequence+=1;emit(dict(event='observation',id=identifier,sequence=self.sequence))
backend=Backend();engine=Executor(backend,emit)
try:
    for line in sys.stdin:
        q=json.loads(line);emit(dict(event='command',command=q))
        try:
            if q['op']=='clock':emit(dict(event='clock',runtime_ns=time.perf_counter_ns(),sequence=backend.sequence))
            elif q['op']=='submit':engine.submit(q['id'],q['steps'],q['expected_sequence'],q['valid_until_ns'])
            elif q['op']=='cancel':engine.cancel(q['id'])
            elif q['op']=='finish':engine.close();break
        except ValueError as exc:emit(dict(event='rejected',reason=str(exc)))
finally:engine.close()
