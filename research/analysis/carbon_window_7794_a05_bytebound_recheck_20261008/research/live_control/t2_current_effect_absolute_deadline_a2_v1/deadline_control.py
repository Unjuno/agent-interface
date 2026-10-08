#!/usr/bin/env python3
import time
from experiment import wait_effect, EFFECT_TIMEOUT_MS
class LateQueue:
    def __init__(self, receipt, sleep_s): self.receipt=receipt; self.sleep_s=sleep_s
    def get(self, timeout):
        time.sleep(self.sleep_s)
        return self.receipt
session='s-control'; request='r-control'
r={'role':'CURRENT_EFFECT','session_id':session,'request_id':request}
deadline=time.perf_counter_ns()+int(2e6)
accepted,wake=wait_effect(LateQueue(r,0.004),deadline,session,request)
assert accepted is None, (accepted,wake,deadline)
assert wake>=deadline, (wake,deadline)
print('PASS_LATE_WAKE_REJECTED', (wake-deadline)/1e6)
