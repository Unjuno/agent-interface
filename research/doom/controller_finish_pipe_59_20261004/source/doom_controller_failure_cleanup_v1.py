"""Best-effort owned cleanup preserving the controller's primary failure."""
import atexit,json

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
                def finish():
                    child.stdin.write('{"op":"finish"}\n');child.stdin.flush()
                attempt('finish_send',finish)
                if not attempt('child_wait',lambda:child.wait(timeout=5)):
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
