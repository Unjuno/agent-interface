from __future__ import annotations
import time
from PIL import ImageGrab
from doom_retained_input_backend_v3 import Backend as Previous
from doom_typed_observation_v1 import extract_typed_observation
from session_v4 import Frame
from executor_v3 import Cancelled, DecisionRequired

class Backend(Previous):
    """Research-only two-phase final hold snapshot; no shared runtime promotion."""
    def _capture_typed(self, identifier, index):
        before=self.binding(); started_ns=time.perf_counter_ns()
        image=ImageGrab.grab(xdisplay=self.session.name).convert('RGB')
        capture_ns=time.perf_counter_ns()
        source=Frame(image.width,image.height,image.mode,image.tobytes())
        context=self.session.context(); context_ns=time.perf_counter_ns(); after=self.binding()
        self.observed_focus=after['focus'] if before['focus']==after['focus'] else None
        self.observed_pointer=(dict(after) if before==after and after['surface'] is not None else None)
        self.sequence+=1
        metadata={'id':identifier,'step':index,'sequence':self.sequence,'capture_ns':capture_ns,
                  'pointer_binding':self.observed_pointer}
        typed=extract_typed_observation(image,metadata,self.signal_readers)
        self.emit(typed); typed_emit_return_ns=time.perf_counter_ns()
        return before,after,started_ns,image,capture_ns,source,context,context_ns,typed,typed_emit_return_ns

    def _publish_captured(self, parts, identifier, index, release_before_publish):
        before,after,started_ns,image,capture_ns,source,context,context_ns,typed,typed_emit_return_ns=parts
        packet=self.encoder.encode(source,action_id=f'{identifier}:{index}',observed_ns=capture_ns,context=context)
        frame=self.decoder.accept(packet)
        if frame!=source: raise AssertionError('wire reconstruction failed')
        (self.out/f'{self.sequence:03d}.ait').write_bytes(packet)
        artifact=self.images.publish(frame); artifact_ready_ns=time.perf_counter_ns()
        self.last_context=dict(context)
        self.emit({'event':'observation','id':identifier,'step':index,'sequence':self.sequence,
            'capture_ns':capture_ns,'context_ns':context_ns,'context':context,**artifact,
            'input_focus_before':before['focus'],'input_focus_after':after['focus'],
            'focus_samples_match':before['focus']==after['focus'],'pointer_binding':self.observed_pointer,
            'pointer_context_before':before,'pointer_context_after':after,
            'capture_ms':(capture_ns-started_ns)/1e6,'wire_bytes':len(packet),'exact':True,
            'frame_rgb_sha256':typed['frame_rgb_sha256'],'typed_ready_ns':typed['typed_ready_ns'],
            'typed_emit_return_ns':typed_emit_return_ns,'artifact_ready_ns':artifact_ready_ns,
            'capture_to_artifact_ready_ms':(artifact_ready_ns-capture_ns)/1e6,
            'two_phase_release_before_artifact':bool(release_before_publish),
            'semantic_completion':'unknown'})
        return artifact_ready_ns

    def execute(self, step, cancel, identifier, index):
        if step.get('op')!='hold':
            return super().execute(step,cancel,identifier,index)
        previous=getattr(self._release_batch,'context',None)
        self._release_batch.context={'rows':[],'identifier':identifier,'step':index}
        split_used=False
        try:
            if not hasattr(cancel,'expected_focus'):
                cancel.expected_focus=self.observed_focus
                b=self.observed_pointer
                cancel.expected_surface=b['surface'] if b else None
                cancel.expected_geometry=list(b['geometry']) if b else None
            if cancel.expected_focus in (None,0,1) or getattr(cancel,'focus_invalid',False):
                raise DecisionRequired()
            def checkpoint():
                if cancel.is_set(): raise Cancelled()
            for key in step['keys']:
                checkpoint(); self.raw(key,True)
            self.emit({'event':'keys_held','id':identifier,'step':index,'keys':sorted(self.held),
                       'input_ack_ns':time.perf_counter_ns()})
            deadline_ns=time.perf_counter_ns()+int(step['duration_ms']*1_000_000)
            sample_ns=50_000_000
            while True:
                checkpoint(); now=time.perf_counter_ns(); remaining=deadline_ns-now
                if remaining<=0: break
                if remaining<=sample_ns:
                    # Capture the final pre-release frame, but keep durable publication outside authority.
                    parts=self._capture_typed(identifier,index)
                    while True:
                        checkpoint(); remaining=deadline_ns-time.perf_counter_ns()
                        if remaining<=0: break
                        if cancel.wait(min(.005,remaining/1e9)): raise Cancelled()
                    release_started=time.perf_counter_ns()
                    for key in list(self.held): self.raw(key,False)
                    release_returned=time.perf_counter_ns()
                    artifact_ready=self._publish_captured(parts,identifier,index,True)
                    self.emit({'event':'two_phase_observation_boundary','id':identifier,'step':index,
                               'capture_ns':parts[4],'typed_emit_return_ns':parts[9],
                               'release_started_ns':release_started,'release_returned_ns':release_returned,
                               'artifact_ready_ns':artifact_ready,
                               'release_before_artifact':release_returned<=artifact_ready})
                    split_used=True; break
                self.snapshot(identifier,index)
                remaining=deadline_ns-time.perf_counter_ns()
                if remaining<=0: break
                if cancel.wait(min(.05,remaining/1e9)): raise Cancelled()
        finally:
            for key in list(self.held): self.raw(key,False)
            if previous is None:
                try: del self._release_batch.context
                except AttributeError: pass
            else:self._release_batch.context=previous
        checkpoint()
        # Preserve ordinary post-release observation.
        self.snapshot(identifier,index)
        self.emit({'event':'two_phase_hold_result','id':identifier,'step':index,
                   'split_used':split_used,'semantic_completion':'unknown'})
