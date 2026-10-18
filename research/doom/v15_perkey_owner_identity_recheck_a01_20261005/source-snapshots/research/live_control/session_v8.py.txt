"""Explicit bounded pixel-quiet observation, with no input authority renewal."""
import time
from session_v7 import Backend as Previous,suite
from executor_v3 import Cancelled
from quiet_window import QuietWindow

class Backend(Previous):
    def validate(self,steps):
        if not isinstance(steps,list):raise ValueError('steps must be a list')
        rewritten=[];extra=0
        for step in steps:
            if isinstance(step,dict) and step.get('op')=='settle':
                quiet=step.get('quiet_ms');timeout=step.get('timeout_ms')
                if type(quiet) is not int or not 40<=quiet<=250:raise ValueError('quiet_ms must be 40–250')
                if type(timeout) is not int or not quiet<=timeout<=2000:raise ValueError('timeout_ms must be quiet_ms–2000')
                extra+=timeout;rewritten.append(dict(op='observe'))
            else:rewritten.append(step)
        super().validate(rewritten)
        previous=sum(s.get('duration_ms',0) if s.get('op')=='hold' else s.get('timeout_ms',0) if s.get('op')=='wait_title' else 0 for s in rewritten)
        if previous+extra>10000:raise ValueError('combined wait budget exceeds 10 seconds')

    def execute(self,step,cancel,identifier,index):
        if step['op']!='settle':return super().execute(step,cancel,identifier,index)
        if not hasattr(cancel,'expected_focus'):cancel.expected_focus=self.observed_focus
        start=time.perf_counter_ns();deadline=start+step['timeout_ms']*1_000_000
        quiet=QuietWindow(step['quiet_ms']*1_000_000);samples=0;reason='timeout'
        while True:
            if cancel.is_set():raise Cancelled()
            self.snapshot(identifier,index);samples+=1
            now=time.perf_counter_ns()
            if quiet.sample((self.decoder.frame,self.observed_focus),now,self.observed_focus not in (None,0,1)):
                reason='pixel_quiet';break
            if now>=deadline:break
            if cancel.wait(min(.02,max(0,(deadline-now)/1e9))):raise Cancelled()
        self.emit(dict(event='settle_result',id=identifier,step=index,reason=reason,
            samples=samples,sequence=self.sequence,elapsed_ms=(time.perf_counter_ns()-start)/1e6,
            quiet_ms=step['quiet_ms'],timeout_ms=step['timeout_ms'],semantic_completion='unknown'))
