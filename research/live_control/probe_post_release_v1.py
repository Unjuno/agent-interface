"""Synthetic executor integration: no resumed input, retained cause, passive errors."""
import json
import time
from pathlib import Path
from types import SimpleNamespace
from executor_v7 import Executor
from executor_v3 import DecisionRequired
from report_pages_v2 import digest

HERE=Path(__file__).resolve().parent
out=HERE/'results/post-release-01';out.mkdir(exist_ok=False)
rows=[]
for mode in ('stable','changing','snapshot_error','release_failed','unrelated_reason','normal'):
    events=[]
    class Backend:
        sequence=1
        snapshots=0
        observed_pointer={'focus':10,'surface':10}
        decoder=SimpleNamespace(frame=b'initial')
        def validate(self,steps):pass
        def execute(self,step,lease,identifier,index):
            if mode=='normal':return
            if index:raise AssertionError('tail executed')
            if mode!='unrelated_reason':
                lease.record_interruption(dict(event='owner_release',reason='focus_changed',verified=True))
            raise DecisionRequired('unrelated' if mode=='unrelated_reason' else '')
        def release_all(self):
            self.released=True
            return dict(verified=mode!='release_failed',keys_down=[],buttons_down=[])
        def snapshot(self,identifier,index):
            assert self.released
            self.snapshots+=1
            if mode=='snapshot_error':raise RuntimeError('capture unavailable')
            self.sequence+=1
            self.decoder.frame=b'stable' if mode=='stable' else bytes([self.snapshots])
            events.append(dict(event='observation',sequence=self.sequence))
    backend=Backend();engine=Executor(backend,events.append)
    try:
        engine.submit('test',[dict(op='one'),dict(op='tail')],1,time.perf_counter_ns()+5_000_000_000)
        with engine.lock:job=engine.active
        if job:
            job[2].join(2);assert not job[2].is_alive()
        terminal=events[-1];assert terminal['event']=='terminal'
        post=terminal['post_release_observation']
        if mode in ('stable','changing','snapshot_error'):
            assert terminal['status']=='needs_decision' and terminal['decision_reason']=='focus_changed'
            assert terminal['steps_completed']==0
            assert terminal['interruption']['record']['reason']=='focus_changed'
            assert [e['event'] for e in events].index('input_stopped') < len(events)-1
            if mode=='snapshot_error':assert post['captures']==0 and post['error']
            else:
                assert post['captures']==2 and post['error'] is None
                assert post['equal_sample_pair']==(mode=='stable')
        else:
            assert post is None and backend.snapshots==0
            assert terminal['status']=={'release_failed':'failed','normal':'completed','unrelated_reason':'needs_decision'}[mode]
        rows.append(dict(mode=mode,events=events))
    finally:engine.close()
result=dict(success=True,cases=rows,sources={n:digest((HERE/n).read_bytes()) for n in
    ['probe_post_release_v1.py','executor_v7.py','post_release_observation_v1.py','executor_v6.py']})
(out/'report.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(dict(success=True,cases=len(rows))))
