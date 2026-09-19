"""Unpromoted drag-feedback backend with pointer-only client focus equivalence."""
from session_v11 import Backend as Previous,suite
from session_v9 import Encoder,Decoder,ImageArtifactSink
from input_owner_v6 import InputOwner

class Backend(Previous):
    def __init__(self,session,out,emit):
        self.session,self.out,self.emit=session,out,emit
        self.encoder,self.decoder=Encoder('live-control','O2',64),Decoder('live-control')
        self.images=ImageArtifactSink(out,compress_level=1,reuse=True)
        self.held=set();self.touched=set();self.sequence=0;self.last_context={}
        self.observed_focus=None;self.observed_pointer=None
        self.owner=InputOwner(session.name)
