"""Hard-kill current-main Executor V3 + InputOwner while Xvfb key is down."""
import argparse,hashlib,json,os,select,subprocess,sys,threading,time
from pathlib import Path

def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()

class Watcher:
    def __init__(self,name,window,types):
        from Xlib import X,display
        self.types=set(types); self.d=display.Display(name); self.w=self.d.create_resource_object('window',window)
        self.w.change_attributes(event_mask=X.KeyPressMask|X.KeyReleaseMask); self.d.sync()
        self.cv=threading.Condition(); self.events=[]; self.err=None; self.stop=threading.Event(); self.started=time.perf_counter_ns()
        self.t=threading.Thread(target=self.run,daemon=False); self.t.start()
    def run(self):
        try:
            while not self.stop.is_set():
                if not self.d.pending_events():
                    ready,_,_=select.select([self.d.fileno()],[],[],0.02)
                    if not ready: continue
                while self.d.pending_events():
                    e=self.d.next_event()
                    if e.type in self.types:
                        row={'type':int(e.type),'keycode':int(e.detail),'window':int(e.window.id),'observed_ns':time.perf_counter_ns()}
                        with self.cv: self.events.append(row); self.cv.notify_all()
        except BaseException as e:
            with self.cv: self.err=f'{type(e).__name__}: {e}'; self.cv.notify_all()
    def wait(self,pred,timeout):
        end=time.monotonic()+timeout
        with self.cv:
            while not any(pred(x) for x in self.events) and not self.err:
                rem=end-time.monotonic()
                if rem<=0: break
                self.cv.wait(rem)
            if self.err: raise RuntimeError(self.err)
            return next((dict(x) for x in self.events if pred(x)),None)
    def close(self):
        self.stop.set(); self.t.join(2); self.d.close()
        if self.t.is_alive(): raise RuntimeError('watcher failed to stop')

def key_down(d,code):
    bm=d.query_keymap(); return bool(bm[code//8] & (1 << (code%8)))

def main():
    from Xlib import X,XK,display
    ap=argparse.ArgumentParser(); ap.add_argument('--out',type=Path,required=True); ap.add_argument('--display',default=':137'); a=ap.parse_args()
    if a.out.exists(): raise SystemExit('refusing to overwrite result leaf')
    a.out.mkdir(parents=True); here=Path(__file__).resolve().parent; root=here.parent
    raw={'schema':'v39-executor-hardkill-xvfb-raw-a01-v1','status':'STOP','errors':[],'display':a.display,'scope':'current-main in-process Executor V3 and InputOwner V4/V12 worker process; SIGKILL under held Xvfb key','events':[],'cleanup':{}}
    xv=None; observer=None; watcher=None; proc=None; reader=None; lines=[]; q=__import__('queue').Queue(); keycode=None; window=None
    try:
        freeze=json.loads((root/'FREEZE.json').read_text())
        for n,h in freeze['source_sha256'].items():
            if sha(here/n)!=h: raise RuntimeError('frozen source mismatch '+n)
        xv=subprocess.Popen(['Xvfb',a.display,'-screen','0','640x480x24','-nolisten','tcp','-noreset','-ac'],stdin=subprocess.DEVNULL,stdout=subprocess.DEVNULL,stderr=subprocess.PIPE)
        end=time.monotonic()+5
        while time.monotonic()<end:
            if xv.poll() is not None: raise RuntimeError('Xvfb exited on startup')
            try: observer=display.Display(a.display); break
            except Exception: time.sleep(.05)
        if observer is None: raise TimeoutError('Xvfb display startup timeout')
        rootwin=observer.screen().root; keycode=int(observer.keysym_to_keycode(XK.string_to_keysym('a')))
        win=rootwin.create_window(40,40,300,180,0,observer.screen().root_depth,X.InputOutput,X.CopyFromParent,event_mask=X.KeyPressMask|X.KeyReleaseMask)
        win.map(); observer.sync(); observer.set_input_focus(win,X.RevertToParent,X.CurrentTime); observer.sync()
        if getattr(observer.get_input_focus().focus,'id',None)!=win.id: raise RuntimeError('test window not focused')
        while observer.pending_events(): observer.next_event()
        watcher=Watcher(a.display,int(win.id),(X.KeyPress,X.KeyRelease))
        log=a.out/'worker-events.jsonl'
        proc=subprocess.Popen([sys.executable,str(here/'worker.py'),a.display,str(int(win.id)),str(log)],stdin=subprocess.DEVNULL,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,bufsize=1)
        def read_lines():
            for line in proc.stdout:
                try: q.put(json.loads(line))
                except Exception: q.put({'parse_error':line[:300]})
        reader=threading.Thread(target=read_lines,daemon=True); reader.start()
        got_down=False; deadline=time.monotonic()+5
        while time.monotonic()<deadline and not got_down:
            try: row=q.get(timeout=.05); lines.append(row)
            except __import__('queue').Empty: continue
            if row.get('event')=='key_down_active': got_down=True
        if not got_down: raise TimeoutError('worker did not report active key hold')
        press=watcher.wait(lambda e:e['type']==X.KeyPress and e['keycode']==keycode,2)
        if not press or not key_down(observer,keycode): raise RuntimeError('no independent keydown/keymap proof before kill')
        raw['events']=lines; raw['keycode']=keycode; raw['window']=int(win.id); raw['key_press']=press; raw['key_down_before_kill']=True
        raw['kill_requested_ns']=time.perf_counter_ns(); proc.kill(); raw['worker_returncode']=proc.wait(timeout=5); raw['worker_dead_observed_ns']=time.perf_counter_ns()
        release=watcher.wait(lambda e:e['type']==X.KeyRelease and e['keycode']==keycode and e['observed_ns']>=raw['kill_requested_ns'],1)
        deadline=time.monotonic()+1; states=[]
        while time.monotonic()<deadline:
            down=key_down(observer,keycode); states.append({'at_ns':time.perf_counter_ns(),'down':down})
            if not down: break
            time.sleep(.01)
        raw['key_release_after_kill']=release; raw['keymap_samples_after_kill']=states
        raw['key_up_within_1s']=bool(states and states[-1]['down'] is False)
        raw['worker_killed_by_sigkill']=raw['worker_returncode']==-9
        if not raw['worker_killed_by_sigkill']: raise RuntimeError('worker did not exit by SIGKILL status -9')
        raw['status']='CANDIDATE_COMPLETE'
    except BaseException as e: raw['errors'].append(f'{type(e).__name__}: {e}')
    finally:
        if proc is not None and proc.poll() is None:
            proc.kill()
            try: proc.wait(timeout=3)
            except Exception: pass
        if reader is not None: reader.join(timeout=1)
        if proc is not None:
            try: raw['worker_stderr']=proc.stderr.read()[-4000:]
            except Exception: pass
        if watcher is not None:
            try: raw['watcher_events']=watcher.events; watcher.close()
            except BaseException as e: raw['cleanup']['watcher_error']=f'{type(e).__name__}: {e}'
        if observer is not None:
            try: observer.close()
            except BaseException as e: raw['cleanup']['observer_error']=f'{type(e).__name__}: {e}'
        if xv is not None:
            try: xv.terminate(); xv.wait(timeout=5); raw['cleanup']['xvfb_exit']=xv.returncode
            except BaseException as e: raw['cleanup']['xvfb_error']=f'{type(e).__name__}: {e}'; xv.kill(); xv.wait(timeout=5); raw['cleanup']['xvfb_exit']=xv.returncode
        if raw['errors'] or raw['cleanup'].get('xvfb_exit')!=0 or any(k.endswith('_error') for k in raw['cleanup']): raw['status']='STOP'
        (a.out/'RAW.json').write_text(json.dumps(raw,indent=2,sort_keys=True)+'\n')
    print(json.dumps({'status':raw['status'],'errors':raw['errors'],'worker_returncode':raw.get('worker_returncode'),'key_up_within_1s':raw.get('key_up_within_1s'),'cleanup':raw['cleanup']},sort_keys=True))
    if raw['status']!='CANDIDATE_COMPLETE': raise SystemExit(1)
if __name__=='__main__': main()
