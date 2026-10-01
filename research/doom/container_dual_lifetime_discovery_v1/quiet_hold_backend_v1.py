"""Development-only hold variant: no observation while a keyboard hold is active.

It preserves the existing InputOwner lease, focus binding, key admission/release,
and final post-step observation on normal completion. The sole changed mechanism
is removal of capture/artifact work from the active hold interval.
"""
from __future__ import annotations
import time
from doom_retained_input_backend_v3 import Backend as Previous
from executor_v3 import Cancelled, DecisionRequired

class Backend(Previous):
    def execute(self, step, cancel, identifier, index):
        if step.get('op') != 'hold':
            return super().execute(step, cancel, identifier, index)
        if not hasattr(cancel, 'expected_focus'):
            cancel.expected_focus = self.observed_focus
        if cancel.expected_focus in (None,0,1) or getattr(cancel,'focus_invalid',False):
            raise DecisionRequired()
        def checkpoint():
            if cancel.is_set():
                raise Cancelled()
            cancel.check()
        checkpoint()
        try:
            for key in step['keys']:
                checkpoint(); self.raw(key, True)
            self.emit(dict(event='keys_held', id=identifier, step=index,
                           keys=sorted(self.held), input_ack_ns=time.perf_counter_ns(),
                           in_hold_observation=False))
            deadline=time.perf_counter_ns()+int(step['duration_ms']*1_000_000)
            while True:
                remaining=deadline-time.perf_counter_ns()
                if remaining<=0:break
                if cancel.wait(min(.05,remaining/1e9)):
                    raise Cancelled()
        finally:
            for key in list(self.held):
                self.raw(key, False)
        checkpoint()
        self.snapshot(identifier,index)
