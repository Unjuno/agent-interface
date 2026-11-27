"""Inert bounded probe of supervisor behavior when helper send blocks."""
import hashlib
import json
import threading
import time
from pathlib import Path
from runtime.guarded_win32_v1 import process_cancellation as module

class Process:
    def is_alive(self): return True

class Connection:
    def __init__(self): self.enter=threading.Event();self.unblock=threading.Event()
    def send(self, request):
        self.enter.set()
        if not self.unblock.wait(2): raise TimeoutError("fake send safety bound")
    def poll(self, timeout): return False

def main():
    process=Process();conn=Connection()
    supervisor=object.__new__(module.OperationCancellationSupervisor)
    supervisor._helpers={"recovery":{"process":process,"connection":conn,"lock":threading.Lock(),"available":True,"identity":"same"}}
    supervisor._clock_ns=time.monotonic_ns
    supervisor._terminate_grace_s=0;supervisor._kill_grace_s=0;supervisor._poll_interval_s=0.01
    supervisor._process_identity_reader=lambda _:"same"
    supervisor._retire_process=lambda *_:True
    errors=[]
    start=time.monotonic_ns();deadline=start+100_000_000
    def worker():
        try: supervisor._exchange_helper("recovery",{"request_id":"fake"},deadline)
        except BaseException as error: errors.append(type(error).__name__)
    thread=threading.Thread(target=worker);thread.start()
    try:
        if not conn.enter.wait(1): raise RuntimeError("fake send not entered")
        thread.join(0.2)
        observed=time.monotonic_ns()
        blocked=thread.is_alive()
    finally:
        conn.unblock.set();thread.join(2)
    if thread.is_alive(): raise RuntimeError("fake probe thread did not stop")
    result={"schema":"win32-fake-blocked-helper-send-v1",
      "source_sha256":hashlib.sha256(Path(module.__file__).read_bytes()).hexdigest(),
      "cutoff_ns":deadline-start,"observation_ns":observed-start,
      "blocked_past_cutoff":blocked,"after_unblock_error":errors,
      "scope":"Fake process and fake connection only; no GUI, native input, or live allocation."}
    print(json.dumps(result,sort_keys=True))
    return 0 if blocked and errors==["TimeoutError"] else 1

if __name__ == "__main__": raise SystemExit(main())
