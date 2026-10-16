import threading, time
from executor_v12 import Executor
state = {}
class Backend:
    sequence=1
    lease=None
    def validate(self, steps): pass
    def execute(self, *args): state['execute_called']=True
    def release_all(self): return {'verified': True}
executor=None
def emit(event):
    if event.get('event') == 'accepted':
        state['worker']=executor.active[2]
        executor.close()
executor=Executor(Backend(), emit)
try:
    executor.submit('reentrant-close-parent', [{'op':'noop'}], 1,
                    time.perf_counter_ns()+10_000_000_000)
except RuntimeError as exc:
    state['submit_error']=str(exc)
else:
    raise AssertionError('parent unexpectedly returned from nested close')
worker=state['worker']
state.update(closed=executor.closed, worker_ident=worker.ident,
            worker_alive=worker.is_alive(), active_retained=executor.active is not None,
            execute_called=state.get('execute_called',False))
print(state)
assert state['closed'] and state['worker_ident'] is None
assert state['worker_alive'] is False and state['active_retained']
assert state['execute_called'] is False
assert state['submit_error']=='cannot join thread before it is started'
