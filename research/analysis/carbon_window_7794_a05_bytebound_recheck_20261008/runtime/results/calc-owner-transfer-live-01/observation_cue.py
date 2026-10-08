"""App-local synchronous Calc cue. No capture, input, alias mint or retry."""
import copy, hashlib, io, json, subprocess, time
from pathlib import Path
from PIL import Image
from cell_cue import cell_pair_cue

class CueUnavailable(ValueError): pass

def positive_int(value):
    return type(value) is int and value > 0

def bridge_context(bridge):
    # Read-only existing bridge APIs; no observe, input, review or alias change.
    return {'scope':bridge.scope,'revision':bridge.binding_revision,
            'binding':bridge._binding(),'focus_ok':bridge._focus_within_target(),
            'sequence':bridge.sequence,'title':bridge._window_title(),
            'review_required':bridge.review_required,
            'busy':bridge.active is not None,
            'recovery_required':bridge.session.recovery_required}

class CalcObservationCue:
    def __init__(self, *, capture_root, evidence_root, approved, context,
                 deadline_ns, clock=time.monotonic_ns, runner=subprocess.run,
                 max_age_ns=1_500_000_000):
        if not positive_int(deadline_ns) or not positive_int(max_age_ns):
            raise ValueError('positive monotonic deadline and age required')
        if approved.get('geometry_reviewed') is not True:
            raise ValueError('fresh primary geometry review required')
        if approved.get('image_size') != [1280,800]:
            raise ValueError('historical cue requires freshly reviewed 1280x800 layout')
        if not isinstance(approved.get('scope'),str) or not approved['scope']:
            raise ValueError('reviewed session scope required')
        if type(approved.get('revision')) is not int or approved['revision']<0:
            raise ValueError('strict reviewed binding revision required')
        if not isinstance(approved.get('titles'),list) or not approved['titles'] or any(type(t) is not str or not t for t in approved['titles']):
            raise ValueError('explicit reviewed main-sheet titles required')
        self.capture_root=Path(capture_root).resolve()
        self.evidence_root=Path(evidence_root)
        self.evidence_root.mkdir(parents=True,exist_ok=False)
        self.approved=copy.deepcopy(approved);self.context=context
        self.deadline_ns=deadline_ns;self.clock=clock;self.runner=runner
        self.max_age_ns=max_age_ns;self.calls=0
        self.seen=set()

    def check_context(self,native):
        now=self.clock();start=native.get('capture_ns')
        if not positive_int(start) or not start <= now < self.deadline_ns:
            raise CueUnavailable('capture clock or caller deadline')
        if now-start > self.max_age_ns:
            raise CueUnavailable('capture too old')
        try:state=self.context()
        except Exception as error:raise CueUnavailable('context sampling failed: '+type(error).__name__) from error
        if type(state.get('revision')) is not int or type(native.get('binding_revision')) is not int:
            raise CueUnavailable('invalid binding revision type')
        if not positive_int(state.get('sequence')):
            raise CueUnavailable('invalid current sequence type')
        if state.get('busy') is not False or state.get('recovery_required') is not False:
            raise CueUnavailable('busy or recovery pending')
        for key in ('scope','revision','binding'):
            if state.get(key)!=self.approved.get(key):
                raise CueUnavailable('reviewed association changed')
        if state.get('focus_ok') is not True or state.get('review_required') is not False:
            raise CueUnavailable('focus or review unknown')
        if state.get('sequence')!=native.get('sequence'):
            raise CueUnavailable('observation replaced')
        if state.get('title') not in self.approved.get('titles',[]):
            raise CueUnavailable('unreviewed title or modal')
        if native.get('binding_revision')!=state['revision'] or native.get('pointer_binding')!=state['binding']:
            raise CueUnavailable('native binding does not match reviewed association')
        return state

    def __call__(self,native,rgb):
        self.calls+=1;prefix=self.evidence_root/f'{self.calls:03d}'
        record={'sequence':native.get('sequence'),'cue':'unknown','reason':None,
                'started_ns':self.clock(),'command':['tesseract','stdin','stdout','--psm','11','tsv'],
                'extra_capture':False,'input_dispatched':False,'source_context_verified':False}
        try:
            if not positive_int(native.get('sequence')) or native['sequence'] in self.seen:
                raise CueUnavailable('invalid or reused sequence')
            self.seen.add(native['sequence'])
            before=self.check_context(native)
            meta=native['native'];artifact=meta['artifact']
            path=Path(artifact['path']).resolve()
            if not path.is_relative_to(self.capture_root):
                raise CueUnavailable('artifact outside owned capture root')
            if artifact.get('mime_type')!='image/png' or artifact.get('bytes',0)>32*1024*1024:
                raise CueUnavailable('invalid artifact format or size')
            data=path.read_bytes();digest=hashlib.sha256(data).hexdigest()
            record['artifact_sha256']=digest
            if digest!=artifact['sha256'] or len(data)!=artifact['bytes']:
                raise CueUnavailable('artifact identity mismatch')
            if artifact.get('source_raw_sha256')!=meta.get('sha256'):
                raise CueUnavailable('artifact/raw association mismatch')
            if meta.get('frame')!='screen_physical_px' or meta.get('region')!=[0,0,1280,800]:
                raise CueUnavailable('unreviewed capture coordinates')
            if [meta.get('width'),meta.get('height')]!=[1280,800] or [artifact.get('width'),artifact.get('height')]!=[1280,800]:
                raise CueUnavailable('capture dimensions mismatch')
            if meta.get('native_window_id')!=before['binding']['surface']:
                raise CueUnavailable('capture target mismatch')
            if not native['capture_ns']<=meta['capture_ended_ns']<=self.clock():
                raise CueUnavailable('capture interval mismatch')
            decoded=Image.open(io.BytesIO(data));decoded.load();decoded=decoded.convert('RGB')
            if rgb.mode!='RGB' or rgb.size!=(1280,800) or decoded.size!=rgb.size or decoded.tobytes()!=rgb.tobytes():
                raise CueUnavailable('RGB handoff differs from original PNG')
            self.check_context(native)
            timeout=min(1.0,(self.deadline_ns-self.clock())/1e9,
                        (native['capture_ns']+self.max_age_ns-self.clock())/1e9)
            if timeout<=0:raise CueUnavailable('no OCR budget')
            record['timeout_seconds']=timeout
            result=self.runner(record['command'],input=data,capture_output=True,timeout=timeout,check=False)
            prefix.with_suffix('.tsv').write_bytes(result.stdout)
            prefix.with_suffix('.stderr').write_bytes(result.stderr)
            record['returncode']=result.returncode
            if result.returncode!=0:raise CueUnavailable('OCR failed')
            if len(result.stdout)>1024*1024:raise CueUnavailable('OCR output exceeds bound')
            after=self.check_context(native)
            if after!=before:raise CueUnavailable('context changed during OCR')
            record['source_context_verified']=True
            record['cue']=cell_pair_cue(result.stdout.decode('utf-8'),main_sheet_reviewed=True,modal_present=False)
            record['reason']='current-image cue; not saved-workbook completion'
        except (CueUnavailable,KeyError,TypeError,ValueError,OSError,subprocess.TimeoutExpired) as error:
            record['cue']='unknown';record['reason']=str(error)
            if isinstance(error,subprocess.TimeoutExpired):
                prefix.with_suffix('.tsv').write_bytes(error.stdout or b'')
                prefix.with_suffix('.stderr').write_bytes(error.stderr or b'')
        record['ended_ns']=self.clock()
        prefix.with_suffix('.json').write_text(json.dumps(record,indent=2)+'\n')
        return {'cells':record['cue'],'sheet_context':record['cue']!='unknown','source_context_verified':record['source_context_verified']}
