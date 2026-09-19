"""Research-only one-shot guard before an ordinary shared Return program."""
import time
from PIL import ImageGrab
from session_v16 import Backend as Previous,suite
from bound_modal_proposal import Context
from executor_v3 import DecisionRequired


class Backend(Previous):
    def arm_modal(self,identifier,proposal):
        if hasattr(self,'modal_guard'):raise ValueError('one pending guard only')
        self.modal_guard=(identifier,proposal)

    def execute(self,step,cancel,identifier,index):
        guard=getattr(self,'modal_guard',None)
        if guard is None or guard[0]!=identifier:return super().execute(step,cancel,identifier,index)
        del self.modal_guard
        proposal=guard[1]
        if index!=0 or step!=dict(op='key',key='Return'):raise ValueError('guard supports first Return only')
        input_before=self.owner.call('input_state')
        before=self.binding();started=time.perf_counter_ns()
        image=ImageGrab.grab(xdisplay=self.session.name).convert('RGB')
        captured=time.perf_counter_ns();after=self.binding()
        if before!=after or before.get('surface') is None:status='unstable_live_binding'
        else:
            current=Context(self.session.name,self.sequence,proposal.context.capture_ns,
                            after['surface'],after['focus'],tuple(after['geometry']))
            status=proposal.revalidate(current,image,time.perf_counter_ns())
        record=dict(event='modal_guard',id=identifier,status=status,sample_started_ns=started,
                    captured_ns=captured,checked_ns=time.perf_counter_ns(),before=before,after=after,
                    scope='pre-input sample; ordinary lease/owner checks still required')
        # Do not block on diagnostic I/O between this check and normal execution.
        try:
            if status!='requires_new_admission':raise DecisionRequired()
            return super().execute(step,cancel,identifier,index)
        finally:
            record['input_before']=input_before
            record['input_after']=self.owner.call('input_state')
            image.save(self.out/f'{identifier}-guard.png')
            self.emit(record)
