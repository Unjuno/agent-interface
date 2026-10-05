"""Check archived owner API against the V39 release-batch owner call, with fake X only."""
from __future__ import annotations
import argparse, hashlib, json, sys, types
from pathlib import Path

def main():
    parser=argparse.ArgumentParser(); parser.add_argument('source',type=Path); parser.add_argument('output',type=Path)
    args=parser.parse_args(); source=args.source.resolve(); args.output.parent.mkdir(parents=True,exist_ok=True)
    forbidden=[]
    def refuse(*a,**kw):
        forbidden.append({'call':'XTest.fake_input'}); raise AssertionError('native XTest forbidden')
    class FakeRoot:
        def query_pointer(self): return types.SimpleNamespace(mask=0)
    class FakeDisplay:
        def __init__(self,*a,**kw): self.root=FakeRoot(); self.closed=False
        def screen(self): return types.SimpleNamespace(root=self.root)
        def query_keymap(self): return bytes(32)
        def sync(self): return None
        def close(self): self.closed=True
    made=[]
    def open_display(*a,**kw):
        value=FakeDisplay(); made.append(value); return value
    x=types.SimpleNamespace(KeyPress=2,KeyRelease=3,ButtonPress=4,ButtonRelease=5,Button1Mask=256,AnyPropertyType=0,IsViewable=2)
    xk=types.SimpleNamespace(string_to_keysym=lambda s: 1)
    error=types.SimpleNamespace(BadWindow=type('BadWindow',(Exception,),{}),BadDrawable=type('BadDrawable',(Exception,),{}))
    display=types.ModuleType('Xlib.display'); display.Display=open_display
    ext=types.ModuleType('Xlib.ext'); xtest=types.ModuleType('Xlib.ext.xtest'); xtest.fake_input=refuse; ext.xtest=xtest
    xlib=types.ModuleType('Xlib'); xlib.X=x; xlib.XK=xk; xlib.error=error; xlib.display=display
    sys.modules.update({'Xlib':xlib,'Xlib.display':display,'Xlib.ext':ext,'Xlib.ext.xtest':xtest})
    research=source/'research'; archive=research/'doom/map01_attack_onset_phase_allocation_02_v1/dependencies/v12'
    sys.path[:0]=[str(archive),str(research/'live_control')]
    backend_path=research/'doom/doom_owner_thread_release_batch_backend_v1.py'
    archived_path=archive/'input_owner_v12.py'; current_path=research/'live_control/input_owner_v12.py'
    backend_text=backend_path.read_text(); archived_text=archived_path.read_text(); current_text=current_path.read_text()
    required='"up_batch", self.lease, [item["key"] for item in pending]' in backend_text
    current_support='release_keys_batch(lease, keys)' in current_text and "op == 'up_batch'" in current_text
    import input_owner_v12 as archived_module
    owner=archived_module.InputOwner(':fake-inert:')
    outcome={'required_operation':'up_batch','backend_requires_up_batch':required,
             'current_owner_declares_up_batch':current_support,
             'archived_owner_file':str(Path(archived_module.__file__).resolve().relative_to(source)),
             'archived_source_sha256':hashlib.sha256(archived_path.read_bytes()).hexdigest(),
             'exception_type':None,'exception_message':None,'returned_type':None}
    try:
        returned=owner.call('up_batch',object(),['left','right'])
        outcome['returned_type']=type(returned).__name__
    except BaseException as exc:
        outcome['exception_type']=type(exc).__name__; outcome['exception_message']=str(exc)
    finally:
        owner.close()
    outcome.update({'owner_closed':owner.closed,'owner_thread_alive':owner.thread.is_alive(),
                    'display_closed':bool(made and made[0].closed),'forbidden_calls':forbidden})
    expected=(outcome['backend_requires_up_batch'] and outcome['current_owner_declares_up_batch']
              and outcome['exception_type']=='ValueError' and outcome['exception_message']=='unknown input operation'
              and outcome['owner_closed'] and not outcome['owner_thread_alive']
              and outcome['display_closed'] and not forbidden)
    outcome['status']='FAIL_COMPATIBILITY' if expected else ('PASS_COMPATIBILITY' if outcome['returned_type']=='list' and not forbidden else 'INCONCLUSIVE')
    args.output.write_text(json.dumps(outcome,indent=2,sort_keys=True)+'\n')
    print(json.dumps(outcome,sort_keys=True))
    return 0 if expected or outcome['status']=='PASS_COMPATIBILITY' else 1
if __name__=='__main__': raise SystemExit(main())
