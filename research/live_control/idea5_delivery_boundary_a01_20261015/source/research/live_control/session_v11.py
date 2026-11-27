"""Candidate bounded drag checkpoints; independent owner retains the same lease."""
from session_v9 import Backend as Previous,suite
from executor_v3 import Cancelled,DecisionRequired

class Backend(Previous):
    def validate(self,steps):
        rewritten=[];feedback_ms=0
        if not isinstance(steps,list):return super().validate(steps)
        for step in steps:
            if not isinstance(step,dict) or step.get('op')!='pointer_drag' or 'observe_at' not in step:
                rewritten.append(step);continue
            clean=dict(step);indices=clean.pop('observe_at');points=clean.get('points')
            delay=clean.pop('feedback_delay_ms',0)
            if type(delay) is not int or not 0<=delay<=250:raise ValueError('feedback_delay_ms must be 0..250')
            if not isinstance(points,list) or not isinstance(indices,list) or not 1<=len(indices)<=4:
                raise ValueError('drag observe_at requires 1..4 point indices')
            if any(type(i) is not int or not 0<=i<len(points)-1 for i in indices) or indices!=sorted(set(indices)):
                raise ValueError('observe_at must be unique increasing non-final point indices')
            feedback_ms+=delay*len(indices)
            rewritten.append(clean)
        super().validate(rewritten)
        declared=sum(s.get('duration_ms',40 if s['op']=='pointer_click' else 0) if s['op'] in ('hold','pointer_click','pointer_drag') else s.get('timeout_ms',0) if s['op'] in ('wait_title','settle') else 0 for s in rewritten)
        if declared+feedback_ms>10000:raise ValueError('combined hold/wait/feedback budget exceeds 10 seconds')

    def execute(self,step,cancel,identifier,index):
        if step['op']!='pointer_drag' or 'observe_at' not in step:
            return super().execute(step,cancel,identifier,index)
        if not hasattr(cancel,'expected_focus'):
            cancel.expected_focus=self.observed_focus;b=self.observed_pointer
            cancel.expected_surface=b['surface'] if b else None
            cancel.expected_geometry=list(b['geometry']) if b else None
        if cancel.expected_surface is None:raise DecisionRequired()
        def call(op,payload):
            record=self.owner.call(op,cancel,payload)
            if record is not None:self.emit(dict(record,id=identifier,step=index))
        def checkpoint(point):
            if point not in step['observe_at']:return
            if cancel.is_set():raise Cancelled()
            self.emit(dict(event='drag_checkpoint',id=identifier,step=index,point_index=point,
                valid_until_ns=cancel.deadline,meaning='capture requested before planned release; owner may release independently'))
            if cancel.wait(step.get('feedback_delay_ms',0)/1000):raise Cancelled()
            self.snapshot(identifier,index)
            self.emit(dict(event='drag_feedback',id=identifier,step=index,point_index=point,
                sequence=self.sequence,valid_until_ns=cancel.deadline,semantic_completion='unknown'))
            # Captures never renew authority, and no tail movement after cancellation/expiry.
            if cancel.is_set():raise Cancelled()
        points=step['points'];button=step.get('button',1)
        call('move',points[0])
        try:
            call('button_down',button);checkpoint(0)
            for n,p in enumerate(points[1:],1):
                if cancel.wait(step['duration_ms']/1000/(len(points)-1)):raise Cancelled()
                call('move',p);checkpoint(n)
        finally:call('button_up',button)
        if cancel.is_set():raise Cancelled()
        self.snapshot(identifier,index)
