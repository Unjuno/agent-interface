import threading, time
from executor_v12 import Executor

entered_release = threading.Event()
finish_release = threading.Event()
execute_called = threading.Event()
state = {}

class Backend:
    sequence = 1
    lease = None
    def validate(self, steps):
        if steps != [{'op': 'noop'}]: raise ValueError(steps)
    def execute(self, step, lease, identifier, index):
        execute_called.set()
    def release_all(self):
        entered_release.set()
        if not finish_release.wait(3): raise TimeoutError('release gate')
        return {'verified': True}

backend = Backend()
executor = None

def emit(event):
    if event.get('event') == 'accepted' and not state.get('nested_close'):
        state['nested_close'] = True
        state['worker_ident_when_close_returns'] = executor.active[2].ident
        executor.close()
        state['close_returned'] = True
        state['closed_after_nested_close'] = executor.closed
        state['worker_ident_after_close'] = executor.active[2].ident
    state.setdefault('events', []).append(event.get('event'))

executor = Executor(backend, emit)
executor.submit('reentrant-close', [{'op':'noop'}], 1, time.perf_counter_ns() + 10_000_000_000)
if not entered_release.wait(1): raise AssertionError('worker did not enter release_all')
state['worker_alive_after_close_return'] = executor.active[2].is_alive()
state['execute_called'] = execute_called.is_set()
print(state)
assert state['close_returned'] and state['closed_after_nested_close']
assert state['worker_ident_when_close_returns'] is None
assert state['worker_alive_after_close_return'] is True
assert state['execute_called'] is False
finish_release.set()
executor.active[2].join(2)
assert not executor.active[2].is_alive()
