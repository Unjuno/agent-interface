"""Bounded retry for idempotent shared-file operations, never model calls."""
import time

def retry_permission(operation, *, stage, timeout=2.0, interval=0.02,
                     clock=time.monotonic, sleep=time.sleep, observe=None):
    if not callable(operation) or type(stage) is not str or not stage:
        raise ValueError('operation and stage required')
    if timeout <= 0 or interval <= 0:
        raise ValueError('positive timeout and interval required')
    deadline = clock() + timeout
    attempt = 0
    while True:
        attempt += 1
        try:
            return operation()
        except PermissionError:
            remaining = deadline - clock()
            if observe is not None:
                observe({'stage': stage, 'attempt': attempt,
                         'status': 'deadline' if remaining <= 0 else 'retry'})
            if remaining <= 0:
                raise
            sleep(min(interval, remaining))
