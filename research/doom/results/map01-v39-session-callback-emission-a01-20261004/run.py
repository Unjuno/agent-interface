import argparse, contextlib, hashlib, importlib.util, io, json, os, sys, tempfile, threading, time, types
from pathlib import Path

REPO = Path(__file__).resolve().parents[4]
cli = argparse.ArgumentParser()
cli.add_argument('--run-id', required=True, help='new, unused output directory name under raw/')
RUN_ID = cli.parse_args().run_id
if not RUN_ID or Path(RUN_ID).name != RUN_ID:
    raise SystemExit('run-id must be a simple nonempty basename')
SESSION_PATH = REPO / 'research/doom/session_map01_v12.py'
BACKEND_PATH = REPO / 'research/doom/doom_typed_release_backend_v3.py'

class FakeOwner:
    def __init__(self, name):
        self.name = name; self.owner_id = 'owner-composition-a01'; self.records = []; self.closed = False
    def call(self, op, lease=None, key=None):
        token = getattr(lease, 'intent_token', None)
        if op == 'down':
            return {'event':'input_admission','operation':'down','key':key,'owner_id':self.owner_id,
                    'intent_token':token,'admitted_ns':100,'input_ack_ns':110}
        if op == 'up':
            receipt = {'event':'owner_explicit_keyup','operation':'up','key':key,'owner_id':self.owner_id,
                       'intent_token':token,'valid_until_ns':1000,'owner_keyrelease_started_ns':220,
                       'owner_sync_returned_ns':230,'server_sync_completed':True,
                       'physical_verification_authoritative':False}
            self.records.append(receipt)
            return {'event':'input_release_transition','operation':'up','key':key,'owner_id':self.owner_id,
                    'intent_token':token,'release_call_started_ns':210,'release_call_returned_ns':240,
                    'valid_until_ns':1000,'ordinary_release_candidate':True,
                    'owner_thread_keyup_receipt':dict(receipt),'owner_thread_keyup_verified':True,
                    'owner_transition_verified':None,'grants_input_authority':False}
        if op == 'input_state':
            return {'owner_id':self.owner_id,'owned_keycodes':[],'sample_started_ns':300,'sample_finished_ns':310}
        if op == 'release':
            record = {'event':'owner_release','reason':'release','owner_id':self.owner_id,
                      'keys_down':[],'buttons_down':[],'verified':True,'valid_until_ns':1000,'verified_ns':400}
            self.records.append(record); return dict(record)
        raise AssertionError(op)
    def close(self):
        if not self.closed:
            self.records.append({'event':'owner_release','reason':'close','owner_id':self.owner_id,
                                 'keys_down':[],'buttons_down':[],'verified':True,'valid_until_ns':1000,'verified_ns':410})
            self.closed = True

class Lease:
    intent_token = 'integration-a01'

class Parent:
    def __init__(self, session, out, emit, signal_readers):
        self.owner = FakeOwner(session.name); self.lease = None; self.held=set(); self.emit=emit; self.out=out
    def execute(self, step, cancel, identifier, index):
        self.lease=Lease()
        for key in step.get('keys',[]): self.raw(key,True)
        for key in step.get('keys',[]): self.raw(key,False)
        return {'accepted':True}
    def snapshot(self, label, index): self.emit({'event':'observation','label':label,'sequence':index,'image':'fixture.png'})
    def release_all(self):
        for key in list(self.held): self.raw(key,False)
        if self.lease is not None: self.owner.call('release',self.lease)
        return {'verified':True}
    def close(self): self.owner.close()

parent=types.ModuleType('doom_typed_release_backend_v1'); parent.Backend=Parent; parent.suite=types.SimpleNamespace(Session=None)
wrapper=types.ModuleType('input_transition_owner_v3'); wrapper.InputOwner=FakeOwner
sys.modules['doom_typed_release_backend_v1']=parent; sys.modules['input_transition_owner_v3']=wrapper
spec=importlib.util.spec_from_file_location('doom_typed_release_backend_v3',BACKEND_PATH)
backend_mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(backend_mod); sys.modules['doom_typed_release_backend_v3']=backend_mod

class FakeSession:
    def __init__(self):
        self.name=':fake-session'; self.tmp=Path(tempfile.mkdtemp(prefix='session-callback-a01-'))
        self.env={k:str(self.tmp/k.lower()) for k in ('DISPLAY','XAUTHORITY','HOME','XDG_CONFIG_HOME','XDG_CACHE_HOME','XDG_RUNTIME_DIR')}
        self.d=types.SimpleNamespace(intern_atom=lambda *_:1,screen=lambda:types.SimpleNamespace(root=types.SimpleNamespace(get_full_property=lambda *_:True)))
    def _wait(self,*_): pass
    def windows(self): return 'id seq win 0 DOOM'
    def focus(self,*_): pass
    def close(self): pass
parent.suite.Session=FakeSession

class FakeExecutor:
    def __init__(self,backend,emit): self.backend=backend; self.closed=False
    def submit(self,identifier,steps,sequence,valid_until):
        for idx,step in enumerate(steps): self.backend.execute(step,threading.Event(),identifier,idx)
    def cancel(self,*_): pass
    def close(self):
        if not self.closed: self.backend.release_all(); self.closed=True
executor_mod=types.ModuleType('executor_v12'); executor_mod.Executor=FakeExecutor; sys.modules['executor_v12']=executor_mod
lease_mod=types.ModuleType('lease'); lease_mod.Expired=type('Expired',(Exception,),{}); sys.modules['lease']=lease_mod
hud_mod=types.ModuleType('doom_hud_signal_v3'); hud_mod.DoomStatusNumberReader=lambda *a,**k:object(); sys.modules['doom_hud_signal_v3']=hud_mod

with tempfile.TemporaryDirectory(prefix='fake-vizdoom-a01-') as temp:
    pkg=Path(temp)/'vizdoom'; pkg.mkdir(); (pkg/'__init__.py').write_text(''); (pkg/'freedoom2.wad').write_bytes(b'fake-iwad')
    vd=types.ModuleType('vizdoom'); vd.__file__=str(pkg/'__init__.py'); vd.__version__='fake-1'
    vd.Mode=types.SimpleNamespace(ASYNC_SPECTATOR='ASYNC_SPECTATOR')
    vd.ScreenResolution=types.SimpleNamespace(RES_640X480='640x480')
    vd.Button=types.SimpleNamespace(**{n:n for n in ('TURN_LEFT','TURN_RIGHT','MOVE_FORWARD','MOVE_BACKWARD','MOVE_LEFT','MOVE_RIGHT','ATTACK','USE','SPEED')})
    vd.GameVariable=types.SimpleNamespace(DEATHCOUNT='DEATHCOUNT',KILLCOUNT='KILLCOUNT')
    class FakeGame:
        def __init__(self): self.tic=1; self.dead=False; self.closed=False
        def __getattr__(self,name):
            if name.startswith('set_') or name in ('init','set_mode','set_seed','set_doom_skill'): return lambda *a,**k:None
            raise AttributeError(name)
        def advance_action(self,*_): self.tic+=1
        def get_episode_time(self): return self.tic
        def get_mode(self): return 'ASYNC_SPECTATOR'
        def get_ticrate(self): return 35
        def get_game_variable(self,var): return 0
        def is_episode_finished(self): return False
        def is_player_dead(self): return self.dead
        def get_total_reward(self): return 0
        def close(self): self.closed=True
    vd.DoomGame=FakeGame; sys.modules['vizdoom']=vd
    pil=types.ModuleType('PIL'); imagegrab=types.ModuleType('PIL.ImageGrab')
    class FakeImage:
        def save(self,path): Path(path).write_bytes(b'fake-screen')
    imagegrab.grab=lambda **_:FakeImage(); pil.ImageGrab=imagegrab
    sys.modules['PIL']=pil; sys.modules['PIL.ImageGrab']=imagegrab
    spec=importlib.util.spec_from_file_location('session_map01_v12_under_test',SESSION_PATH)
    session_mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(session_mod)
    out=Path(__file__).resolve().parent/'raw'/RUN_ID
    if out.exists() or (Path(__file__).resolve().parent/'raw'/f'{RUN_ID}-stdout.txt').exists():
        raise FileExistsError(f'preserving existing capture; choose a new --run-id: {RUN_ID}')
    inp='\n'.join([json.dumps({'op':'submit','id':'p1','steps':[{'op':'hold','keys':['w']}],'expected_sequence':0,'valid_until_ns':999999999999}),json.dumps({'op':'finish'})])+'\n'
    stdout=io.StringIO()
    old_argv,old_stdin=sys.argv,sys.stdin
    try:
        sys.argv=['session_map01_v12.py','--out',str(out),'--seed','1']
        sys.stdin=io.StringIO(inp)
        with contextlib.redirect_stdout(stdout): session_mod.main()
        (Path(__file__).resolve().parent/'raw'/f'{RUN_ID}-stdout.txt').write_text(stdout.getvalue(),encoding='utf-8')
    finally: sys.argv,sys.stdin=old_argv,old_stdin
    events=[json.loads(s) for s in (out/'events.jsonl').read_text().splitlines()]
    delivered=(out/'delivered.jsonl').read_bytes()
    owner_events=json.loads((out/'owner-events.json').read_text())
    release=[r for r in events if r.get('event')=='input_release_transition']
    owner_up=[r for r in owner_events if r.get('event')=='owner_explicit_keyup']
    assert len(release)==1, release
    assert len(owner_up)==1, owner_up
    assert (out/'events.jsonl').read_bytes()==delivered
    assert release[0]['owner_thread_keyup_receipt']['owner_sync_returned_ns']==230
    assert release[0]['release_batch_identifier']=='p1'
    assert release[0]['owner_transition_verified'] is True
    assert owner_up[0]['intent_token']=='integration-a01'
    assert owner_up[0]['server_sync_completed'] is True
    record={'schema':'session-callback-integration-a01','scope':'exact session source with fake X11, VizDoom, owner and executor; no live or physical input',
            'session_source_sha256':hashlib.sha256(SESSION_PATH.read_bytes()).hexdigest(),
            'backend_source_sha256':hashlib.sha256(BACKEND_PATH.read_bytes()).hexdigest(),
            'session_git_blob':os.popen(f'git -C {REPO} hash-object {SESSION_PATH}').read().strip(),
            'backend_git_blob':os.popen(f'git -C {REPO} hash-object {BACKEND_PATH}').read().strip(),
            'events_count':len(events),'release_event_count':len(release),'owner_keyup_count':len(owner_up),
            'events_equals_delivered':(out/'events.jsonl').read_bytes()==delivered,
            'receipt_preserved':True,'owner_record_preserved':True,'pass':True}
    dest=Path(__file__).resolve().parent/'RESULT.json'
    dest.write_text(json.dumps(record,indent=2)+'\n')
    print(json.dumps(record,indent=2))
