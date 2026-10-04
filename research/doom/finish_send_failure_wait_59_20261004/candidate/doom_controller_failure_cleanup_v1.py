"""Best-effort owned cleanup preserving the controller's primary failure."""
import atexit,json,os,select,time

def send_failure_finish(stream, timeout=0.25):
    """Attempt finish on an owned POSIX pipe without an unbounded flush.

    This failure-only path cannot certify protocol delivery or input release.
    Unsupported descriptors fail rather than falling back to a blocking write.
    The caller must have exclusive ownership of the stream during teardown.
    """
    if os.name != 'posix':
        raise NotImplementedError('bounded failure finish requires POSIX pipe')
    fd=stream.fileno()
    blocking=os.get_blocking(fd)
    deadline=time.monotonic()+timeout
    data=b'{"op":"finish"}\n'
    os.set_blocking(fd,False)
    try:
        while data:
            remaining=deadline-time.monotonic()
            if remaining <= 0: raise TimeoutError('failure finish pipe deadline')
            if not select.select([], [fd], [], remaining)[1]:
                raise TimeoutError('failure finish pipe deadline')
            try: written=os.write(fd,data)
            except BlockingIOError: continue
            if written <= 0: raise BrokenPipeError('failure finish made no progress')
            data=data[written:]
    finally:
        os.set_blocking(fd,blocking)

class ControllerFailureCleanup:
    def __init__(self, planner, out):
        self.planner=planner;self.out=out;self.process=None
    def track(self, process):
        self.process=process
    def __enter__(self): return self
    def __exit__(self, kind, error, traceback):
        if error is None: return False
        receipt={'format':'controller-failure-cleanup-v1', 'primary_error_type':kind.__name__,
                 'stages':[], 'input_release_verified':False,
                 'scope':'owned child process only; no physical release or scorer certificate'}
        def attempt(name, operation):
            try:
                result=operation()
                receipt['stages'].append({'stage':name,'status':'returned','result':result})
                return True
            except BaseException as secondary:
                receipt['stages'].append({'stage':name,'status':'failed','error_type':type(secondary).__name__})
                try: error.add_note(name+' cleanup failed: '+type(secondary).__name__)
                except BaseException: pass
                return False
        child=self.process
        if child is not None:
            polled=attempt('child_poll_before',child.poll)
            if not polled or receipt['stages'][-1]['result'] is None:
                finish_sent=attempt('finish_send',lambda:send_failure_finish(child.stdin))
                if finish_sent:
                    if not attempt('child_wait',lambda:child.wait(timeout=5)):
                        attempt('child_terminate',child.terminate)
                        if not attempt('terminated_wait',lambda:child.wait(timeout=1)):
                            attempt('child_kill',child.kill)
                            attempt('killed_wait',lambda:child.wait(timeout=1))
                else:
                    receipt['stages'].append({'stage':'child_wait','status':'skipped',
                                              'reason':'finish_send_failed'})
                    poll_ok=attempt('child_poll_after_finish_failure',child.poll)
                    if not poll_ok or receipt['stages'][-1]['result'] is None:
                        attempt('child_terminate',child.terminate)
                        if not attempt('terminated_wait',lambda:child.wait(timeout=1)):
                            attempt('child_kill',child.kill)
                            attempt('killed_wait',lambda:child.wait(timeout=1))
            if attempt('child_poll_after',child.poll):
                receipt['child_exit_code']=receipt['stages'][-1]['result']
        if attempt('planner_close',lambda:self.planner.close(timeout=1)):
            attempt('atexit_unregister',lambda:atexit.unregister(self.planner.close))
        attempt('failure_receipt_write',lambda:(self.out/'controller-failure.json').write_text(json.dumps(receipt,indent=2)+'\n'))
        return False
