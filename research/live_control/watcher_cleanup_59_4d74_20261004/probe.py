import threading,time,json
from executor_v13 import Executor
class Backend:
 sequence=1
 def __init__(self): self.started=threading.Event();self.finish=threading.Event();self.releases=0
 def validate(self,steps):pass
 def execute(self,*args):self.started.set();assert self.finish.wait(2)
 def release_all(self):self.releases+=1;return {"verified":True,"keys_down":[],"buttons_down":[]}
b=Backend();events=[];errors=[]
threading.excepthook=lambda args:errors.append(type(args.exc_value).__name__)
def emit(e):
 events.append(e)
 if e['event']=='terminal':raise OSError('terminal acknowledgement lost')
x=Executor(b,emit);x.submit('normal',[{'op':'pointer_drag'}],1,time.perf_counter_ns()+5_000_000_000)
assert b.started.wait(1)
worker=x.active[2];lease=x.active[1];b.finish.set();worker.join(1)
assert not worker.is_alive()
closed=threading.Event()
def close():x.close();closed.set()
t=threading.Thread(target=close);t.start();returned=closed.wait(.25)
result={'close_returned_before_supervisor_cleanup':returned,'interruption':lease.interruption_snapshot(),'terminal_attempts':sum(e['event']=='terminal' for e in events),'terminal_error':x.terminal_publication_errors,'worker_errors':errors,'release_count':b.releases}
# A supervisor ends only this fake construction after observation; never relaunch.
for stop in x.release_watch_stops.values():stop.set()
t.join(1)
result['all_threads_retired']=not t.is_alive() and all(not w.is_alive() for w in x.release_watchers)
print(json.dumps(result,sort_keys=True))
assert result['all_threads_retired']
assert result['terminal_attempts']==1 and result['interruption'] is None
assert result['terminal_error']['normal']['status']=='delivery_unknown'
assert returned,'normal terminal sink failure hangs close'
