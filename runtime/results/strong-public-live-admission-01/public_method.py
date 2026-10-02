"""Caller-authored Calc composition of genuine ordinary public API operations.

No graph/guarded alias substitution, model, repair, rebind or durable-state oracle.
Per-key guarded semantics remain a disclosed difference from compiled.run.
"""
import hashlib,io,json,time
from pathlib import Path
from PIL import Image
from runtime.cli_v1.observe import observe_in_session
from runtime.cli_v1.api import dispatch_in_session
from runtime.cli_v1.review import present_result
from runtime.cli_v1.x11_target_review import inspect_focused_target
from delivered_capture import DeliveredCapture

ENTER=[{'op':'key_chord','keys':['CTRL','Home']},{'op':'text','text':'317','gap_ms':20},
       {'op':'key_chord','keys':['ENTER']},{'op':'wait_update','timeout_ms':100},
       {'op':'text','text':'529','gap_ms':20},{'op':'key_chord','keys':['ENTER']},
       {'op':'wait_update','timeout_ms':100}]
SAVE=[{'op':'key_chord','keys':['CTRL','s']}]

class Yield(Exception):pass

def run(owner,ground,regions,out,read_cells,*,sequence,target='app',compact=False):
    out=Path(out);out.mkdir(exist_ok=False)
    if type(sequence) is not int or sequence<1:raise ValueError('explicit initial sequence')
    if set(regions)!={'A1','A2'} or not callable(read_cells):raise ValueError('same exact two-cell reader required')
    box=ground['box'];pixels=ground['pixels']
    if type(box) is not list or len(box)!=4 or any(type(v) is not int for v in box) or not (0<=box[0]<box[2]<=1280 and 0<=box[1]<box[3]<=800):raise ValueError('bounded grounded context box')
    if not isinstance(pixels,bytes) or len(pixels)!=(box[2]-box[0])*(box[3]-box[1])*3:raise ValueError('exact RGB context pixels')
    for region in regions.values():
        if type(region) is not list or len(region)!=4 or any(type(v) is not int for v in region) or not (0<=region[0]<region[2]<=1280 and 0<=region[1]<region[3]<=800):raise ValueError('bounded exact cell regions')
    revision=owner.binding_revision;window=owner.targets[target]
    started=time.monotonic_ns();deadline=started+10_000_000_000
    state=DeliveredCapture();prefix=[];reports=[];count=0;shown=None
    def retain(name,row):
        with (out/(name+'.json')).open('x') as f:json.dump(row,f,indent=2)
    def check():
        if time.monotonic_ns()>=deadline:raise Yield('budget_exhausted')
        if owner.binding_revision!=revision or owner.targets[target]!=window:raise Yield('association_changed')
    def select(raw):
        nonlocal sequence,shown
        shown=present_result(raw,out,compact=compact,report_refs=compact)
        native=state.accept(raw,shown)
        if native is None:raise Yield('delivered_capture_unavailable')
        sequence+=1
        return native
    def perceive(native):
        nonlocal count
        check();artifact=native['artifact'];payload=Path(artifact['path']).read_bytes()
        if hashlib.sha256(payload).hexdigest()!=artifact['sha256']:raise Yield('artifact_changed')
        rgb=Image.open(io.BytesIO(payload)).convert('RGB')
        evidence=inspect_focused_target(owner.get().backend,owner.family_roots[target])
        check()
        if evidence['window_id']!=window or rgb.crop(box).tobytes()!=pixels:raise Yield('dependency_changed')
        count+=1;rows=read_cells(rgb,regions,out/('reading-'+str(count)))
        retain('perception-'+str(count),{'source_sha256':artifact['sha256'],'evidence':evidence,'reading':rows})
        check();return rows
    def dispatch(name,ops):
        check()
        program={'schema':'agent-interface/program-v1','program_id':'public-calc-'+name,
          'source':{'observation_seq':sequence,'binding_revision':revision},
          'authority':{'lease_id':'public-calc-'+name,'expires_at_ns':min(deadline,time.monotonic_ns()+2_000_000_000)},
          'terminal':{'release_all_required':True},
          'ops':[{'op':'focus','target':target},*ops,{'op':'release_all'}]}
        retain(name+'-request',program);state.accept({},{});owner.dispatch_attempted=True
        raw=dispatch_in_session(owner.get(),program,current_observation_seq=sequence,current_binding_revision=revision,capture_directory=str(out/'images'))
        retain(name+'-input',raw);reports.append(raw)
        result=raw.get('result',{});releases=result.get('execution',{}).get('releases',[])
        neutral=bool(releases) and all(r.get('verified') is True and r.get('keys_down')==[] and r.get('buttons_down')==[] and 'error' not in r for r in releases)
        if result.get('status')!='completed' or result.get('recovery_required') is not False or not neutral:raise Yield('input_incomplete_or_release_unverified')
        prefix.append(name)
        raw['post_dispatch_inspection']=owner.inspect_after_dispatch(raw,target,screen_region=[0,0,1280,800],capture_directory=str(out/'images'),wait_ms=100)
        retain(name+'-post',raw);check();return raw
    try:
        check()
        initial=observe_in_session(owner.get(),target=target,frame='screen_physical_px',region=[0,0,1280,800],capture_directory=str(out/'images'))
        retain('initial',initial);perceive(select(initial))
        rows=perceive(select(dispatch('enter',ENTER)))
        if [rows[k]['value'] for k in ['A1','A2']]!=['317','529']:raise Yield('cells_unknown_or_mismatch')
        saved=dispatch('save',SAVE)
        shown=present_result(saved,out,compact=compact,report_refs=compact)
        if state.accept(saved,shown) is not None:sequence+=1
        outcome,reason='SAFE_YIELD','save_handoff_requires_primary_review'
    except Yield as error:outcome,reason='SAFE_YIELD',str(error)
    except Exception as error:outcome,reason='RUNTIME_FAILED',repr(error)
    row={'outcome':outcome,'reason':reason,'confirmed_completed_inputs':prefix,
      'sequence':sequence,'binding_revision':owner.binding_revision,'task_success':None,
      'replay_allowed':False,'started_ns':started,'ended_ns':time.monotonic_ns(),
      'local_readings':count,'final_capture':state.current,'scope':'public local composition; no durable scoring or model feedback acknowledgement'}
    retain('receipt',row)
    return row
