"""Controlled live-thread stalls; compares frozen v7 and cooperative v8."""
import json
import threading
import time
from pathlib import Path
from types import SimpleNamespace
from executor_v7 import Executor as V7
from executor_v8 import Executor as V8
from executor_v3 import DecisionRequired
from report_pages_v2 import digest

HERE=Path(__file__).resolve().parent
out=HERE/'results/post-release-stop-01';out.mkdir(exist_ok=False)
names=['probe_post_release_stop_v1.py','executor_v7.py','executor_v8.py',
       'post_release_observation_v1.py','post_release_observation_v2.py','lease_cause_v2.py']
plan=dict(sources={n:digest((HERE/n).read_bytes()) for n in names},
    cases=[['capture','cancel'],['output','cancel'],['before_collect','cancel'],
           ['capture','close'],['output','close']],
    scope='Synthetic gates in real worker threads. Probe releases every gate; not X11, actual pipe saturation, or a hard capture timeout.')
(out/'plan.json').write_text(json.dumps(plan,indent=2)+'\n')
rows=[]
for version,Executor in [('v7',V7),('v8',V8)]:
    for boundary,action in plan['cases']:
        entered,resume,done,closing=threading.Event(),threading.Event(),threading.Event(),threading.Event()
        events=[];closer=None
        def gate():
            entered.set()
            assert resume.wait(3),'probe gate never released'
        def emit(e):
            e['probe_ns']=time.perf_counter_ns();events.append(e)
            if boundary=='before_collect' and e['event']=='input_stopped':gate()
            if boundary=='output' and e['event']=='observation' and e['sequence']==2:gate()
            if e['event']=='terminal':done.set()
        class Backend:
            sequence=1
            snapshots=0
            observed_pointer={'focus':99,'surface':99}
            decoder=SimpleNamespace(frame=b'foreign-window')
            def validate(self,steps):pass
            def execute(self,step,lease,identifier,index):
                assert index==0,'input tail resumed'
                lease.record_interruption(dict(event='owner_release',reason='focus_changed',verified=True))
                raise DecisionRequired()
            def release_all(self):
                self.released=True
                return dict(verified=True,keys_down=[],buttons_down=[])
            def snapshot(self,identifier,index):
                assert self.released
                self.snapshots+=1
                if boundary=='capture' and self.snapshots==1:gate()
                self.sequence+=1
                emit(dict(event='observation',id=identifier,sequence=self.sequence))
        backend=Backend();engine=Executor(backend,emit)
        try:
            engine.submit('fault',[dict(op='one'),dict(op='tail')],1,time.perf_counter_ns()+5_000_000_000)
            assert entered.wait(2)
            if action=='cancel':
                assert engine.cancel('fault')
            else:
                def close():
                    closing.set();engine.close()
                closer=threading.Thread(target=close);closer.start();assert closing.wait(1)
            assert backend.lease.cancel.wait(1)
            no_terminal_while_stalled=not done.wait(.1)
            assert no_terminal_while_stalled
            if closer:assert closer.is_alive()
            resumed_ns=time.perf_counter_ns();resume.set();assert done.wait(2)
            if closer:closer.join(2);assert not closer.is_alive()
            terminal=next(e for e in events if e['event']=='terminal')
            assert terminal['status']=='needs_decision' and terminal['decision_reason']=='focus_changed'
            assert terminal['steps_completed']==0 and terminal['release']['verified']
            expected=2 if version=='v7' else 0 if boundary=='before_collect' else 1
            assert backend.snapshots==expected
            if version=='v8':assert terminal['post_release_observation']['stopped']
            rows.append(dict(version=version,boundary=boundary,action=action,
                no_terminal_while_stalled=no_terminal_while_stalled,captures=backend.snapshots,
                resume_to_terminal_ms=(terminal['probe_ns']-resumed_ns)/1e6,events=events))
        finally:
            resume.set();engine.close()
            if closer:closer.join(2)
result=dict(success=True,cases=rows,
    limitation='Both candidates still wait for the current synchronous capture/output to return. v8 stops subsequent optional captures; it does not preempt a blocked call or reclassify the original cause.')
(out/'report.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(dict(success=True,cases=[{k:v for k,v in r.items() if k!='events'} for r in rows])))
