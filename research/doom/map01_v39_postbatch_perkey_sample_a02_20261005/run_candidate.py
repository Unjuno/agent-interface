#!/usr/bin/env python3
"""One-shot inert current-V39 post-batch keymap sample experiment."""
from __future__ import annotations
import hashlib, importlib.util, json, os, sys, threading, time, types
from pathlib import Path
HERE=Path(__file__).resolve().parent; ROOT=HERE.parents[2]
OUT=Path(os.environ.get('RESULT_DIR', str(HERE/'results/a02')))
MODE='normal'; REC=[]; LOCK=threading.Lock(); DISPLAY_INSTANCES=[]
def sha(b): return hashlib.sha256(b).hexdigest()
def record(name, **fields):
 with LOCK: REC.append({'event':name,'time_ns':time.perf_counter_ns(),**fields})
def main():
 freeze=json.loads((HERE/'FREEZE.json').read_text())
 head=os.environ.get('BASE_COMMIT','')
 if head!=freeze['base_commit']: raise SystemExit('STOP base mismatch')
 if sha(Path(__file__).read_bytes())!=freeze['candidate_sha256']: raise SystemExit('STOP candidate hash mismatch')
 for rel,digest in freeze['source_sha256'].items():
  if sha((ROOT/rel).read_bytes())!=digest: raise SystemExit('STOP source hash mismatch: '+rel)
 if OUT.exists():
  if any(OUT.iterdir()): raise SystemExit('STOP output directory is occupied')
 else: OUT.mkdir(parents=True,exist_ok=False)
 DOOM=ROOT/'research/doom'; LIVE=ROOT/'research/live_control'
 sys.path[:0]=[str(DOOM),str(LIVE)]
 global MODE
 X=types.SimpleNamespace(KeyPress=2,KeyRelease=3,ButtonPress=4,ButtonRelease=5,Button1Mask=256,AnyPropertyType=0,IsViewable=2)
 XK=types.SimpleNamespace(string_to_keysym=lambda value:value)
 class FakeRoot:
  id=1
  def query_pointer(self): record('query_pointer'); return types.SimpleNamespace(mask=0,root_x=0,root_y=0,child=None)
  def get_geometry(self): return types.SimpleNamespace(width=1024,height=768)
 class FakeDisplay:
  def __init__(self,name):
   self.name=name; self.root=FakeRoot(); self.keys=set(); self.fail_sample=(MODE=='sample_error'); DISPLAY_INSTANCES.append(self); record('display_open',display=name,mode=MODE)
  def screen(self): return types.SimpleNamespace(root=self.root)
  def get_input_focus(self): record('get_input_focus'); return types.SimpleNamespace(focus=types.SimpleNamespace(id=42))
  def keysym_to_keycode(self,sym): return {'a':38,'space':65}.get(sym,0)
  def sync(self): record('display_sync')
  def query_keymap(self):
   record('query_keymap',keys=sorted(self.keys))
   if self.fail_sample:
    self.fail_sample=False; record('query_keymap_error',error='injected_once'); raise RuntimeError('injected keymap sample failure')
   bitmap=bytearray(32)
   for code in self.keys: bitmap[code//8]|=1<<(code%8)
   return bytes(bitmap)
  def close(self): record('display_close')
 def fake_input(d,event,detail,**kwargs):
  name='key_down' if event==X.KeyPress else 'key_up' if event==X.KeyRelease else 'other_input'
  if event==X.KeyPress: d.keys.add(detail)
  elif event==X.KeyRelease and not (MODE=='release_stuck' and detail==65): d.keys.discard(detail)
  record(name,keycode=detail,display_event_type=event)
 xlib=types.ModuleType('Xlib'); xlib.__path__=[]; xlib.X=X; xlib.XK=XK
 xdisplay=types.ModuleType('Xlib.display'); xdisplay.Display=FakeDisplay
 xerror=types.ModuleType('Xlib.error'); xerror.BadWindow=type('BadWindow',(Exception,),{}); xerror.BadDrawable=type('BadDrawable',(Exception,),{})
 xext=types.ModuleType('Xlib.ext'); xext.__path__=[]; xtest=types.ModuleType('Xlib.ext.xtest'); xtest.fake_input=fake_input; xext.xtest=xtest
 xlib.display=xdisplay; xlib.error=xerror; xlib.ext=xext
 sys.modules.update({'Xlib':xlib,'Xlib.display':xdisplay,'Xlib.error':xerror,'Xlib.ext':xext,'Xlib.ext.xtest':xtest})
 # The current V3 default is not instantiated; the selected V4 wrapper supplies this candidate V12 owner.
 owner_v10=types.ModuleType('input_owner_v10'); owner_v10.InputOwner=type('UnusedV10',(),{}); sys.modules['input_owner_v10']=owner_v10
 # The actual V15 release backend is retained; only its typed lower-level operation loop is scripted.
 base=types.ModuleType('doom_typed_release_backend_v2')
 class DummyOwner:
  def close(self): record('inherited_empty_owner_close')
 class FakeTypedBackend:
  def __init__(self,session,out,emit,signal_readers):
   self.owner=DummyOwner(); self.held=set(); self.emit=emit; self._input_event_context=None
   self.lease=types.SimpleNamespace(intent_token='postbatch-a01-'+MODE,deadline=time.perf_counter_ns()+60_000_000_000,expected_focus=42,expected_surface=None,expected_geometry=None,focus_invalid=False,cancel=threading.Event(),check=lambda:None)
  def execute(self,step,cancel,identifier,index):
   self._input_event_context=(identifier,index)
   try:
    for key in step['keys']: self.raw(key,True)
    for key in step['keys']: self.raw(key,False)
   finally: self._input_event_context=None
  def release_all(self): return self.owner.call('release',self.lease)
 base.Backend=FakeTypedBackend; base.suite=object(); sys.modules['doom_typed_release_backend_v2']=base
 # Load the isolated owner candidate as V12 so current V3/V4 and the real release backend compose around it.
 candidate_path=HERE/'experimental_source/input_owner_v13_postbatch_candidate.py'
 spec=importlib.util.spec_from_file_location('input_owner_v12',candidate_path); owner_mod=importlib.util.module_from_spec(spec); sys.modules['input_owner_v12']=owner_mod; spec.loader.exec_module(owner_mod)
 from doom_owner_thread_release_batch_backend_v1 import Backend
 scenarios=[]
 for scenario in ('normal','release_stuck','sample_error'):
  MODE=scenario; REC.clear(); DISPLAY_INSTANCES.clear(); sample_box={}; emitted=[]
  backend=Backend(types.SimpleNamespace(name='fake-display-v39'),None,lambda row: emitted.append(row),{})
  owner=backend.owner; original_call=owner.call
  def traced_call(operation,lease=None,key=None):
   result=original_call(operation,lease,key)
   if operation=='input_state':
    sample_box['result']=result
    if 'physical_keymap_sample_started_ns' in result:
     record('postbatch_keymap_sample',owner_id=result['owner_id'],intent_token=backend.lease.intent_token,
            sample_started_ns=result['physical_keymap_sample_started_ns'],sample_finished_ns=result['physical_keymap_sample_finished_ns'],
            sampled_owned_keycodes_down=result['sampled_owned_keycodes_down'])
   return result
  owner.call=traced_call
  def emit(row):
   if row.get('event')=='input_release_transition':
    sample=sample_box.get('result'); receipt=row.get('owner_thread_keyup_receipt')
    if isinstance(sample,dict) and isinstance(receipt,dict):
     keycode=receipt.get('keycode'); down=sample.get('sampled_owned_keycodes_down')
     if (sample.get('owner_id')==row.get('owner_id') and sample.get('owner_id')==receipt.get('owner_id')
         and backend.lease.intent_token==row.get('intent_token')==receipt.get('intent_token')
         and type(keycode) is int and isinstance(down,list)
         and type(sample.get('physical_keymap_sample_started_ns')) is int
         and sample['physical_keymap_sample_started_ns']>=row.get('release_call_returned_ns',0)):
      row['post_batch_key_state_sample']={'schema':'per-key-postbatch-keymap-v1','key':row.get('key'),'keycode':keycode,
       'program_id':row.get('id'),'step':row.get('step'),'owner_id':row.get('owner_id'),'intent_token':row.get('intent_token'),
       'sample_started_ns':sample['physical_keymap_sample_started_ns'],'sample_finished_ns':sample['physical_keymap_sample_finished_ns'],
       'status':'PHYSICAL_STILL_DOWN_AT_POSTBATCH_SAMPLE' if keycode in down else 'KEY_UP_AT_POSTBATCH_SAMPLE',
       'physical_verification_authoritative':False,'application_consumption_observed':False}
   emitted.append(row)
  backend.emit=emit
  try:
   backend.execute({'keys':['a','space']},None,'two-key-postbatch-'+scenario,7)
   case_error=None
  except BaseException as exc:
   case_error=type(exc).__name__+': '+str(exc); record('candidate_exception',error=case_error)
  before_close=[dict(x) for x in REC]
  physical_before_close=sorted(DISPLAY_INSTANCES[0].keys) if DISPLAY_INSTANCES else []
  held_before_close=sorted(backend.held)
  owner_close_error=None
  try: owner.close()
  except BaseException as exc: owner_close_error=type(exc).__name__+': '+str(exc); record('owner_close_exception',error=owner_close_error)
  scenarios.append({'scenario':scenario,'events':emitted,'operations':before_close,'physical_keycodes_before_close':physical_before_close,
                    'backend_held_before_close':held_before_close,'candidate_exception':case_error,'owner_close_exception':owner_close_error,
                    'sample_returned':sample_box.get('result') is not None})
 raw={'schema':'map01-v39-postbatch-perkey-keymap-candidate-v1','run_id':freeze['run_id'],'base_commit':head,
      'scenarios':scenarios,'environment':{'fake_xlib':True,'live_x_server':False,'gui':False,'game':False,'model_calls':0,'os_input':False,'container':os.environ.get('CONTAINER_RUN')=='1'},
      'scope':'actual current release-batch backend and V3/V4 owner adapters with an experimental V12 input_state keymap sample; typed step loop and X display are inert fakes'}
 raw_bytes=(json.dumps(raw,indent=2,sort_keys=True)+'\n').encode(); (OUT/'raw.json').write_bytes(raw_bytes)
 print(json.dumps({'status':'CANDIDATE_EXECUTED','raw_sha256':sha(raw_bytes),'scenarios':[{k:x[k] for k in ('scenario','candidate_exception','owner_close_exception','sample_returned')} for x in scenarios]},sort_keys=True))
if __name__=='__main__': main()
