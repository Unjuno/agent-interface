"""Ordinary source-exact class regression; entirely inert endpoint, clock1."""
import ast, hashlib, json, sys, types, unittest
from pathlib import Path
HERE=Path(__file__).resolve().parent
SOURCE=Path(sys.argv.pop(1)).resolve() if len(sys.argv)>1 and Path(sys.argv[1]).is_dir() else HERE
paths={n:SOURCE/n for n in ('backend.py','session.py','contract.py')}
if not paths['contract.py'].exists():paths['contract.py']=HERE.parents[1]/'core_v1/contract.py'
sources={n:p.read_text(encoding='utf8') for n,p in paths.items()}
contract=types.ModuleType('wheel_contract');sys.modules[contract.__name__]=contract
exec(compile(sources['contract.py'],'actual_contract.py','exec'),contract.__dict__)
X=types.SimpleNamespace(KeyPress=2,KeyRelease=3,ButtonPress=4,ButtonRelease=5,
    Button1Mask=256,Button2Mask=512,Button3Mask=1024,Button4Mask=2048,Button5Mask=4096)
class Clock:
    @staticmethod
    def monotonic_ns():return 1
    @staticmethod
    def sleep(_):raise RuntimeError('sleep forbidden')
class Endpoint:
    def __init__(self,fault=None,foreign=()):
        self.fault=fault;self.buttons=set(foreign);self.keys=set();self.events=[];self.queries=0
    def screen(self):return types.SimpleNamespace(root=self)
    def has_extension(self,name):return name=='XTEST'
    def send(self,kind,code):
        self.events.append({'kind':kind,'code':code})
        fault=self.fault
        if (fault=='release_pre' and kind==X.ButtonRelease) or (fault=='press_pre' and kind==X.ButtonPress):raise RuntimeError(fault)
        state=self.keys if kind in (X.KeyPress,X.KeyRelease) else self.buttons
        if kind in (X.KeyPress,X.ButtonPress):state.add(code)
        elif fault!='stubborn':state.discard(code)
        if (fault=='release_post' and kind==X.ButtonRelease) or (fault=='press_post' and kind==X.ButtonPress):raise RuntimeError(fault)
    def sync(self):
        self.events.append({'sync':True})
        if self.fault=='sync':raise RuntimeError('sync')
    def query_keymap(self):
        self.events.append({'keys_read':True})
        if self.fault=='keys_read':raise RuntimeError('keys_read')
        b=bytearray(32)
        for c in self.keys:b[c//8]|=1<<(c%8)
        return bytes(b)
    def query_pointer(self):
        self.queries+=1;self.events.append({'buttons_read':self.queries})
        if self.fault=='buttons_read' and self.queries>=2:raise RuntimeError('buttons_read')
        return types.SimpleNamespace(mask=sum(1<<(7+n) for n in self.buttons if 1<=n<=5))
current_endpoint=None
def display_factory(_):return current_endpoint
native={'__name__':'wheel_classes','Any':object,'X':X,'time':Clock,
    'display':types.SimpleNamespace(Display=display_factory),
    'xtest':types.SimpleNamespace(fake_input=lambda d,k,c,**kw:d.send(k,c)),
    'OFFICE_FLOOR':contract.OFFICE_FLOOR,'WINDOW_ACTIVATE':contract.WINDOW_ACTIVATE,
    'capability_manifest':contract.capability_manifest,'validate_backend_manifest':contract.validate_backend_manifest}
def class_module(text,constants=False):
    nodes=[ast.ImportFrom(module='__future__',names=[ast.alias(name='annotations')],level=0)]
    for n in ast.parse(text).body:
        if isinstance(n,ast.ClassDef) or (constants and isinstance(n,ast.Assign)):nodes.append(n)
    return ast.fix_missing_locations(ast.Module(body=nodes,type_ignores=[]))
exec(compile(class_module(sources['backend.py'],True),'actual_backend_classes.py','exec'),native)
Backend=native['X11Backend']
sg={'__name__':'wheel_session','Any':object,'admit_program':contract.admit_program,
    'X11Backend':Backend,'X11BackendError':native['X11BackendError'],'X11ExecutionError':native['X11ExecutionError']}
exec(compile(class_module(sources['session.py']),'actual_session_class.py','exec'),sg)
Session=sg['X11RuntimeSession']
class MixedEndpoint(Endpoint):
    def sync(self):
        self.events.append({'sync':True})
        if self.fault=='sync' and any(e.get('kind')==X.ButtonPress for e in self.events):raise RuntimeError('sync')
class WheelTests(unittest.TestCase):
    def make(self,endpoint_class=Endpoint,**kw):
        global current_endpoint
        current_endpoint=endpoint_class(**kw);b=Backend('inert',{})
        b._refresh_keyboard_mapping=lambda:False;b._keyboard_mapping_snapshot=lambda:('fixed',)
        b._activation_supported=lambda:False
        return b,Session(b)
    def dispatch(self,s,dy=0):
        ops=([{'op':'scroll','dx':0,'dy':dy}] if dy else [])+[{'op':'release_all'}]
        p={'schema':contract.SCHEMA_PROGRAM,'program_id':'ordinary-wheel',
           'source':{'observation_seq':7,'binding_revision':3},
           'authority':{'lease_id':'ordinary-wheel','expires_at_ns':100},
           'terminal':{'release_all_required':True},'ops':ops}
        return s.dispatch(p,current_observation_seq=7,current_binding_revision=3)
    def row(self,b,s,name,value):
        print(json.dumps({'case':name,'value':value,'buttons':sorted(b.d.buttons),
            'owned':sorted(getattr(b,'held_scroll_buttons',set())), 'keys':sorted(b.d.keys),
            'events':list(b.d.events),'emissions':b.emissions,'recovery_required':s.recovery_required},sort_keys=True))
    def fault_case(self,fault,requires):
        for dy,code in ((-1,4),(1,5)):
            with self.subTest(fault=fault,code=code):
                b,s=self.make(fault=fault);reply=self.dispatch(s,dy);self.row(b,s,fault+str(code),reply)
                self.assertEqual(reply['status'],'release_unverified' if fault=='stubborn' else 'execution_failed')
                self.assertEqual(s.recovery_required,requires)
                if requires:
                    self.assertEqual(b.held_scroll_buttons,{code})
                    events=list(b.d.events);follow=self.dispatch(s,dy);self.row(b,s,fault+str(code)+'_follow',follow)
                    self.assertEqual(follow['error'],'INPUT_RECOVERY_REQUIRED');self.assertEqual(b.d.events,events)
                    b.d.fault=None;recovered=s.recover_input();self.row(b,s,fault+str(code)+'_recover',recovered)
                    self.assertEqual(recovered['status'],'input_recovered');self.assertFalse(recovered['replay_allowed'])
                    self.assertFalse(b.d.buttons);self.assertFalse(b.held_scroll_buttons)
                    self.assertEqual(sum(e.get('kind')==X.ButtonPress for e in b.d.events),1)
                else:self.assertFalse(b.d.buttons);self.assertFalse(b.held_scroll_buttons)
    def test_healthy(self):
        for dy in (-2,2):
            b,s=self.make();r=self.dispatch(s,dy);self.row(b,s,'healthy'+str(dy),r)
            self.assertEqual(r['status'],'completed')
            self.assertEqual(b.emissions,len([e for e in b.d.events if 'kind' in e]))
            self.assertFalse(b.d.buttons);self.assertFalse(b.held_scroll_buttons)
    def test_failed_release_before_effect(self):self.fault_case('release_pre',True)
    def test_failed_release_after_effect(self):self.fault_case('release_post',True)
    def test_failed_press_before_effect(self):self.fault_case('press_pre',False)
    def test_failed_press_after_effect(self):self.fault_case('press_post',False)
    def test_failed_sync(self):self.fault_case('sync',True)
    def test_failed_key_readback(self):self.fault_case('keys_read',True)
    def test_failed_button_readback(self):self.fault_case('buttons_read',True)
    def test_stubborn_release(self):self.fault_case('stubborn',True)
    def test_foreign_same_wheel_is_not_pressed_or_released(self):
        for dy,code in ((-1,4),(1,5)):
            b,s=self.make(foreign=(code,));r=self.dispatch(s,dy);self.row(b,s,'foreign'+str(code),r)
            self.assertEqual(r['status'],'execution_failed');self.assertTrue(s.recovery_required)
            self.assertFalse([e for e in b.d.events if 'kind' in e]);self.assertEqual(b.d.buttons,{code})
            self.assertFalse(b.held_scroll_buttons)
            r=s.recover_input();self.row(b,s,'foreign_recover'+str(code),r)
            self.assertEqual(r['status'],'recovery_failed');self.assertEqual(b.d.buttons,{code})
            self.assertFalse([e for e in b.d.events if 'kind' in e])
    def test_foreign_other_wheel_is_not_released(self):
        b,s=self.make(foreign=(5,));r=self.dispatch(s,-1);self.row(b,s,'foreign_other',r)
        self.assertEqual(r['status'],'release_unverified');self.assertEqual(b.d.buttons,{5})
        self.assertTrue(s.recovery_required);self.assertFalse(b.held_scroll_buttons)
        self.assertFalse([e for e in b.d.events if e.get('kind')==X.ButtonRelease and e['code']==5])
    def test_release_retires_only_after_both_reads(self):
        b,s=self.make(fault='keys_read');b.held_scroll_buttons={4};b.d.buttons={4}
        with self.assertRaises(RuntimeError):b.release_all()
        self.row(b,s,'direct_key_read_fault',{})
        self.assertEqual(b.held_scroll_buttons,{4})
        b.d.fault=None;r=b.release_all();self.row(b,s,'direct_recovered',r)
        self.assertTrue(r['verified']);self.assertFalse(b.held_scroll_buttons)
    def test_mixed_key_up_and_wheel_recover_without_replay(self):
        # A previously-owned key must survive an uncertain explicit UP even
        # when a later wheel obligation also needs recovery.
        for fault in (None,'release_pre','release_post','press_post','sync','keys_read','buttons_read','stubborn'):
            for dy,code in ((-1,4),(1,5)):
                with self.subTest(fault=fault,code=code):
                    b,s=self.make(endpoint_class=MixedEndpoint,fault=fault)
                    b._keycode=lambda key:38
                    case='mixed_'+str(fault)+'_'+str(code)
                    p={'schema':contract.SCHEMA_PROGRAM,'program_id':case,
                       'source':{'observation_seq':7,'binding_revision':3},
                       'authority':{'lease_id':'ordinary-mixed','expires_at_ns':100},
                       'terminal':{'release_all_required':True},
                       'ops':[{'op':'key_state','key':'a','down':True},
                              {'op':'key_state','key':'a','down':False},
                              {'op':'scroll','dx':0,'dy':dy},{'op':'release_all'}]}
                    def record(stage,reply):
                        print(json.dumps({'mixed_case':case,'stage':stage,'fault':fault,'dy':dy,
                            'reply':reply,'fixture_keys':sorted(b.d.keys),'fixture_buttons':sorted(b.d.buttons),
                            'held_keycodes':dict(b.held_keycodes),'held_scroll_buttons':sorted(b.held_scroll_buttons),
                            'events':list(b.d.events),'emissions':b.emissions,'recovery_required':s.recovery_required},sort_keys=True))
                    def dispatch():return s.dispatch(p,current_observation_seq=7,current_binding_revision=3,now_ns=1)
                    reply=dispatch();record('dispatch',reply)
                    self.assertEqual(reply['admission'],'accepted')
                    self.assertEqual(reply['status'],'completed' if fault is None else ('release_unverified' if fault=='stubborn' else 'execution_failed'))
                    needs=fault not in (None,'press_post')
                    self.assertEqual(s.recovery_required,needs)
                    if needs:
                        self.assertEqual(b.held_keycodes,{'a':38});self.assertEqual(b.held_scroll_buttons,{code})
                        before=list(b.d.events);follow=dispatch();record('quarantined_followup',follow)
                        self.assertEqual(follow['error'],'INPUT_RECOVERY_REQUIRED');self.assertEqual(b.d.events,before)
                        presses=[e for e in before if e.get('kind') in (X.KeyPress,X.ButtonPress)]
                        b.d.fault=None;recovered=s.recover_input();record('recover',recovered)
                        self.assertEqual(recovered['status'],'input_recovered');self.assertFalse(recovered['replay_allowed'])
                        self.assertEqual([e for e in b.d.events if e.get('kind') in (X.KeyPress,X.ButtonPress)],presses)
                    else:
                        before=list(b.d.events);control=s.recover_input();record('recovery_not_required',control)
                        self.assertEqual(control['error'],'INPUT_RECOVERY_NOT_REQUIRED');self.assertEqual(b.d.events,before)
                    self.assertFalse(b.d.keys or b.d.buttons);self.assertFalse(b.held_keycodes or b.held_buttons or b.held_scroll_buttons)
                    self.assertFalse(s.recovery_required)
                    b.d.fault=None;fresh=dispatch();record('new_explicit_dispatch',fresh)
                    self.assertEqual(fresh['status'],'completed');self.assertFalse(b.d.keys or b.d.buttons)
                    self.assertFalse(b.held_keycodes or b.held_buttons or b.held_scroll_buttons or s.recovery_required)

print(json.dumps({'source_pins':{n:hashlib.sha256(t.encode()).hexdigest() for n,t in sources.items()},
    'clock_ns':1,'expires_ns':100,'scope':'ordinary inert source-class regression; native/backend module import0'}))
if __name__=='__main__':unittest.main(verbosity=2)
