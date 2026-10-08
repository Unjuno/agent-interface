"""App-local explicit Save dependency guard; no alias mint, OCR or replay."""
import copy, hashlib, time
from contextlib import contextmanager
from runtime.backends.x11_v1.backend import X11BackendError

class SemanticSaveGuard:
    def __init__(self,bridge,*,alias,offset,regions,deadline_ns,clock=time.monotonic_ns):
        if type(deadline_ns) is not int or deadline_ns<=0:
            raise ValueError('positive caller deadline required')
        if not regions or any(len(box)!=4 or any(type(v) is not int for v in box) or not (0<=box[0]<box[2] and 0<=box[1]<box[3]) for box in regions):
            raise ValueError('explicit primary-reviewed cell rectangles required')
        self.bridge=bridge;self.alias=alias;self.offset=copy.deepcopy(offset)
        self.regions=copy.deepcopy(regions);self.deadline_ns=deadline_ns;self.clock=clock
        self.snapshot=None;self.events=[];self.installed=False

    def arm(self,native,rgb,*,cue_record):
        b=self.bridge
        if self.snapshot is not None:raise ValueError('dependency cannot be renewed')
        if b.active is not None or b.review_required or b.session.recovery_required:
            raise ValueError('cannot arm during input or unresolved review/recovery')
        if native['sequence']!=b.sequence or native['binding_revision']!=b.binding_revision or native['pointer_binding']!=b._binding():
            raise ValueError('exact current source association required')
        original,image=b.history[native['sequence']]
        if original!=native or rgb.mode!='RGB' or image.mode!='RGB' or rgb.size!=image.size or rgb.tobytes()!=image.tobytes():
            raise ValueError('exact native RGB history source required')
        if cue_record.get('cue')!='filled' or cue_record.get('sequence')!=native['sequence'] or cue_record.get('artifact_sha256')!=native['native']['artifact']['sha256']:
            raise ValueError('current filled-cell OCR evidence required')
        if self.clock()>=min(self.deadline_ns,native['capture_ns']+1_500_000_000):raise ValueError('expired dependency source')
        if any(box[2]>rgb.width or box[3]>rgb.height for box in self.regions):raise ValueError('dependency outside frame')
        self.snapshot={'scope':b.scope,'revision':b.binding_revision,'binding':copy.deepcopy(native['pointer_binding']),
         'source_sequence':native['sequence'],'source_capture_ns':native['capture_ns'],'size':rgb.size,
         'pixels':[rgb.crop(box).tobytes() for box in self.regions]}
        self.events.append({'event':'armed','source_sequence':native['sequence'],'artifact_sha256':cue_record['artifact_sha256'],'renewal':False,'authority_granted':False})

    def validate(self,stage):
        b=self.bridge;s=self.snapshot;reason=None
        if s is None:reason='unarmed dependency'
        elif self.clock()>=self.deadline_ns:reason='caller deadline expired'
        elif b.scope!=s['scope'] or b.binding_revision!=s['revision'] or b._binding()!=s['binding'] or b.review_required or b.session.recovery_required or not b._focus_within_target():reason='association or focus changed'
        else:
            native,rgb=b.history[b.sequence]
            if native['sequence']<=s['source_sequence'] or native['binding_revision']!=s['revision'] or native['pointer_binding']!=s['binding'] or rgb.mode!='RGB' or rgb.size!=s['size']:
                reason='guard capture association changed'
            elif not native['capture_ns']<=self.clock()<native['capture_ns']+1_500_000_000:reason='guard capture stale'
            elif any(rgb.crop(box).tobytes()!=pixels for box,pixels in zip(self.regions,s['pixels'])):reason='cell dependency pixels changed'
        self.events.append({'event':'dependency_checked','stage':stage,'sequence':b.sequence,'eligible':reason is None,'reason':reason,'checked_ns':self.clock()})
        if reason is not None:raise X11BackendError('Calc Save dependency refused: '+reason)

    @contextmanager
    def installed_guard(self):
        if self.installed:raise RuntimeError('guard already installed')
        b=self.bridge;old_check=b.check;old_key=b.backend.key_state
        protected=(self.alias,self.offset)
        def check(stage):
            outcome=old_check(stage)  # Retain every original capture/alias/lease check.
            if b.active==protected:self.validate(stage)
            return outcome
        def key_state(key,down):
            if down and b.active==protected:
                # Existing key guard checks focus/lease; this additionally captures
                # and validates both semantic ROIs before each new key press.
                b.check('before_save_key_press:'+str(key))
            return old_key(key,down)  # Releases remain possible after refusal.
        b.check=check;b.backend.key_state=key_state;self.installed=True
        try:yield self
        finally:
            b.check=old_check;b.backend.key_state=old_key;self.installed=False

    @contextmanager
    def install_for_save(self,save_tail):
        """Explicit caller composition around the one frozen Save program."""
        if not save_tail or not any(op.get('op')=='key_chord' and op.get('keys')==['CTRL','S'] for op in save_tail):
            raise ValueError('explicit frozen Ctrl+S tail required')
        expected=copy.deepcopy(save_tail);b=self.bridge;old_keyboard=b.keyboard
        def keyboard(alias,offset,*,tail,expires_at_ns=None):
            save_requested=any(op.get('op')=='key_chord' and set(op.get('keys',[]))=={'CTRL','S'} for op in tail)
            if save_requested and (alias!=self.alias or offset!=self.offset or list(tail)!=expected):
                raise ValueError('Save differs from frozen guarded program')
            if alias==self.alias and offset==self.offset and list(tail)==expected:
                with self.installed_guard():
                    return old_keyboard(alias,offset,tail=tail,expires_at_ns=expires_at_ns)
            return old_keyboard(alias,offset,tail=tail,expires_at_ns=expires_at_ns)
        b.keyboard=keyboard
        try:yield self
        finally:b.keyboard=old_keyboard
