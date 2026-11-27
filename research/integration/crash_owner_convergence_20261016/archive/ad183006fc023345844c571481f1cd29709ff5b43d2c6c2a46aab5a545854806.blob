"""Child process: actual current-main Executor V3 plus InputOwner; parent may SIGKILL."""
import json,sys,threading,time
from pathlib import Path
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
from executor_v3 import Executor
from input_transition_owner_v4 import InputOwner

class OwnerLease:
    def __init__(self,focus):
        self.deadline=time.perf_counter_ns()+20_000_000_000
        self.expected_focus=focus; self.expected_surface=focus
        self.intent_token='hardkill-xvfb-a01'; self.cancel=threading.Event(); self.focus_invalid=False
    def check(self):
        if self.cancel.is_set(): raise RuntimeError('cancelled')
        if time.perf_counter_ns()>=self.deadline: raise RuntimeError('expired')

class Sink:
    def __init__(self,path): self.path=Path(path); self.lock=threading.Lock()
    def emit(self,row):
        with self.lock:
            with self.path.open('a',encoding='utf8') as f:
                f.write(json.dumps(row,sort_keys=True)+'\n'); f.flush()
            print(json.dumps(row,sort_keys=True),flush=True)

class Backend:
    sequence=2
    def __init__(self,owner,lease,sink): self.owner=owner; self.owner_lease=lease; self.sink=sink; self.down=[]
    def validate(self,steps):
        if steps != [{'op':'hold','keys':['a'],'duration_ms':5000}]: raise ValueError('unexpected hold')
    def execute(self,step,cancel,identifier,index):
        self.owner.call('down',self.owner_lease,'a'); self.down.append('a')
        self.sink.emit({'event':'key_down_active','key':'a','at_ns':time.perf_counter_ns()})
        while not cancel.wait(0.01): pass
    def release_all(self):
        keys=list(self.down)
        transitions=self.owner.call('up_batch',self.owner_lease,keys) if keys else []
        return {'verified':all(x.get('owner_thread_keyup_verified') is True for x in transitions), 'keys_down':[] if transitions else keys,'buttons_down':[],'owner_transitions':transitions}

def main():
    display_name,window_id,eventlog=sys.argv[1],int(sys.argv[2]),sys.argv[3]
    sink=Sink(eventlog); owner=InputOwner(display_name); lease=OwnerLease(window_id)
    executor=Executor(Backend(owner,lease,sink),sink.emit)
    executor.submit('hardkill-hold-a01',[{'op':'hold','keys':['a'],'duration_ms':5000}],2,time.perf_counter_ns()+10_000_000_000)
    while True: time.sleep(1)
if __name__=='__main__': main()
