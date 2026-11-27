"""Candidate observations bracketed by independent owner's historical input state."""
from session_v12 import Backend as Previous,suite,Encoder,Decoder,ImageArtifactSink
from input_owner_v7 import InputOwner

class Backend(Previous):
    def __init__(self,session,out,emit):
        self.session,self.out,self.emit=session,out,emit
        self.encoder,self.decoder=Encoder('live-control','O2',64),Decoder('live-control')
        self.images=ImageArtifactSink(out,compress_level=1,reuse=True)
        self.held=set();self.touched=set();self.sequence=0;self.last_context={}
        self.observed_focus=None;self.observed_pointer=None
        self.owner=InputOwner(session.name)

    def snapshot(self,identifier,index):
        before=self.owner.call('input_state');emit=self.emit
        def bracketed(record):
            if record.get('event')=='observation':
                after=self.owner.call('input_state')
                record.update(input_state_before=before,input_state_after=after,
                    owner_revision_unchanged=before['revision']==after['revision'],
                    input_state_scope='historical samples around capture/publication; not atomic or current at delivery')
            emit(record)
        self.emit=bracketed
        try:return super().snapshot(identifier,index)
        finally:self.emit=emit
