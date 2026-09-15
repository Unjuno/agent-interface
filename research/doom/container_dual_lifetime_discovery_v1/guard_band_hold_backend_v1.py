"""Development hold: preserve periodic observations, but start none in final 100 ms of authority."""
from __future__ import annotations
import time
from doom_retained_input_backend_v3 import Backend as Previous
from executor_v3 import Cancelled, DecisionRequired

GUARD_NS=100_000_000

class Backend(Previous):
    def execute(self,step,cancel,identifier,index):
        if step.get('op')!='hold':return super().execute(step,cancel,identifier,index)
        if not hasattr(cancel,'expected_focus'):cancel.expected_focus=self.observed_focus
        if cancel.expected_focus in (None,0,1) or getattr(cancel,'focus_invalid',False):raise DecisionRequired()
        def checkpoint():
            if cancel.is_set():raise Cancelled()
            cancel.check()
        checkpoint(); samples=0; guard_skips=0
        try:
            for key in step['keys']:checkpoint();self.raw(key,True)
            self.emit(dict(event='keys_held',id=identifier,step=index,keys=sorted(self.held),
                           input_ack_ns=time.perf_counter_ns(),guard_band_ms=GUARD_NS/1e6))
            step_deadline=time.perf_counter_ns()+int(step['duration_ms']*1_000_000)
            while True:
                checkpoint();now=time.perf_counter_ns()
                if now>=step_deadline:break
                authority_remaining=cancel.deadline-now
                if authority_remaining>GUARD_NS:
                    self.snapshot(identifier,index);samples+=1
                    now=time.perf_counter_ns()
                else:
                    guard_skips+=1
                wait_ns=min(50_000_000,max(0,step_deadline-now),max(0,cancel.deadline-now))
                if wait_ns<=0:
                    checkpoint();continue
                if cancel.wait(wait_ns/1e9):raise Cancelled()
        finally:
            self.emit(dict(event='hold_guard_summary',id=identifier,step=index,
                           in_hold_samples=samples,guard_skips=guard_skips,
                           guard_band_ms=GUARD_NS/1e6,summary_ns=time.perf_counter_ns()))
            for key in list(self.held):self.raw(key,False)
        checkpoint();self.snapshot(identifier,index)
