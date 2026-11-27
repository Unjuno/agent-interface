"""One-shot real V12 owner close-path check on isolated Xvfb."""
import argparse, hashlib, json, subprocess, time, select
from pathlib import Path
HERE=Path(__file__).resolve().parent

def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
class Lease:
    def __init__(self, focus):
        import threading
        self.deadline=time.perf_counter_ns()+20_000_000_000
        self.expected_focus=focus
        self.intent_token='v39-owner-close-a08'
        self.cancel=threading.Event()
        self.focus_invalid=False
    def check(self):
        if self.cancel.is_set(): raise RuntimeError('cancelled')
        if time.perf_counter_ns()>=self.deadline: raise RuntimeError('expired')
    def record_interruption(self,row): self.interruption=row

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--out',type=Path,required=True);ap.add_argument('--display',default=':130');a=ap.parse_args()
    if a.out.exists(): raise SystemExit('output exists; refusing to overwrite first outcome')
    a.out.mkdir(parents=True)
    raw={'schema':'v39-owner-close-xvfb-raw-a08-v1','status':'STOP','errors':[],'scope':'one V12 owner key held then closed on isolated Xvfb; no game/model/physical input','owner_records':[],'client_events':[],'owner_queries':[],'cleanup':{}}
    xvfb=observer=owner=None; original_query=None
    try:
        freeze=json.loads((HERE.parent/'FREEZE.json').read_text())
        for name,digest in freeze['source_sha256'].items():
            if sha(HERE/name)!=digest: raise ValueError('frozen source SHA mismatch: '+name)
        from Xlib import X,Xatom,XK,display
        original_query=display.Display.query_keymap
        owner_id=[None]
        def traced(d):
            start=time.perf_counter_ns();bitmap=original_query(d);end=time.perf_counter_ns()
            raw['owner_queries'].append({'role':'owner' if id(d)==owner_id[0] else 'observer_or_other','started_ns':start,'returned_ns':end})
            return bitmap
        display.Display.query_keymap=traced
        xvfb=subprocess.Popen(['Xvfb',a.display,'-screen','0','640x480x24','-nolisten','tcp','-noreset','-ac'],stdin=subprocess.DEVNULL,stdout=subprocess.DEVNULL,stderr=subprocess.PIPE)
        raw['xvfb_pid']=xvfb.pid
        deadline=time.monotonic()+5
        while time.monotonic()<deadline:
            if xvfb.poll() is not None: raise RuntimeError('Xvfb exited: '+xvfb.stderr.read().decode('utf-8','replace'))
            try: observer=display.Display(a.display);break
            except Exception: time.sleep(.05)
        if observer is None: raise TimeoutError('Xvfb observer connect timed out')
        root=observer.screen().root
        win=root.create_window(20,20,320,200,0,observer.screen().root_depth,X.InputOutput,X.CopyFromParent,event_mask=X.KeyPressMask|X.KeyReleaseMask)
        win.map();active=observer.intern_atom('_NET_ACTIVE_WINDOW');root.change_property(active,Xatom.WINDOW,32,[win.id]);observer.sync()
        observer.set_input_focus(win,X.RevertToParent,X.CurrentTime);observer.sync()
        for _ in range(100):
            f=observer.get_input_focus().focus
            if getattr(f,'id',f)==win.id: break
            time.sleep(.01)
        else: raise RuntimeError('client focus not established')
        while observer.pending_events(): observer.next_event()
        keycode=int(observer.keysym_to_keycode(XK.string_to_keysym('a')))
        if not keycode: raise RuntimeError('a keycode unavailable')
        raw.update({'client_window':int(win.id),'keycode':keycode,'display':a.display})
        import sys,types
        ex=types.ModuleType('executor_v3');ex.Cancelled=type('Cancelled',(Exception,),{});ex.DecisionRequired=type('DecisionRequired',(Exception,),{});sys.modules['executor_v3']=ex
        sys.path.insert(0,str(HERE))
        from input_transition_owner_v4 import InputOwner
        owner=InputOwner(a.display); owner_id[0]=id(owner._inner)
        lease=Lease(int(win.id))
        admission=owner.call('down',lease,'a')
        raw['admission']=admission
        deadline=time.monotonic()+2
        press=None
        while time.monotonic()<deadline:
            if observer.pending_events(): ev=observer.next_event()
            else:
                ready,_,_=select.select([observer.fileno()],[],[],max(0,deadline-time.monotonic()))
                if not ready: break
                ev=observer.next_event()
            if ev.type not in (X.KeyPress,X.KeyRelease): continue
            press={'type':int(ev.type),'keycode':int(ev.detail),'window':int(ev.window.id),'observed_ns':time.perf_counter_ns()};break
        raw['client_events'].append(press) if press else None
        if not press or press['type']!=X.KeyPress or press['keycode']!=keycode or press['window']!=win.id: raise RuntimeError('press event mismatch')
        owner.close()
        raw['owner_closed']=True
        deadline=time.monotonic()+2
        release=None
        while time.monotonic()<deadline:
            if observer.pending_events(): ev=observer.next_event()
            else:
                ready,_,_=select.select([observer.fileno()],[],[],max(0,deadline-time.monotonic()))
                if not ready: break
                ev=observer.next_event()
            if ev.type not in (X.KeyPress,X.KeyRelease): continue
            release={'type':int(ev.type),'keycode':int(ev.detail),'window':int(ev.window.id),'observed_ns':time.perf_counter_ns()};break
        raw['client_events'].append(release) if release else None
        bitmap=observer.query_keymap();raw['observer_key_up']=not bool(bitmap[keycode//8]&(1<<(keycode%8)))
        inner=owner._inner
        raw['owner_records']=list(inner.records)
        raw['cleanup'].update({'owner_closed':inner.closed,'owner_stopped':inner.stopped.is_set(),'owner_thread_alive':inner.thread.is_alive(),'terminal_release':next((r for r in reversed(inner.records) if r.get('event')=='owner_release'),None)})
        if not release or release['type']!=X.KeyRelease or release['keycode']!=keycode or release['window']!=win.id: raise RuntimeError('release event mismatch')
        if not raw['observer_key_up']: raise RuntimeError('observer keymap still down')
        raw['status']='CANDIDATE_COMPLETE'
    except BaseException as e:
        raw['errors'].append(f'{type(e).__name__}: {e}')
    finally:
        if owner is not None:
            try:
                owner.close()
                inner=owner._inner
                raw['owner_records']=list(inner.records)
                raw['cleanup'].update({'owner_closed':inner.closed,'owner_stopped':inner.stopped.is_set(),'owner_thread_alive':inner.thread.is_alive(),'terminal_release':next((r for r in reversed(inner.records) if r.get('event')=='owner_release'),None)})
            except BaseException as e: raw['cleanup']['owner_close_error']=f'{type(e).__name__}: {e}'
        if observer is not None:
            try: observer.close()
            except BaseException as e: raw['cleanup']['observer_close_error']=f'{type(e).__name__}: {e}'
        if xvfb is not None:
            try: xvfb.terminate();xvfb.wait(timeout=5);raw['cleanup']['xvfb_exit']=xvfb.returncode
            except BaseException as e: raw['cleanup']['xvfb_error']=f'{type(e).__name__}: {e}';xvfb.kill();xvfb.wait(timeout=5)
        if original_query is not None:
            from Xlib import display
            display.Display.query_keymap=original_query
        (a.out/'RAW.json').write_text(json.dumps(raw,indent=2,sort_keys=True)+'\n')
    print(json.dumps({'status':raw['status'],'errors':raw['errors'],'cleanup':raw['cleanup']}))
if __name__=='__main__': main()
