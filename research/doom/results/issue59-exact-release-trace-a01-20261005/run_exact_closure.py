import importlib.util, json, sys, threading, time, types
from pathlib import Path
ROOT=Path(r'C:\Users\user\Documents\Codex\2026-10-03\new-chat\work\issue59-v15-scorer-20261005')
DOOM=ROOT/'research'/'doom'; LIVE=ROOT/'research'/'live_control'
sys.path[:0]=[str(DOOM),str(LIVE)]
EVENTS=[]; HELD=set()
def mark(event,**kw): EVENTS.append({'t_ns':time.perf_counter_ns(),'event':event,**kw})
class X:
    KeyPress='KeyPress'; KeyRelease='KeyRelease'; ButtonRelease='ButtonRelease'; ButtonPress='ButtonPress'
    AnyPropertyType=0; IsViewable=2; Button1Mask=1
class XK:
    @staticmethod
    def string_to_keysym(s): return s
class FakeRoot:
    id=1
    def query_pointer(self): return types.SimpleNamespace(mask=0,root_x=0,root_y=0)
class FakeScreen:
    root=FakeRoot()
class FakeDisplay:
    def __init__(self,name): mark('display_open',name=name)
    def keysym_to_keycode(self,s): return {'a':38,'space':65}.get(s,0)
    def get_input_focus(self): return types.SimpleNamespace(focus=types.SimpleNamespace(id=42))
    def screen(self): return FakeScreen()
    def query_keymap(self):
        mark('query_keymap',held=sorted(HELD)); bits=bytearray(32)
        for code in HELD: bits[code//8] |= 1 << (code%8)
        return bytes(bits)
    def sync(self): mark('xsync')
    def close(self): mark('display_close')
class BadWindow(Exception): pass
class BadDrawable(Exception): pass
xlib=types.ModuleType('Xlib'); xlib.X=X; xlib.XK=XK; xlib.display=types.SimpleNamespace(Display=FakeDisplay); xlib.error=types.SimpleNamespace(BadWindow=BadWindow,BadDrawable=BadDrawable)
extmod=types.ModuleType('Xlib.ext'); xtest=types.ModuleType('Xlib.ext.xtest')
def fake_input(display,event,detail,**kwargs):
    if event=='KeyPress': HELD.add(detail)
    elif event=='KeyRelease': HELD.discard(detail)
    mark('xtest_fake_input',input_event=event,detail=detail)
xtest.fake_input=fake_input
sys.modules.update({'Xlib':xlib,'Xlib.ext':extmod,'Xlib.ext.xtest':xtest})
extmod.xtest=xtest
ex=types.ModuleType('executor_v3')
class Cancelled(Exception): pass
class DecisionRequired(Exception): pass
ex.Cancelled=Cancelled; ex.DecisionRequired=DecisionRequired; sys.modules['executor_v3']=ex
# v3 imports this only as its default constructor. V4 supplies actual InputOwner v12 explicitly.
v10=types.ModuleType('input_owner_v10'); v10.InputOwner=object; sys.modules['input_owner_v10']=v10
import input_transition_owner_v4 as transition_v4
class PlaceholderOwner:
    owner_id='placeholder'
    def close(self): pass
class Base:
    inject_interkey_query=False
    def __init__(self,session,out,emit,signal_readers):
        self.owner=PlaceholderOwner(); self.held=set(); self.emit=emit; self.lease=None; self._input_event_context=None
    def execute(self,step,cancel,identifier,index):
        self._input_event_context=(identifier,index)
        for key in step['keys']: self.raw(key,True)
        for i,key in enumerate(step['keys']):
            if self.inject_interkey_query and i==1: self.owner.call('input_state')
            self.raw(key,False)
        self._input_event_context=None
    def release_all(self): return {'verified':True}
base=types.ModuleType('doom_typed_release_backend_v2'); base.Backend=Base; base.suite=object(); sys.modules['doom_typed_release_backend_v2']=base
path=DOOM/'doom_owner_thread_release_batch_backend_v1.py'; spec=importlib.util.spec_from_file_location('exact_release_batch_backend',path); module=importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
original_call=transition_v4.InputOwner.call
def tagged_call(self,operation,lease=None,key=None):
    mark('owner_rpc_start',op=operation,key=key)
    result=original_call(self,operation,lease,key)
    mark('owner_rpc_return',op=operation,key=key)
    return result
transition_v4.InputOwner.call=tagged_call

def run(inject):
    EVENTS.clear(); HELD.clear(); emitted=[]
    backend=module.Backend(types.SimpleNamespace(name='fake-display'),None,emitted.append,{})
    backend.lease=types.SimpleNamespace(intent_token='exact-A01',deadline=time.perf_counter_ns()+30_000_000_000,cancel=threading.Event(),expected_focus=42,focus_invalid=False,check=lambda:None)
    backend.inject_interkey_query=inject
    begin=len(EVENTS); backend.execute({'keys':['a','space']},None,'program-exact-A01',3); end=len(EVENTS)
    rows=[r for r in emitted if r.get('event')=='input_release_transition']
    # Close only after taking the bounded action interval: close intentionally exercises owner cleanup/query_keymap.
    backend.owner.close()
    trial=EVENTS[begin:end]
    ups=[i for i,e in enumerate(trial) if e['event']=='xtest_fake_input' and e.get('input_event')=='KeyRelease' and e.get('detail') in (38,65)]
    keyups=[(i,e) for i,e in enumerate(trial) if e['event']=='xtest_fake_input' and e.get('input_event')=='KeyRelease' and e.get('detail') in (38,65)]
    qkeys=[i for i,e in enumerate(trial) if e['event']=='query_keymap']
    samples=[i for i,e in enumerate(trial) if e['event']=='owner_rpc_start' and e.get('op')=='input_state']
    checks={
      'keyrelease_order':['KeyRelease','KeyRelease']==[e['input_event'] for _,e in keyups],
      'keycodes_order':[38,65]==[e['detail'] for _,e in keyups],
      'no_query_keymap_between_explicit_releases':not any(keyups[0][0]<q<keyups[1][0] for q in qkeys) if len(keyups)==2 else False,
      'one_terminal_input_state':len(samples)==1 and samples[-1]>keyups[-1][0],
      'injected_interkey_sample_detected':(not inject) or (len(samples)==2 and samples[0]<keyups[1][0]),
      'perkey_receipts':['a','space']==[r.get('owner_thread_keyup_receipt',{}).get('key') for r in rows],
      'receipt_physical_authority_false':all(r.get('owner_thread_keyup_receipt',{}).get('physical_verification_authoritative') is False for r in rows),
      'published_physical_authority_false':all(r.get('physical_verification_authoritative') is False for r in rows),
      'terminal_empty_owner_state':all(r.get('owned_keycodes_after_batch')==[] for r in rows),
    }
    return {'injected_interkey_query':inject,'checks':checks,'all':all(checks.values()),'trial_events':trial,'rows':rows,'post_trial_cleanup_events':EVENTS[end:]}
baseline=run(False); negative=run(True)
report={'schema':'issue59-exact-closure-a01-v1','source_head':'8a9e76d56be60fdaf96fa87ccbc9c7defd29e20d','scope':'actual V15 batch wrapper and actual v4->v3->v12 owner adapter/input-owner source; fake Xlib Display + fake outer executor; no live X11, game, or input','baseline':baseline,'negative_control':negative,'decision':'baseline must pass; negative control must fail; query_keymap observed during owner.close cleanup is outside the explicit two-key release interval'}
print(json.dumps(report,sort_keys=True,indent=2))
if not baseline['all'] or negative['all']: raise SystemExit(1)




