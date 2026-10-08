import json, sys, types, threading, time
from pathlib import Path
sys.dont_write_bytecode = True
sys.path.insert(0, str((Path(__file__).parent / "frozen_source")))

class FakeDisplay:
    def __init__(self, mode):
        self.mode=mode; self.failed=False; self.armed=False; self.down=set(); self.trace=[]
        self.root=types.SimpleNamespace(query_pointer=lambda: types.SimpleNamespace(mask=0,root_x=0,root_y=0))
    def get_input_focus(self): return types.SimpleNamespace(focus=41)
    def keysym_to_keycode(self, key): return {ord('W'):38,ord('A'):39}.get(key,0)
    def query_keymap(self):
        b=bytearray(32)
        for c in self.down: b[c//8]|=1<<(c%8)
        self.trace.append(('query',tuple(sorted(self.down))))
        return bytes(b)
    def sync(self):
        self.trace.append(('sync',))
        if self.mode=='sync' and self.armed and not self.failed:
            self.failed=True
            raise OSError('synthetic sync transport failure')
    def screen(self): return types.SimpleNamespace(root=self.root)
    def close(self): pass

results=[]
for mode in ('send','sync'):
    d=FakeDisplay(mode)
    X=types.SimpleNamespace(KeyPress=2,KeyRelease=3,ButtonRelease=5,ButtonPress=4,Button1Mask=256,AnyPropertyType=0)
    xlib=types.ModuleType('Xlib'); xlib.X=X
    xk=types.ModuleType('Xlib.XK'); xk.string_to_keysym=lambda k:ord(k)
    display=types.ModuleType('Xlib.display'); display.Display=lambda _name:d
    error=types.ModuleType('Xlib.error'); error.BadWindow=type('BadWindow',(Exception,),{}); error.BadDrawable=type('BadDrawable',(Exception,),{})
    ext=types.ModuleType('Xlib.ext'); xtest=types.ModuleType('Xlib.ext.xtest')
    def fake_input(_d,event,code):
        d.trace.append(('event',event,code))
        if event==X.KeyRelease and mode=='send' and d.armed and not d.failed:
            d.failed=True
            raise OSError('synthetic XTest send failure')
        if event==X.KeyPress: d.down.add(code)
        elif event==X.KeyRelease: d.down.discard(code)
    xtest.fake_input=fake_input; ext.xtest=xtest
    xlib.XK=xk; xlib.display=display; xlib.error=error; xlib.ext=ext
    sys.modules.update({'Xlib':xlib,'Xlib.X':types.ModuleType('Xlib.X'),'Xlib.XK':xk,'Xlib.display':display,'Xlib.error':error,'Xlib.ext':ext,'Xlib.ext.xtest':xtest})
    for name in ('input_owner_v12','executor_v3','lease'): sys.modules.pop(name,None)
    from input_owner_v12 import InputOwner
    owner=InputOwner(':fake')
    class Lease:
        intent_token='test'; deadline=time.perf_counter_ns()+10_000_000_000; expected_focus=41; focus_invalid=False
        def __init__(self): self.cancel=threading.Event()
        def check(self): pass
    lease=Lease()
    owner.call('down',lease,'W'); owner.call('down',lease,'A')
    d.trace.clear(); d.armed=True
    try: owner.call('up_batch',lease,['A','W']); outcome='unexpected-return'
    except OSError as exc: outcome=type(exc).__name__+': '+str(exc)
    initial=[e for e in d.trace if e[0]=='event' and e[1]==X.KeyRelease]
    records_before_cleanup=[r for r in owner.records if r.get('event')=='owner_explicit_keyup']
    try: cleanup=owner.call('release',lease)
    except Exception as exc: cleanup={'error':type(exc).__name__+': '+str(exc)}
    results.append({'mode':mode,'up_batch_outcome':outcome,'initial_keyrelease_codes':[e[2] for e in initial],'explicit_receipts_before_cleanup':len(records_before_cleanup),'cleanup_verified':cleanup.get('verified') if isinstance(cleanup,dict) else None,'owner_release_records':sum(r.get('event')=='owner_release' for r in owner.records),'remaining_keys':sorted(d.down),'owner_failed':owner.error is not None})
    try: owner.close()
    except Exception: pass
    for name in ('input_owner_v12','executor_v3','lease'): sys.modules.pop(name,None)
print(json.dumps(results,sort_keys=True))
