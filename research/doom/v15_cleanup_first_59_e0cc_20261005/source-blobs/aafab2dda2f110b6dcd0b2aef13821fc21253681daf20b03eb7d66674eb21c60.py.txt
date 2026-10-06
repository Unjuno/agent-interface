"""Focus-bound input research revision; matching samples do not prove atomicity."""
import time
from PIL import ImageGrab
from session_v4 import Encoder,Decoder,Frame,ImageArtifactSink,suite
from session_v5 import Backend as Previous
from input_owner_v2 import InputOwner
from executor_v3 import DecisionRequired

class Backend(Previous):
    def __init__(self,session,out,emit):
        self.session,self.out,self.emit=session,out,emit
        self.encoder,self.decoder=Encoder('live-control','O2',64),Decoder('live-control')
        self.images=ImageArtifactSink(out,compress_level=1,reuse=True)
        self.held=set();self.touched=set();self.sequence=0;self.last_context={}
        self.observed_focus=None
        self.owner=InputOwner(session.name)

    def focus_id(self):
        value=self.session.d.get_input_focus().focus
        return value.id if hasattr(value,'id') else value

    def execute(self,step,cancel,identifier,index):
        if not hasattr(cancel,'expected_focus'):
            if self.observed_focus in (None,0,1):
                raise DecisionRequired()
            cancel.expected_focus=self.observed_focus
        return super().execute(step,cancel,identifier,index)

    def snapshot(self,identifier,index):
        before=self.focus_id()
        start=time.perf_counter_ns()
        im=ImageGrab.grab(xdisplay=self.session.name).convert('RGB')
        capture=time.perf_counter_ns()
        source=Frame(im.width,im.height,im.mode,im.tobytes())
        context=self.session.context(); context_ns=time.perf_counter_ns()
        after=self.focus_id()
        self.observed_focus=after if before==after else None
        packet=self.encoder.encode(source,action_id=f'{identifier}:{index}',observed_ns=capture,context=context)
        frame=self.decoder.accept(packet)
        if frame!=source:raise AssertionError('wire reconstruction failed')
        self.sequence+=1
        (self.out/f'{self.sequence:03d}.ait').write_bytes(packet)
        artifact=self.images.publish(frame)
        self.last_context=dict(context)
        self.emit(dict(event='observation',id=identifier,step=index,sequence=self.sequence,
                       capture_ns=capture,context_ns=context_ns,context=context,**artifact,
                       input_focus_before=before,input_focus_after=after,focus_samples_match=before==after,
                       capture_ms=(capture-start)/1e6,wire_bytes=len(packet),exact=True,
                       semantic_completion='unknown'))

