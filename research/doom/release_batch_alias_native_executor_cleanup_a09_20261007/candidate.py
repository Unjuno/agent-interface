#!/usr/bin/env python3
import json, pathlib, select, subprocess, sys, time, threading, hashlib
HERE=pathlib.Path(__file__).resolve().parent
SRC=HERE/'source'; sys.path[:0]=[str(SRC)]
class Lease:
 def __init__(self, focus):
  self.deadline=time.perf_counter_ns()+10_000_000_000; self.expected_focus=focus; self.intent_token='a07'; self.cancel=threading.Event(); self.focus_invalid=False
 def check(self): pass
 def interruption_snapshot(self): return None
 def record_interruption(self,row): pass
 def is_set(self): return self.cancel.is_set()
 def wait(self,s): return self.cancel.wait(s)
 def set(self): self.cancel.set()
 def wait_interruption(self,s): return None
class Backend:
 def __init__(self,owner,focus): self.owner=owner; self.lease=Lease(focus); self.held=set(); self.sequence=0
 def execute(self,step,cancel,identifier,index):
  self.lease=cancel
  self.owner.call('down',cancel,'a'); self.held.add('a'); self.owner.call('down',cancel,'A'); self.held.add('A')
  return self.owner.call('up_batch',cancel,['a','A'])
 def release_all(self): return self.owner.call('release',self.lease)
 def validate(self,steps): pass

def main():
 out=pathlib.Path('/out/A09_RAW.json'); raw={'schema':'a09-native-v15-v13-alias-cleanup-raw-v1','status':'STOP','errors':[],'limits':['One isolated Xvfb case; candidate-only alias guard; no game/model/physical keyboard/application effect.']}; xvfb=obs=owner=None
 try:
  from Xlib import X, Xatom, XK, display
  xvfb=subprocess.Popen(['Xvfb',':139','-screen','0','640x480x24','-nolisten','tcp','-noreset','-ac'],stdout=subprocess.DEVNULL,stderr=subprocess.PIPE)
  end=time.monotonic()+5
  while time.monotonic()<end:
   try: obs=display.Display(':139'); break
   except Exception: time.sleep(.05)
  if obs is None: raise RuntimeError('Xvfb observer connect timeout')
  screen=obs.screen(); root=screen.root; window=root.create_window(20,20,320,200,0,screen.root_depth,X.InputOutput,X.CopyFromParent,event_mask=X.KeyPressMask|X.KeyReleaseMask); window.map(); obs.sync(); obs.set_input_focus(window,X.RevertToParent,X.CurrentTime); obs.sync(); time.sleep(.05)
  focus=obs.get_input_focus().focus.id; codes=[obs.keysym_to_keycode(XK.string_to_keysym(k)) for k in ('a','A')]; raw['alias_codes']=codes
  sys.path.insert(0,str(HERE)); import guarded_input_owner_v12 as guarded
  guarded.X=X; guarded.XK=XK; guarded.display=display; guarded.error=__import__('Xlib').error; guarded.xtest=__import__('Xlib.ext.xtest',fromlist=['xtest'])
  sys.modules['input_owner_v12']=guarded
  owner_mod=__import__('input_transition_owner_v4'); owner=owner_mod.InputOwner(':139',_owner_cls=guarded.InputOwner)
  # Candidate uses the same production owner chain and V13 finally-cleanup, with a narrow backend adapter.
  backend=Backend(owner,focus); emitted=[]; from executor_v13 import Executor
  engine=Executor(backend,emitted.append)
  engine.submit('a09', [{'op':'key_batch','actions':[]}], expected_sequence=0, valid_until_ns=time.perf_counter_ns()+5_000_000_000)
  end=time.monotonic()+3
  while time.monotonic()<end and not any(x.get('event')=='terminal' for x in emitted): time.sleep(.005)
  engine.close(); raw['events']=emitted; raw['terminal']=next((x for x in emitted if x.get('event')=='terminal'),None); raw['owner_records']=list(owner._inner.records); raw['keymap_after']=obs.query_keymap()[codes[0]//8] & (1<<(codes[0]%8)) !=0; raw['status']='CANDIDATE_COMPLETE' if raw['terminal'] else 'STOP'
 except BaseException as e: raw['errors'].append(type(e).__name__+': '+str(e))
 finally:
  if owner:
   try: owner.close()
   except BaseException as e: raw.setdefault('cleanup_errors',[]).append(type(e).__name__+': '+str(e))
  if obs:
   try: obs.close()
   except Exception: pass
  if xvfb:
   xvfb.terminate(); xvfb.wait(timeout=5); raw['xvfb_exit']=xvfb.returncode
  out.write_text(json.dumps(raw,indent=2,sort_keys=True)+'\n')
 print(json.dumps({'status':raw['status'],'errors':raw['errors'],'terminal':raw.get('terminal'),'keymap_after':raw.get('keymap_after')}))
if __name__=='__main__': main()
