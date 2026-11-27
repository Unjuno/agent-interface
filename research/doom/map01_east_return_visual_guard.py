"""Fixed post-cross image resemblance gate for the east-return experiment."""
import hashlib
import io
import time
from pathlib import Path
from PIL import Image,ImageChops,ImageStat

ROI=(480,300,800,500)
MAX_MEAN_ABSOLUTE_DIFFERENCE=15
MAX_FRAME_AGE_NS=2_000_000_000
SIZE=(1280,800)
REFERENCE_GEOMETRY=[321,180,640,480]

def check(source,*,reference,reference_sha256,runtime_dir,terminal,transition,settlement,expected,typed,clock=time.perf_counter_ns):
    start=clock()
    if type(source) is not dict or source.get('id')!='reverse-cross' or type(source.get('step')) is not int or source.get('step')!=0 or type(source.get('sequence')) is not int or source['sequence']<1:
        raise ValueError('wrong observation')
    # The caller supplies its independently tracked last observation and identity,
    # plus the actual terminal, release transition and completed settlement.
    if not all(type(row) is dict for row in (terminal,transition,settlement,expected,typed)):
        raise ValueError('missing completed operation evidence')
    paired_fields=('id','step','sequence','capture_ns','frame_rgb_sha256','pointer_binding',
                   'renewal_owner_id','input_owner_generation','target_process_identity',
                   'target_renewal_window_identity')
    if (typed.get('event')!='typed_observation' or type(typed.get('step')) is not int
        or typed['step']!=0 or any(typed.get(k)!=source.get(k) for k in paired_fields)):
        raise ValueError('typed and full observations differ')
    if expected.get('geometry')!=REFERENCE_GEOMETRY:
        raise ValueError('window geometry differs from fixed reference')
    up=transition.get('owner_thread_keyup_receipt');release=terminal.get('release')
    process=source.get('target_process_identity');window=source.get('target_renewal_window_identity')
    if (any(type(expected.get(k)) is not str or not expected[k] for k in ('owner','process_digest','window_digest'))
        or type(expected.get('sequence')) is not int or type(expected.get('generation')) is not int
        or type(expected.get('surface')) is not int or type(expected.get('geometry')) is not list
        or source.get('event')!='observation' or type(up) is not dict or type(release) is not dict
        or type(process) is not dict or type(window) is not dict
        or terminal.get('event')!='terminal' or terminal.get('id')!='reverse-cross'
        or terminal.get('status')!='completed' or release.get('verified') is not True
        or any(release.get(key)!=[] for key in ('keys_down','buttons_down','keys_unknown','key_state_errors'))
        or transition.get('event')!='input_release_transition' or transition.get('id')!='reverse-cross'
        or transition.get('operation')!='up' or transition.get('key')!='Up'
        or any(transition.get(key) is not True for key in ('owner_transition_verified','admission_receipt_valid','release_batch_complete','owner_sample_ordered_after_batch','owner_identity_matches_after_batch','intent_token_matches_after_batch','owner_thread_keyup_verified_after_batch'))
        or transition.get('owned_keycodes_after_batch')!=[] or up.get('server_keyup_verified') is not True
        or up.get('key')!='Up' or not transition.get('intent_token')
        or transition.get('intent_token')!=up.get('intent_token') or transition.get('intent_token')!=release.get('intent_token')
        or settlement.get('event')!='door_settle' or settlement.get('operation_id')!='reverse-cross'
        or settlement.get('status')!='DONE'
        or source.get('sequence')!=expected.get('sequence')
        or source.get('renewal_owner_id')!=expected.get('owner') or source.get('input_owner_generation')!=expected.get('generation')
        or terminal.get('input_owner_id')!=expected.get('owner') or terminal.get('input_owner_generation')!=expected.get('generation')
        or transition.get('owner_id')!=expected.get('owner') or up.get('owner_id')!=expected.get('owner')
        or process.get('sequence')!=source.get('sequence') or window.get('sequence')!=source.get('sequence')
        or process.get('surface')!=expected.get('surface') or window.get('surface')!=expected.get('surface')
        or process.get('digest')!=expected.get('process_digest') or window.get('digest')!=expected.get('window_digest')):
        raise ValueError('operation, owner or target evidence differs')
    keyup_ns=up.get('owner_keymap_sampled_ns');sample_ns=transition.get('owner_sample_after_finished_ns')
    captured_ns=source.get('capture_ns');terminal_ns=terminal.get('terminal_ns');settled_ns=settlement.get('emit_ns')
    if (any(type(value) is not int for value in (keyup_ns,sample_ns,captured_ns,terminal_ns,settled_ns))
        or not 0<=keyup_ns<=sample_ns<=captured_ns<=terminal_ns<=settled_ns<=start):
        raise ValueError('observation is not post-release and settled')
    binding=source.get('pointer_binding')
    if (type(binding) is not dict or type(binding.get('surface')) is not int or binding.get('surface')!=expected.get('surface') or binding.get('geometry')!=expected.get('geometry') or binding.get('focus')!=binding['surface']
        or source.get('input_focus_before')!=binding['surface'] or source.get('input_focus_after')!=binding['surface']
        or source.get('exact') is not True or source.get('focus_samples_match') is not True
        or type(source.get('renewal_owner_id')) is not str or not source['renewal_owner_id']
        or type(source.get('input_owner_generation')) is not int or source['input_owner_generation']<0
        or type(source.get('capture_ns')) is not int or not 0<=start-source['capture_ns']<MAX_FRAME_AGE_NS):
        raise ValueError('source is stale or target binding differs')
    reference=Path(reference);frame=Path(source['image']);runtime_dir=Path(runtime_dir)
    if reference.is_symlink() or frame.is_symlink() or frame.parent.resolve()!=runtime_dir.resolve():
        raise ValueError('frame path differs')
    reference_bytes=reference.read_bytes();frame_bytes=frame.read_bytes()
    if hashlib.sha256(reference_bytes).hexdigest()!=reference_sha256:
        raise ValueError('reference digest differs')
    with Image.open(io.BytesIO(reference_bytes)) as im:
        ref=im.convert('RGB')
    with Image.open(io.BytesIO(frame_bytes)) as im:
        current=im.convert('RGB')
    if ref.size!=SIZE or current.size!=SIZE or hashlib.sha256(current.tobytes()).hexdigest()!=source.get('frame_rgb_sha256'):
        raise ValueError('frame pixels differ')
    diff=ImageChops.difference(ref.crop(ROI),current.crop(ROI))
    total=int(sum(ImageStat.Stat(diff).sum));components=(ROI[2]-ROI[0])*(ROI[3]-ROI[1])*3
    end=clock()
    if type(end) is not int or not start<=end or not 0<=end-source['capture_ns']<MAX_FRAME_AGE_NS:
        raise ValueError('source expired during comparison')
    return {'passed':total<=MAX_MEAN_ABSOLUTE_DIFFERENCE*components,'sequence':source['sequence'],'capture_ns':source['capture_ns'],'frame_rgb_sha256':source['frame_rgb_sha256'],
            'owner_id':source['renewal_owner_id'],'owner_generation':source['input_owner_generation'],
            'surface':binding['surface'],'roi':list(ROI),'difference_sum':total,'component_count':components,
            'limit_mean':MAX_MEAN_ABSOLUTE_DIFFERENCE,'started_ns':start,'finished_ns':end,
            'scope':'post-cross visual resemblance only; not position, facing or door-state proof'}
