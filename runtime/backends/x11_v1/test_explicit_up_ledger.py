"""Ordinary source-exact X11 class construction; no Xlib/native import."""
import ast, hashlib, json, os, sys, types, unittest
from pathlib import Path

HERE=Path(__file__).resolve().parent
REPOSITORY=HERE.parents[2]
PATHS=('runtime/backends/x11_v1/backend.py','runtime/backends/x11_v1/session.py','runtime/core_v1/contract.py')
SOURCES={path:(REPOSITORY/path).read_text(encoding='utf8') for path in PATHS}
BACKEND_SOURCE=SOURCES['runtime/backends/x11_v1/backend.py']
contract=types.ModuleType('ledger_contract_scoped');sys.modules[contract.__name__]=contract
exec(compile(SOURCES['runtime/core_v1/contract.py'],'pinned_actual_contract.py','exec'),contract.__dict__)

class InertClock:
    @staticmethod
    def monotonic_ns():return 1
    @staticmethod
    def sleep(value):raise AssertionError('unplanned sleep/native path')

X=types.SimpleNamespace(KeyPress=2,KeyRelease=3,ButtonPress=4,ButtonRelease=5,Button1Mask=256,Button2Mask=512,Button3Mask=1024,Button4Mask=2048,Button5Mask=4096)
class InertXTest:
    @staticmethod
    def fake_input(display,kind,code,**kw):display.send(kind,code)
class FakeDisplay:
    def __init__(self,stubborn=False,fault=None):
        self.keys=set();self.buttons=set();self.stubborn=stubborn;self.fault=fault;self.events=[];self.attempts=0
    def send(self,kind,code):
        self.attempts+=1;self.events.append({'send_kind':kind,'code':code,'attempt':self.attempts})
        if self.fault=='send' and self.attempts==2:raise native['X11BackendError']('inert explicit UP send fault')
        state=self.keys if kind in (X.KeyPress,X.KeyRelease) else self.buttons
        if kind in (X.KeyPress,X.ButtonPress):state.add(code)
        elif not self.stubborn:state.discard(code)
    def sync(self):
        self.events.append({'sync':True})
        if self.fault=='sync' and self.attempts==2:raise native['X11BackendError']('inert explicit UP sync fault')
    def query_keymap(self):
        self.events.append({'query_keymap':True})
        if self.fault=='key_query':raise RuntimeError('inert key query fault')
        result=bytearray(32)
        for code in self.keys:result[code//8]|=1<<(code%8)
        return bytes(result)
    def query_pointer(self):
        self.events.append({'query_pointer':True})
        if self.fault=='button_query':raise RuntimeError('inert button query fault')
        masks={1:X.Button1Mask,2:X.Button2Mask,3:X.Button3Mask,4:X.Button4Mask,5:X.Button5Mask}
        return types.SimpleNamespace(mask=sum(masks.get(n,0) for n in self.buttons))

native={'__name__':'ledger_x11_scoped','Any':object,'time':InertClock,'X':X,'xtest':InertXTest,
        'OFFICE_FLOOR':contract.OFFICE_FLOOR,'WINDOW_ACTIVATE':contract.WINDOW_ACTIVATE,
        'capability_manifest':contract.capability_manifest,'validate_backend_manifest':contract.validate_backend_manifest,
        'BUTTON_MAP':{'left':1,'middle':2,'right':3,'x1':8,'x2':9},'BUTTON_MASKS':{1:256,2:512,3:1024,4:2048,5:4096},'SCROLL_BUTTON_NAMES':{4:'wheel_up',5:'wheel_down'}}
tree=ast.parse(BACKEND_SOURCE)
nodes=[ast.ImportFrom(module='__future__',names=[ast.alias(name='annotations')],level=0)]+[n for n in tree.body if isinstance(n,ast.ClassDef)]
module=ast.fix_missing_locations(ast.Module(body=nodes,type_ignores=[]))
exec(compile(module,'pinned_x11_classes.py','exec'),native)
Backend=native['X11Backend']
def forbidden(*args,**kw):raise AssertionError('constructor/native path forbidden')
Backend.__init__=forbidden
session_globals={'__name__':'ledger_session_scoped','Any':object,'admit_program':contract.admit_program,
                 'X11Backend':Backend,'X11BackendError':native['X11BackendError'],'X11ExecutionError':native['X11ExecutionError']}
stree=ast.parse(SOURCES['runtime/backends/x11_v1/session.py'])
module=ast.fix_missing_locations(ast.Module(body=[ast.ImportFrom(module='__future__',names=[ast.alias(name='annotations')],level=0)]+[n for n in stree.body if isinstance(n,ast.ClassDef)],type_ignores=[]))
exec(compile(module,'pinned_x11_session_class.py','exec'),session_globals)
Session=session_globals['X11RuntimeSession']

class ExplicitUpTests(unittest.TestCase):
    def make(self,**options):
        b=Backend.__new__(Backend);d=FakeDisplay(**options);b.d=d;b.root=d;b.held_keycodes={};b.held_buttons=set();b.held_scroll_buttons=set();b.emissions=0
        b.maps={'a':38,'SHIFT':50};b._keycode=lambda key:b.maps[key]
        b._refresh_keyboard_mapping=lambda:False;b._keyboard_mapping_snapshot=lambda:('fixed-inert-map',)
        b._activation_supported=lambda:False
        return b,Session(b)
    def dispatch(self,s,ops,name):
        p={'schema':contract.SCHEMA_PROGRAM,'program_id':name,'source':{'observation_seq':7,'binding_revision':3},
           'authority':{'lease_id':'ordinary-x11-ledger','expires_at_ns':100},'terminal':{'release_all_required':True},'ops':ops+[{'op':'release_all'}]}
        return s.dispatch(p,current_observation_seq=7,current_binding_revision=3,now_ns=1)
    def record(self,b,s,name,call):
        try:value=call()
        except Exception as e:value={'exception':type(e).__name__,'detail':str(e)}
        row={'test':self.id(),'case':name,'value':value,'held_keycodes':dict(b.held_keycodes),'held_buttons':sorted(b.held_buttons),
             'api_keys':sorted(b.d.keys),'api_buttons':sorted(b.d.buttons),'events':list(b.d.events),'recovery_required':s.recovery_required,'emissions':b.emissions}
        print(json.dumps(row,sort_keys=True));return value
    def family(self,label,ops,*,key=True):
        for stubborn in (False,True):
            with self.subTest(label=label,stubborn=stubborn):
                b,s=self.make(stubborn=stubborn);name=label+('_stubborn' if stubborn else '_healthy')
                reply=self.record(b,s,name,lambda:self.dispatch(s,ops,name))
                self.assertEqual(reply['admission'],'accepted')
                self.assertEqual(reply['status'],'release_unverified' if stubborn else 'completed')
                self.assertEqual(b.held_keycodes,{'a':38} if stubborn and key else {})
                self.assertEqual(b.held_buttons,{'left'} if stubborn and not key else set())
                self.assertEqual(s.recovery_required,stubborn)
                before=b.emissions
                follow=self.record(b,s,name+'_followup',lambda:self.dispatch(s,[{'op':'key_state','key':'a','down':True}],name+'_followup'))
                if stubborn:
                    self.assertEqual(follow['error'],'INPUT_RECOVERY_REQUIRED');self.assertEqual(b.emissions,before)
                    b.d.stubborn=False
                    recover=self.record(b,s,name+'_recover',s.recover_input)
                    self.assertEqual(recover['status'],'input_recovered');self.assertFalse(b.d.keys or b.d.buttons)
                else:self.assertEqual(follow['status'],'completed')
    def test_key_pair(self):self.family('key_pair',[{'op':'key_state','key':'a','down':True},{'op':'key_state','key':'a','down':False}])
    def test_key_chord(self):self.family('key_chord',[{'op':'key_chord','keys':['a']}])
    def test_ascii_text(self):self.family('ascii_text',[{'op':'text','text':'a'}])
    def test_button_pair(self):self.family('button_pair',[{'op':'pointer_button','button':'left','down':True},{'op':'pointer_button','button':'left','down':False}],key=False)
    def test_query_faults_preserve_explicit_up_obligations(self):
        for fault in ('key_query','button_query'):
            with self.subTest(fault=fault):
                b,s=self.make(stubborn=True,fault=fault);ops=([{'op':'key_state','key':'a','down':True},{'op':'key_state','key':'a','down':False}] if fault=='key_query' else [{'op':'pointer_button','button':'left','down':True},{'op':'pointer_button','button':'left','down':False}])
                reply=self.record(b,s,fault,lambda:self.dispatch(s,ops,fault));self.assertEqual(reply['status'],'execution_failed');self.assertTrue(s.recovery_required)
                self.assertEqual(b.held_keycodes,{'a':38} if fault=='key_query' else {});self.assertEqual(b.held_buttons,{'left'} if fault=='button_query' else set())
                b.d.fault=None;b.d.stubborn=False
                recover=self.record(b,s,fault+'_recover',s.recover_input);self.assertEqual(recover['status'],'input_recovered');self.assertFalse(b.d.keys or b.d.buttons)
    def test_send_sync_fault_controls(self):
        for fault in ('send','sync'):
            with self.subTest(fault=fault):
                b,s=self.make(stubborn=True,fault=fault)
                reply=self.record(b,s,fault,lambda:self.dispatch(s,[{'op':'key_state','key':'a','down':True},{'op':'key_state','key':'a','down':False}],fault))
                self.assertEqual(reply['status'],'execution_failed');self.assertTrue(s.recovery_required);self.assertEqual(b.held_keycodes,{'a':38})
                b.d.fault=None;b.d.stubborn=False
                recover=self.record(b,s,fault+'_recover',s.recover_input);self.assertEqual(recover['status'],'input_recovered');self.assertFalse(b.d.keys)
    def test_untracked_up_never_claims_ownership(self):
        b,s=self.make(stubborn=True);b.d.keys={38};b.d.buttons={1}
        reply=self.record(b,s,'untracked',lambda:self.dispatch(s,[{'op':'key_state','key':'a','down':False},{'op':'pointer_button','button':'left','down':False}],'untracked'))
        self.assertEqual(reply['error'],'INVALID_PROGRAM');self.assertEqual(b.emissions,0);self.assertFalse(s.recovery_required)
        # The current core refuses an unpaired UP program before backend entry.
        # Direct backend UP is a separate ownership control, not admitted input.
        b.key_state('a',False);b.pointer_button('left',False)
        release=self.record(b,s,'untracked_direct',b.release_all)
        self.assertEqual(b.held_keycodes,{});self.assertEqual(b.held_buttons,set());self.assertEqual(b.d.keys,{38});self.assertEqual(b.d.buttons,{1})
        self.assertFalse(release['verified']);self.assertEqual(release['keys_down'],[]);self.assertEqual(release['buttons_down'],['left'])
    def test_remapping_after_up_keeps_original_physical_code(self):
        b,s=self.make(stubborn=True)
        b._wait_update=lambda timeout:b.maps.update(a=39)
        reply=self.record(b,s,'remap_after_up',lambda:self.dispatch(s,[{'op':'key_state','key':'a','down':True},{'op':'key_state','key':'a','down':False},{'op':'wait_update','timeout_ms':1}],'remap_after_up'))
        self.assertEqual(reply['status'],'release_unverified');self.assertEqual(b.held_keycodes,{'a':38})
        b.d.stubborn=False
        recover=self.record(b,s,'remap_recover',s.recover_input);self.assertEqual(recover['status'],'input_recovered');self.assertFalse(b.d.keys)
        self.assertEqual([e['code'] for e in b.d.events if 'send_kind' in e],[38,38,38,38])

if __name__=='__main__':unittest.main(verbosity=2)
