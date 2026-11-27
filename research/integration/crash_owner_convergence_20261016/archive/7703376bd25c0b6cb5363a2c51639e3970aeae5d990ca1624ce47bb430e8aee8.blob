"""SIGKILL Executor V3 child while a separately resident InputOwner survives."""
import argparse,hashlib,json,select,socket,subprocess,sys,threading,time
from pathlib import Path

def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()

class Lease:
    def __init__(self,focus):
        self.deadline=time.perf_counter_ns()+20_000_000_000
        self.expected_focus=focus; self.expected_surface=focus
        self.intent_token='hardkill-supervised-a04'; self.cancel=threading.Event(); self.focus_invalid=False
    def check(self):
        if self.cancel.is_set(): raise RuntimeError('cancelled')
        if time.perf_counter_ns()>=self.deadline: raise RuntimeError('expired')

class Watcher:
    def __init__(self,name,window,types):
        from Xlib import X,display
        self.types=set(types); self.d=display.Display(name)
        self.w=self.d.create_resource_object('window',window); self.w.change_attributes(event_mask=X.KeyPressMask|X.KeyReleaseMask); self.d.sync()
        self.cv=threading.Condition(); self.events=[]; self.error=None; self.stop=threading.Event()
        self.thread=threading.Thread(target=self._run,daemon=False); self.thread.start()
    def _run(self):
        try:
            while not self.stop.is_set():
                if not self.d.pending_events():
                    ready,_,_=select.select([self.d.fileno()],[],[],.02)
                    if not ready: continue
                while self.d.pending_events():
                    event=self.d.next_event()
                    if event.type in self.types:
                        row={'type':int(event.type),'keycode':int(event.detail),'window':int(event.window.id),'observed_ns':time.perf_counter_ns()}
                        with self.cv: self.events.append(row); self.cv.notify_all()
        except BaseException as exc:
            with self.cv: self.error=f'{type(exc).__name__}: {exc}'; self.cv.notify_all()
    def wait(self,predicate,timeout):
        deadline=time.monotonic()+timeout
        with self.cv:
            while not any(predicate(row) for row in self.events) and self.error is None:
                left=deadline-time.monotonic()
                if left<=0: break
                self.cv.wait(left)
            if self.error: raise RuntimeError(self.error)
            return next((dict(row) for row in self.events if predicate(row)),None)
    def close(self):
        self.stop.set(); self.thread.join(2); self.d.close()
        if self.thread.is_alive(): raise RuntimeError('X watcher failed to stop')

def key_down(d,code):
    bitmap=d.query_keymap(); return bool(bitmap[code//8] & (1<<(code%8)))

def main():
    from Xlib import X,XK,display
    from input_transition_owner_v4 import InputOwner
    ap=argparse.ArgumentParser(); ap.add_argument('--out',type=Path,required=True); ap.add_argument('--display',default=':138'); args=ap.parse_args()
    if args.out.exists(): raise SystemExit('refusing to overwrite result')
    args.out.mkdir(parents=True); here=Path(__file__).resolve().parent; root=here.parent
    freeze=json.loads((root/'FREEZE.json').read_text())
    raw={'schema':'v39-executor-hardkill-supervised-xvfb-raw-a04-v1','status':'STOP','errors':[],'display':args.display,'scope':'current-main Executor V3 child separated from current InputOwner V4/V12 resident in supervisor process','cleanup':{}}
    xvfb=observer=watcher=owner=None; worker=None; sock_parent=sock_child=None; rpc_thread=None; reader=None
    queue=__import__('queue').Queue(); rpc_done=threading.Event()
    try:
        for name,digest in freeze['source_sha256'].items():
            if sha(here/name)!=digest: raise RuntimeError('frozen source mismatch: '+name)
        xvfb=subprocess.Popen(['Xvfb',args.display,'-screen','0','640x480x24','-nolisten','tcp','-noreset','-ac'],stdin=subprocess.DEVNULL,stdout=subprocess.DEVNULL,stderr=subprocess.PIPE)
        deadline=time.monotonic()+5
        while time.monotonic()<deadline:
            if xvfb.poll() is not None: raise RuntimeError('Xvfb exited during startup')
            try: observer=display.Display(args.display); break
            except Exception: time.sleep(.05)
        if observer is None: raise TimeoutError('Xvfb connection timeout')
        rootwin=observer.screen().root; keycode=int(observer.keysym_to_keycode(XK.string_to_keysym('a')))
        window=rootwin.create_window(50,50,320,200,0,observer.screen().root_depth,X.InputOutput,X.CopyFromParent,event_mask=X.KeyPressMask|X.KeyReleaseMask)
        window.map(); observer.sync(); observer.set_input_focus(window,X.RevertToParent,X.CurrentTime); observer.sync()
        if getattr(observer.get_input_focus().focus,'id',None)!=window.id: raise RuntimeError('focused-window binding failed')
        watcher=Watcher(args.display,int(window.id),(X.KeyPress,X.KeyRelease))
        lease=Lease(int(window.id)); owner=InputOwner(args.display)
        sock_parent,sock_child=socket.socketpair()
        worker=subprocess.Popen([sys.executable,str(here/'worker.py'),str(sock_child.fileno())],pass_fds=(sock_child.fileno(),),close_fds=True,stdin=subprocess.DEVNULL,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,bufsize=1)
        sock_child.close(); sock_child=None
        def broker():
            stream=sock_parent.makefile('rwb',buffering=0)
            try:
                while True:
                    line=stream.readline()
                    if not line: break
                    req=json.loads(line); result=owner.call(req['op'],lease,req['key'])
                    stream.write((json.dumps({'id':req['id'],'ok':True,'result':result})+'\n').encode())
            except BaseException as exc: queue.put({'event':'owner_broker_error','error':f'{type(exc).__name__}: {exc}'})
            finally: queue.put({'event':'executor_channel_eof','at_ns':time.perf_counter_ns()}); rpc_done.set(); stream.close()
        rpc_thread=threading.Thread(target=broker,daemon=False); rpc_thread.start()
        def read_worker():
            for line in worker.stdout:
                try: queue.put(json.loads(line))
                except Exception: queue.put({'event':'worker_parse_error','line':line[:300]})
        reader=threading.Thread(target=read_worker,daemon=True); reader.start()
        events=[]; active=False; deadline=time.monotonic()+5
        while time.monotonic()<deadline and not active:
            try: row=queue.get(timeout=.05); events.append(row)
            except __import__('queue').Empty: continue
            active=row.get('event')=='key_down_active'
        if not active: raise TimeoutError('Executor child did not report held key')
        press=watcher.wait(lambda e:e['type']==X.KeyPress and e['keycode']==keycode,2)
        if press is None or not key_down(observer,keycode): raise RuntimeError('independent keydown/keymap witness missing')
        raw.update({'executor_events':events,'keycode':keycode,'window':int(window.id),'key_press':press,'key_down_before_kill':True,'owner_separate_from_executor':True})
        raw['kill_requested_ns']=time.perf_counter_ns(); worker.kill(); raw['worker_returncode']=worker.wait(timeout=5); raw['worker_dead_ns']=time.perf_counter_ns()
        if not rpc_done.wait(2): raise TimeoutError('persistent owner did not observe executor channel EOF')
        rpc_rows=[]
        while not queue.empty(): rpc_rows.append(queue.get_nowait())
        raw['supervisor_events']=rpc_rows
        if not any(x.get('event')=='executor_channel_eof' for x in rpc_rows): raise RuntimeError('worker EOF event not recorded')
        raw['owner_close_started_ns']=time.perf_counter_ns(); owner.close(); raw['owner_close_returned_ns']=time.perf_counter_ns()
        # InputOwner V4 delegates directly to its configured V12 owner here.
        innermost=owner._inner
        raw['owner_records']=list(innermost.records); raw['owner_thread_stopped']=innermost.stopped.is_set(); raw['owner_thread_alive']=innermost.thread.is_alive()
        raw['owner_release_record']=next((x for x in reversed(raw['owner_records']) if x.get('event')=='owner_release'),None)
        raw['key_release_after_kill']=watcher.wait(lambda e:e['type']==X.KeyRelease and e['keycode']==keycode and e['observed_ns']>=raw['kill_requested_ns'],2)
        raw['key_up_after_owner_close']=not key_down(observer,keycode); raw['watcher_events']=watcher.events
        raw['worker_killed_by_sigkill']=raw['worker_returncode']==-9
        if not raw['worker_killed_by_sigkill']: raise RuntimeError('Executor child not SIGKILLed')
        raw['status']='CANDIDATE_COMPLETE'
    except BaseException as exc: raw['errors'].append(f'{type(exc).__name__}: {exc}')
    finally:
        if worker is not None and worker.poll() is None:
            worker.kill()
            try: worker.wait(timeout=3)
            except Exception: pass
        if sock_parent is not None:
            try: sock_parent.close()
            except Exception: pass
        if rpc_thread is not None: rpc_thread.join(timeout=2)
        if owner is not None:
            try: owner.close()
            except BaseException as exc: raw['cleanup']['owner_close_error']=f'{type(exc).__name__}: {exc}'
        if watcher is not None:
            try: raw.setdefault('watcher_events',watcher.events); watcher.close()
            except BaseException as exc: raw['cleanup']['watcher_error']=f'{type(exc).__name__}: {exc}'
        if observer is not None:
            try: observer.close()
            except BaseException as exc: raw['cleanup']['observer_error']=f'{type(exc).__name__}: {exc}'
        if xvfb is not None:
            try: xvfb.terminate(); xvfb.wait(timeout=5); raw['cleanup']['xvfb_exit']=xvfb.returncode
            except BaseException as exc: raw['cleanup']['xvfb_error']=f'{type(exc).__name__}: {exc}'; xvfb.kill(); xvfb.wait(timeout=5); raw['cleanup']['xvfb_exit']=xvfb.returncode
        if raw['errors'] or raw['cleanup'].get('xvfb_exit')!=0 or any(k.endswith('_error') for k in raw['cleanup']): raw['status']='STOP'
        (args.out/'RAW.json').write_text(json.dumps(raw,indent=2,sort_keys=True)+'\n')
    print(json.dumps({'status':raw['status'],'errors':raw['errors'],'worker_exit':raw.get('worker_returncode'),'owner_release_verified':bool((raw.get('owner_release_record') or {}).get('verified')),'key_up':raw.get('key_up_after_owner_close'),'cleanup':raw['cleanup']},sort_keys=True))
    if raw['status']!='CANDIDATE_COMPLETE': raise SystemExit(1)
if __name__=='__main__': main()
