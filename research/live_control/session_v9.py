"""Candidate shared backend: snapshot-bound, bounded pointer programs."""
import time
from PIL import ImageGrab
from Xlib import X,error
from session_v8 import Backend as Previous,suite
from session_v4 import Encoder,Decoder,Frame,ImageArtifactSink
from input_owner_v5 import InputOwner
from executor_v3 import Cancelled,DecisionRequired

POINTER={'pointer_move','pointer_click','pointer_drag','pointer_scroll'}

class Backend(Previous):
    def __init__(self,session,out,emit):
        self.session,self.out,self.emit=session,out,emit
        self.encoder,self.decoder=Encoder('live-control','O2',64),Decoder('live-control')
        self.images=ImageArtifactSink(out,compress_level=1,reuse=True)
        self.held=set();self.touched=set();self.sequence=0;self.last_context={}
        self.observed_focus=None;self.observed_pointer=None
        self.owner=InputOwner(session.name)

    def binding(self):
        focus=self.focus_id();root=self.session.d.screen().root
        prop=root.get_full_property(self.session.d.intern_atom('_NET_ACTIVE_WINDOW'),X.AnyPropertyType)
        surface=int(prop.value[0]) if prop is not None and len(prop.value) else None
        if focus in (None,0,1) or surface in (None,0,1):return {'focus':focus,'surface':None,'geometry':None}
        node=self.session.d.create_resource_object('window',focus)
        try:
            for _ in range(32):
                if node.id==surface:
                    geometry=self.owner.call('surface_context',key=surface)
                    return {'focus':focus,'surface':surface,'geometry':geometry}
                if node.id==root.id:break
                node=node.query_tree().parent
        except (error.BadWindow,error.BadDrawable,DecisionRequired):pass
        return {'focus':focus,'surface':None,'geometry':None}

    def snapshot(self,identifier,index):
        before=self.binding();start=time.perf_counter_ns()
        im=ImageGrab.grab(xdisplay=self.session.name).convert('RGB');capture=time.perf_counter_ns()
        source=Frame(im.width,im.height,im.mode,im.tobytes())
        context=self.session.context();context_ns=time.perf_counter_ns();after=self.binding()
        self.observed_focus=after['focus'] if before['focus']==after['focus'] else None
        self.observed_pointer=dict(after) if before==after and after['surface'] is not None else None
        packet=self.encoder.encode(source,action_id=f'{identifier}:{index}',observed_ns=capture,context=context)
        frame=self.decoder.accept(packet)
        if frame!=source:raise AssertionError('wire reconstruction failed')
        self.sequence+=1;(self.out/f'{self.sequence:03d}.ait').write_bytes(packet)
        artifact=self.images.publish(frame);self.last_context=dict(context)
        self.emit(dict(event='observation',id=identifier,step=index,sequence=self.sequence,
            capture_ns=capture,context_ns=context_ns,context=context,**artifact,
            input_focus_before=before['focus'],input_focus_after=after['focus'],
            focus_samples_match=before['focus']==after['focus'],pointer_binding=self.observed_pointer,
            pointer_context_before=before,pointer_context_after=after,
            capture_ms=(capture-start)/1e6,wire_bytes=len(packet),exact=True,semantic_completion='unknown'))

    def validate(self,steps):
        if not isinstance(steps,list):raise ValueError('steps must be list')
        rewritten=[];pointer_ms=0
        def point(p):
            frame=self.decoder.frame
            if not isinstance(p,dict) or set(p)!={'x','y'} or any(type(p[k]) is not int for k in ('x','y')):
                raise ValueError('integer x/y point required')
            if frame is None or not(0<=p['x']<frame.width and 0<=p['y']<frame.height):raise ValueError('point outside observed root')
        for s in steps:
            if not isinstance(s,dict) or s.get('op') not in POINTER:rewritten.append(s);continue
            op=s['op'];required={'op','points','duration_ms'} if op=='pointer_drag' else {'op','x','y'}
            allowed=required|({'button'} if op in ('pointer_drag','pointer_click') else set())
            if op=='pointer_click':allowed|={'duration_ms'}
            if op=='pointer_scroll':required|={'ticks'};allowed|={'ticks'}
            if not required<=set(s) or not set(s)<=allowed:raise ValueError('invalid pointer fields')
            if op=='pointer_drag':
                if not isinstance(s['points'],list) or not 2<=len(s['points'])<=32:raise ValueError('2..32 drag points required')
                for p in s['points']:point(p)
            else:point({'x':s['x'],'y':s['y']})
            if op in ('pointer_drag','pointer_click'):
                if type(s.get('button',1)) is not int or s.get('button',1) not in (1,2,3):raise ValueError('button 1..3 required')
                duration=s.get('duration_ms',40)
                limit=5000 if op=='pointer_drag' else 250
                if type(duration) is not int or not 1<=duration<=limit:raise ValueError('invalid pointer duration')
                pointer_ms+=duration
            if op=='pointer_scroll' and (type(s['ticks']) is not int or s['ticks']==0 or abs(s['ticks'])>10):raise ValueError('nonzero -10..10 ticks required')
            rewritten.append({'op':'observe'})
        super().validate(rewritten)
        other=sum(s.get('duration_ms',0) if s.get('op')=='hold' else s.get('timeout_ms',0) if s.get('op') in ('settle','wait_title') else 0 for s in rewritten)
        if pointer_ms+other>10000:raise ValueError('combined hold/wait budget exceeds 10 seconds')

    def execute(self,step,cancel,identifier,index):
        # Bind all authority once, including when a recovery observation is first.
        if not hasattr(cancel,'expected_focus'):
            cancel.expected_focus=self.observed_focus
            b=self.observed_pointer
            cancel.expected_surface=b['surface'] if b else None
            cancel.expected_geometry=list(b['geometry']) if b else None
        if step['op'] not in POINTER:return super().execute(step,cancel,identifier,index)
        if cancel.expected_surface is None:raise DecisionRequired()
        def call(op,payload):
            record=self.owner.call(op,cancel,payload)
            if record is not None:self.emit(dict(record,id=identifier,step=index))
        def wait(ms):
            if cancel.wait(ms/1000):raise Cancelled()
        op=step['op']
        points=step['points'] if op=='pointer_drag' else [{'x':step['x'],'y':step['y']}]
        call('move',points[0])
        if op in ('pointer_click','pointer_drag'):
            button=step.get('button',1)
            try:
                call('button_down',button)
                if op=='pointer_click':wait(step.get('duration_ms',40))
                else:
                    for p in points[1:]:wait(step['duration_ms']/(len(points)-1));call('move',p)
            finally:call('button_up',button)
        elif op=='pointer_scroll':call('wheel',step['ticks'])
        if cancel.is_set():raise Cancelled()
        self.snapshot(identifier,index)
