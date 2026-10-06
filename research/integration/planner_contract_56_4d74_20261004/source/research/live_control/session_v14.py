"""Candidate guided pointer: one explicit yield, reply and correction at a time."""
from session_v13 import Backend as Previous,suite,Encoder,Decoder,ImageArtifactSink
from input_owner_v8 import InputOwner
from pointer_reply import PointerReply
from executor_v3 import Cancelled,DecisionRequired

class Backend(Previous):
    def __init__(self,session,out,emit):
        self.session,self.out,self.emit=session,out,emit
        self.encoder,self.decoder=Encoder('live-control','O2',64),Decoder('live-control')
        self.images=ImageArtifactSink(out,compress_level=1,reuse=True)
        self.held=set();self.touched=set();self.sequence=0;self.last_context={}
        self.observed_focus=None;self.observed_pointer=None;self.owner=InputOwner(session.name)
        self.replies=PointerReply()
    def validate(self,steps):
        if not isinstance(steps,list):return super().validate(steps)
        rewritten=[];extra=0
        for s in steps:
            if not isinstance(s,dict) or s.get('op')!='pointer_guided':rewritten.append(s);continue
            if set(s)!={'op','points','duration_ms','reply_timeout_ms','max_updates','feedback_delay_ms'}:raise ValueError('invalid guided fields')
            for key,lo,hi in [('reply_timeout_ms',100,5000),('max_updates',1,4),('feedback_delay_ms',0,250)]:
                if type(s[key]) is not int or not lo<=s[key]<=hi:raise ValueError('invalid '+key)
            extra+=s['max_updates']*(s['reply_timeout_ms']+s['feedback_delay_ms'])
            rewritten.append({'op':'pointer_drag','points':s['points'],'duration_ms':s['duration_ms']})
        super().validate(rewritten)
        budget=sum(s.get('duration_ms',40 if s['op']=='pointer_click' else 0) if s['op'] in ('hold','pointer_drag','pointer_click') else s.get('timeout_ms',0) if s['op'] in ('settle','wait_title') else 0 for s in rewritten)
        budget+=sum(s.get('feedback_delay_ms',0)*len(s.get('observe_at',[])) for s in rewritten)
        if budget+extra>10000:raise ValueError('combined declared budget exceeds 10 seconds')
    def reply_pointer(self,ticket,sequence,command):
        if not isinstance(command,dict):raise ValueError('reply command required')
        if command.get('op')=='finish':
            if set(command)!={'op'}:raise ValueError('invalid finish reply')
        elif command.get('op')=='move':
            if set(command)!={'op','x','y'} or any(type(command[k]) is not int for k in ('x','y')):raise ValueError('integer reply point required')
            f=self.decoder.frame
            if f is None or not 0<=command['x']<f.width or not 0<=command['y']<f.height:raise ValueError('reply point outside observation')
        else:raise ValueError('reply must move or finish')
        return self.replies.submit(ticket,sequence,command)
    def execute(self,step,cancel,identifier,index):
        if step['op']!='pointer_guided':return super().execute(step,cancel,identifier,index)
        if not hasattr(cancel,'expected_focus'):
            cancel.expected_focus=self.observed_focus;b=self.observed_pointer
            cancel.expected_surface=b['surface'] if b else None;cancel.expected_geometry=list(b['geometry']) if b else None
        if cancel.expected_surface is None:raise DecisionRequired()
        def call(op,payload):
            r=self.owner.call(op,cancel,payload)
            if r is not None:self.emit(dict(r,id=identifier,step=index))
        points=step['points'];call('move',points[0])
        try:
            call('button_down',1)
            for p in points[1:]:
                if cancel.wait(step['duration_ms']/1000/(len(points)-1)):raise Cancelled()
                call('move',p)
            for update in range(step['max_updates']):
                if cancel.wait(step['feedback_delay_ms']/1000):raise Cancelled()
                observations=[];emit=self.emit
                def collect(r):
                    if r.get('event')=='observation':observations.append(r)
                    emit(r)
                self.emit=collect
                try:self.snapshot(identifier,index)
                finally:self.emit=emit
                observed=observations[-1];state=observed['input_state_after']
                if state['owned_buttons']!=[1] or state['active_lease_deadline_ns']!=cancel.deadline:raise DecisionRequired()
                offer=self.replies.offer(self.sequence,observed['capture_ns'],step['reply_timeout_ms'],cancel)
                self.emit(dict(event='pointer_yield',id=identifier,step=index,update=update,**offer))
                command=self.replies.wait(cancel)
                if command['op']=='finish':break
                call('continue_move',dict(owner_id=state['owner_id'],expected_revision=state['revision'],x=command['x'],y=command['y']))
        finally:
            self.replies.clear();call('button_up',1)
        if cancel.is_set():raise Cancelled()
        self.snapshot(identifier,index)
