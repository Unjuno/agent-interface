import importlib.util, json, sys, threading, types
from pathlib import Path

class Cancelled(Exception): pass
class DecisionRequired(Exception): pass
class Expired(Exception): pass
class Previous:
    def __init__(self, backend, emit):
        self.backend, self.emit = backend, emit
        self.lock = threading.RLock()
        self.active = None
        self.release_publication_attempted_ids = set()
        self.published_release_ids = set()
        self.release_publication_errors = {}
        self.release_watchers = []
        self.terminal_publication_errors = {}

v3 = types.ModuleType('executor_v3'); v3.Cancelled=Cancelled; v3.DecisionRequired=DecisionRequired
v12 = types.ModuleType('executor_v12'); v12.Executor=Previous
lease_module = types.ModuleType('lease'); lease_module.Expired=Expired
sys.modules.update({'executor_v3':v3,'executor_v12':v12,'lease':lease_module})
spec=importlib.util.spec_from_file_location('exact_executor_v13',Path(sys.argv[1]))
module=importlib.util.module_from_spec(spec); spec.loader.exec_module(module)

CUSTODY={'schema':'release-batch-delivery-v1','identifier':'cleanup','step':0,'size':1,
         'positions':[{'position':0,'step':0,'key':'a','state':'unknown'}]}
class Backend:
    def execute(self,step,lease,identifier,index): return None
    def release_all(self):
        error=KeyboardInterrupt('cleanup sink interruption')
        error.release_batch_publication=dict(CUSTODY)
        raise error
class Lease:
    def __init__(self): self.cancel=threading.Event()
    def is_set(self): return False
    def interruption_snapshot(self): return None
    def wait_interruption(self,timeout): return None

events=[]; executor=module.Executor(Backend(),events.append); lease=Lease(); executor.active=('cleanup',lease)
try:
    executor._run_with_watcher_cleanup('cleanup',[{'op':'release'}],lease)
    escaped=None
except BaseException as exc:
    escaped=type(exc).__name__+': '+str(exc)
terminals=[event for event in events if event.get('event')=='terminal']
print(json.dumps({'escaped':escaped,'terminal_count':len(terminals),'terminal':terminals[-1] if terminals else None},sort_keys=True))


