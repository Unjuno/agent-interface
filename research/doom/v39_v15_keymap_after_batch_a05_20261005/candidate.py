from __future__ import annotations
import importlib.util, json, sys, threading, time, types
from pathlib import Path

ROOT=Path(__file__).resolve().parents[3]
DOOM=ROOT/'research/doom'; LIVE=ROOT/'research/live_control'
V12DIR=DOOM/'map01_attack_onset_phase_allocation_02_v1/dependencies/v12'
sys.path[:0]=[str(ROOT),str(DOOM),str(LIVE),str(V12DIR)]

def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path)
    if spec is None or spec.loader is None:raise RuntimeError('module load failed: '+str(path))
    module=importlib.util.module_from_spec(spec);sys.modules[name]=module;spec.loader.exec_module(module);return module

def _pressed(bitmap,code):
    if not isinstance(bitmap,(bytes,bytearray)) or len(bitmap)!=32:return None
    return bool(bitmap[code//8] & (1 << (code%8)))

def run_case(case_name,drop_key=None,query_unavailable=False):
    from map01_v39_perkey_bridge_a01 import test_bridge
    harness_module=test_bridge.load_v12_test_harness()  # installs inert X/PIL bindings
    load('input_owner_v10',LIVE/'input_owner_v10.py')
    owner_module=load('input_owner_v12',LIVE/'input_owner_v12.py')
    harness=harness_module.Harness(owner_module);display=harness.d
    codes={'F8':74,'SPACE':65}
    old_keysym=owner_module.XK.string_to_keysym
    owner_module.XK.string_to_keysym=lambda key:codes[key]
    display.keysym_to_keycode=lambda symbol:symbol
    operations=[]
    old_query,old_sync=display.query_keymap,display.sync
    old_fake=owner_module.xtest.fake_input
    def query_keymap():
        operations.append({'op':'query_keymap','at_ns':time.perf_counter_ns()})
        if query_unavailable:raise RuntimeError('injected post-batch query unavailable')
        return old_query()
    def sync():
        operations.append({'op':'sync','at_ns':time.perf_counter_ns()});return old_sync()
    def fake_input(target,event_type,code=None,**kwargs):
        if event_type==owner_module.X.KeyPress:op='key-down'
        elif event_type==owner_module.X.KeyRelease and code==codes.get(drop_key):op='key-up-dropped'
        else:op='key-up' if event_type==owner_module.X.KeyRelease else 'other-input'
        operations.append({'op':op,'keycode':code,'at_ns':time.perf_counter_ns()})
        if op=='key-up-dropped':return None
        return old_fake(target,event_type,code,**kwargs)
    display.query_keymap=query_keymap;display.sync=sync;owner_module.xtest.fake_input=fake_input
    class FakeOwnerFactory:
        def __new__(cls,display_name):return harness.owner
    from input_transition_owner_v4 import InputOwner as OwnerV4
    owner=OwnerV4(':fake',_owner_cls=FakeOwnerFactory)
    lease=harness_module.Lease(intent='intent-v39-keymap-a05-'+case_name)
    samples=[];events=[]
    original_call=owner.call
    def call(operation,lease_arg=None,key=None):
        if operation!='input_state':return original_call(operation,lease_arg,key)
        operations.append({'op':'owner-input-state-start','at_ns':time.perf_counter_ns()})
        state=original_call(operation,lease_arg,key)
        state_returned=time.perf_counter_ns()
        operations.append({'op':'owner-input-state-return','at_ns':state_returned})
        start=time.perf_counter_ns();operations.append({'op':'post-batch-query-start','at_ns':start})
        try:
            bitmap=owner_module.display  # ensure trace is from the same fake X connection
            bitmap=display.query_keymap()
            finish=time.perf_counter_ns()
            sample={'status':'SAMPLED','sample_started_ns':start,'sample_finished_ns':finish,
                    'owner_state_returned_ns':state_returned,'key_down':{k:_pressed(bitmap,codes[k]) for k in codes}}
        except BaseException as exc:
            finish=time.perf_counter_ns()
            sample={'status':'UNKNOWN','reason':type(exc).__name__, 'sample_started_ns':start,
                    'sample_finished_ns':finish,'owner_state_returned_ns':state_returned,'key_down':None}
        operations.append({'op':'post-batch-query-finish','at_ns':finish,'status':sample['status']})
        samples.append(sample)
        return state
    owner.call=call
    def emit(row):
        row=dict(row)
        if row.get('event')=='input_release_transition':
            sample=samples[-1] if samples else {'status':'UNKNOWN','reason':'missing_sample','key_down':None}
            row['post_batch_keymap_sample']=dict(sample)
            down=(sample.get('key_down') or {}).get(row.get('key'))
            if sample.get('status')!='SAMPLED':row['server_keymap_disposition']='UNKNOWN'
            else:row['server_keymap_disposition']='SERVER_KEY_STILL_DOWN' if down is True else 'NOT_DOWN_AT_POST_BATCH_SAMPLE' if down is False else 'UNKNOWN'
            row['physical_verification_authoritative']=False
            row['application_consumption_observed']=False
            operations.append({'op':'release-row-emit','key':row.get('key'),'at_ns':time.perf_counter_ns()})
        events.append(row)
    # Match the runtime closure: actual V15 backend + typed-release-v2 + actual v4.
    # Only the generic command interpreter/capture superclass is replaced with this list driver.
    class InterpreterSeam:
        def execute(self,step,cancel,identifier,index):
            for key,down in step['actions']:self.raw(key,down)
            return {'seam':'deterministic-action-list'}
        def release_all(self):return {'verified':True}
    base=types.ModuleType('doom_typed_release_backend_v1');base.Backend=InterpreterSeam;base.suite=object()
    sys.modules['doom_typed_release_backend_v1']=base
    for mod in ('input_transition_owner_v3','input_transition_owner_v4','doom_typed_release_backend_v2','doom_owner_thread_release_batch_backend_v1'):
        sys.modules.pop(mod,None)
    import doom_owner_thread_release_batch_backend_v1 as production_backend
    from doom_typed_release_backend_v2 import Backend as TypedV2
    actual_owner=production_backend.InputOwner
    backend=production_backend.Backend.__new__(production_backend.Backend)
    backend.owner=owner;backend.lease=lease;backend.held=set();backend._release_batch=threading.local()
    backend._last_release_batch_delivery=None;backend._input_event_context=None;backend.emit=emit
    try:
        backend.execute({'actions':[('F8',True),('SPACE',True),('SPACE',False),('F8',False)]},None,'cover-'+case_name,1)
        up_indices=[i for i,x in enumerate(operations) if x['op'] in ('key-up','key-up-dropped')]
        between=operations[up_indices[0]+1:up_indices[1]]
        state_samples=[x for x in operations if x['op']=='owner-input-state-return']
        return {'case':case_name,'backend_class':production_backend.Backend.__module__+'.'+production_backend.Backend.__name__,
                'typed_v2_class':TypedV2.__module__+'.'+TypedV2.__name__,'owner_class':actual_owner.__module__+'.'+actual_owner.__name__,
                'events':events,'operations':operations,'between_up_operations':between,
                'keymap_queries_between_ups':sum(x['op']=='query_keymap' for x in between),
                'sample_count':len(samples),'fake_physical_after':sorted(display.physical),
                'backend_held_after':sorted(backend.held),'owner_keycodes_after':state_samples[-1].get('owned_keycodes',[]) if state_samples else None,
                'query_unavailable_injected':query_unavailable,'dropped_release_key':drop_key}
    finally:
        owner_module.xtest.fake_input=old_fake;display.query_keymap=old_query;display.sync=old_sync
        owner_module.XK.string_to_keysym=old_keysym
        owner.close();harness.close()

def run():
    # Runtime selector source has V12 default and V15 opt-in; this is a static selector check,
    # while the actual selected backend/owner classes execute below.
    controller=(DOOM/'map01_overlap_controller_v39.py').read_text(encoding='utf-8')
    start=controller.index('def session_command(');end=controller.index('\ndef ',start+4)
    selector=controller[start:end]
    if not all(x in selector for x in ('measurement_session','session_map01_v15.py','session_map01_v12.py')):
        raise RuntimeError('V39 session selector source contract mismatch')
    return {'schema':'v39-v15-post-batch-keymap-candidate-v1','selector_source_verified':True,
            'cases':[run_case('normal'),run_case('missed-space-up',drop_key='SPACE'),run_case('query-unavailable',query_unavailable=True)]}
