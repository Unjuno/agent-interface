from __future__ import annotations
import importlib.util, json, sys, threading, time, types
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
DOOM = ROOT / 'research' / 'doom'
LIVE = ROOT / 'research' / 'live_control'
V12DIR = DOOM / 'map01_attack_onset_phase_allocation_02_v1' / 'dependencies' / 'v12'
sys.path[:0] = [str(ROOT), str(DOOM), str(LIVE), str(V12DIR)]

CAPTURE_DIR = str(Path(__file__).resolve().parent / 'results')

def run(actions, scenario):
    # Install X/PIL stubs, then construct the harness with the exact runtime owner-v12 file.
    from map01_v39_perkey_bridge_a01 import test_bridge
    def load(name, path):
        spec = importlib.util.spec_from_file_location(name, path)
        module = importlib.util.module_from_spec(spec); sys.modules[name] = module
        spec.loader.exec_module(module)
        return module
    harness_module = test_bridge.load_v12_test_harness()
    load('input_owner_v10', LIVE / 'input_owner_v10.py')
    owner_module = load('input_owner_v12', LIVE / 'input_owner_v12.py')
    h = harness_module.Harness(owner_module)
    # The lower typed backend only supplies its interpreter contract here; all
    # measurement and owner layers beneath it are the frozen production sources.
    class TypedInterpreterSeam:
        def execute(self, step, cancel, identifier, index):
            for key, down in step['actions']:
                self.raw(key, down)
            return {'seam': 'deterministic-actions-consumed'}
        def release_all(self):
            return {'verified': True}
    base = types.ModuleType('doom_typed_release_backend_v1')
    base.Backend = TypedInterpreterSeam
    base.suite = object()
    sys.modules['doom_typed_release_backend_v1'] = base
    sys.modules.pop('input_transition_owner_v3', None)
    sys.modules.pop('input_transition_owner_v4', None)
    sys.modules.pop('doom_typed_release_backend_v2', None)
    sys.modules.pop('doom_owner_thread_release_batch_backend_v1', None)

    # Import exact owner-v4 and exact V15 telemetry backend source.
    import doom_owner_thread_release_batch_backend_v1 as production_backend
    owner_v4 = production_backend.InputOwner

    # Verify the actual controller selector source's default and opt-in branch.
    import ast
    selector_path = DOOM / 'map01_overlap_controller_v39.py'
    selector_source = selector_path.read_text(encoding='utf-8')
    tree = ast.parse(selector_source)
    selector = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == 'session_command')
    selector_text = ast.get_source_segment(selector_source, selector)
    selector_ok = all(x in selector_text for x in ('measurement_session', 'session_map01_v15.py', 'session_map01_v12.py'))
    if not selector_ok:
        raise SystemExit('STOP: V39 V12-default/V15-opt-in selector source changed')

    # Give the V12 fake display distinct, recognizable codes and record all owner I/O.
    old_keysym = owner_module.XK.string_to_keysym
    keycodes = {'F8': 74, 'SPACE': 65}
    owner_module.XK.string_to_keysym = lambda value: keycodes[value]
    h.d.keysym_to_keycode = lambda symbol: symbol
    ops=[]; display=h.d
    old_query, old_sync = display.query_keymap, display.sync
    old_fake = owner_module.xtest.fake_input
    def query():
        ops.append({'op':'query_keymap','at_ns':time.perf_counter_ns()}); result=old_query(); snapshot(); return result
    def sync():
        ops.append({'op':'sync','at_ns':time.perf_counter_ns()}); result=old_sync(); snapshot(); return result
    def fake(target, event_type, code=None, **kwargs):
        op='key-down' if event_type==owner_module.X.KeyPress else 'key-up'
        ops.append({'op':op,'keycode':code,'at_ns':time.perf_counter_ns()})
        result=old_fake(target,event_type,code,**kwargs); snapshot(); return result
    display.query_keymap=query; display.sync=sync; owner_module.xtest.fake_input=fake

    class FakeOwnerFactory:
        def __new__(cls, display_name): return h.owner

    owner = owner_v4(':fake', _owner_cls=FakeOwnerFactory)
    lease = harness_module.Lease(intent='intent-samekey-a03-'+scenario)
    events=[]
    backend = production_backend.Backend.__new__(production_backend.Backend)
    backend.owner=owner; backend.lease=lease; backend.held=set()
    backend._release_batch=threading.local(); backend._last_release_batch_delivery=None
    backend._input_event_context=None
    def emit(row):
        events.append(row); snapshot()
    backend.emit=emit
    def snapshot():
        Path(CAPTURE_DIR).mkdir(parents=True, exist_ok=True)
        snapshot_data = {'schema': 'v39-repeat-samekey-partial-v1', 'scenario': scenario,
                         'selector_source_verified': selector_ok, 'selector_source': selector_text,
                         'backend_class': production_backend.Backend.__module__+'.'+production_backend.Backend.__name__,
                         'owner_class': owner_v4.__module__+'.'+owner_v4.__name__,
                         'events': events, 'operations': ops,
                         'fake_physical_after': sorted(display.physical), 'backend_held_after': sorted(backend.held)}
        target = Path(CAPTURE_DIR) / (scenario + '.partial.json')
        target.write_text(json.dumps(snapshot_data, indent=2, sort_keys=True)+'\n', encoding='utf-8')
    try:
        backend.execute({'actions':actions},None,'cover-samekey-a03-'+scenario,2)
        ups=[i for i,x in enumerate(ops) if x['op']=='key-up']
        between=(ops[ups[0]+1:ups[1]] if len(ups) >= 2 else [])
        return {'schema':'v39-repeat-samekey-candidate-v1',
          'selector_source_verified':selector_ok,'selector_source':selector_text,
          'backend_class':production_backend.Backend.__module__+'.'+production_backend.Backend.__name__,
          'owner_class':owner_v4.__module__+'.'+owner_v4.__name__,
          'events':events,'operations':ops,
          'between_up_operations':between,
          'keymap_queries_between_ups':sum(x['op']=='query_keymap' for x in between),
          'key_up_injection_count':len(ups),
          'fake_physical_after':sorted(display.physical),'backend_held_after':sorted(backend.held),
          'fake_display_counts':{'queries':display.query_i,'syncs':display.sync_i,'injections':len(display.injections)}}
    finally:
        owner_module.xtest.fake_input=old_fake; display.query_keymap,display.sync=old_query,old_sync
        owner_module.XK.string_to_keysym=old_keysym; owner.close(); h.close()




if __name__ == '__main__':
    import traceback
    results = []
    cases = [
        ('sequential', [('F8', True), ('F8', False), ('F8', True), ('F8', False)]),
        ('overlapping_duplicate_down', [('F8', True), ('F8', True), ('F8', False)]),
    ]
    out_dir = Path(CAPTURE_DIR); out_dir.mkdir(parents=True, exist_ok=True)
    for name, actions in cases:
        try:
            result = run(actions, name)
            result['case_status'] = 'RETURNED'
        except BaseException as exc:
            result = {'schema': 'v39-repeat-samekey-case-stop-v1', 'scenario': name,
                      'case_status': 'STOP', 'error_type': type(exc).__name__,
                      'error': str(exc), 'traceback': traceback.format_exc()}
            partial = out_dir / (name + '.partial.json')
            if partial.is_file(): result['partial'] = json.loads(partial.read_text(encoding='utf-8'))
        results.append(result)
        (out_dir / (name + '.json')).write_text(json.dumps(result, indent=2, sort_keys=True)+'\n', encoding='utf-8')
    (out_dir / 'RAW.json').write_text(json.dumps({'schema':'v39-repeat-samekey-raw-v1','cases':results},indent=2,sort_keys=True)+'\n',encoding='utf-8')
    print(json.dumps({'schema':'v39-repeat-samekey-runner-receipt-v1','case_statuses':[r.get('case_status') for r in results]},sort_keys=True))

