import asyncio, json, os, signal, subprocess, sys, time
from pathlib import Path
from Xlib import X, Xatom, XK, display
from Xlib.ext import xtest
from runtime.cli_v1.mcp_server import create_server
from runtime.guarded_x11_v1.owned_target_process import OwnedTargetProcess
from runtime.cli_v1.test_mcp_xvfb_blocked_release_integration import _metadata, _xvfb_blocking_owner_factory

MODE=os.environ['TARGET_RETIRE_MODE']; ROOT=Path('/evidence'); os.environ['DISPLAY']=':98'; os.environ['AGENT_INTERFACE_MCP_XVFB_DELAY_MS']='8000'; os.environ['AGENT_INTERFACE_MCP_XVFB_TRANSACTION_TIMEOUT_S']='4'; os.environ['AGENT_INTERFACE_MCP_XVFB_CANCEL_ACK_WITHHOLD_S']='0.1'
APP=r'''import json, os, sys, time
from pathlib import Path
from Xlib import X, XK, display
root=Path(sys.argv[1]); kind=sys.argv[2]; ready=root/(kind+'.ready'); state=root/(kind+'.json')
d=display.Display(); s=d.screen(); base=s.root.create_window(30,30,240,180,0,X.CopyFromParent,X.InputOutput,X.CopyFromParent,background_pixel=0,event_mask=X.KeyPressMask|X.KeyReleaseMask); base.map(); w=base.create_window(0,0,200,140,0,X.CopyFromParent,X.InputOutput,X.CopyFromParent,background_pixel=0,event_mask=X.KeyPressMask|X.KeyReleaseMask) if kind=='fresh' else base; w.map(); w.set_input_focus(X.RevertToParent,X.CurrentTime); gc=w.create_gc(foreground=0xFFFFFF)
for r in range(9):
 for c in range(13):
  if (r+c)%2==0: w.fill_rectangle(gc,c*16,r*16,16,16)
d.sync(); code=d.keysym_to_keycode(XK.string_to_keysym('a' if kind=='old' else 'b'))
def save(events):
 tmp=state.with_suffix('.tmp'); tmp.write_text(json.dumps({'kind':kind,'pid':os.getpid(),'window':w.id,'events':events})+'\n'); tmp.replace(state)
events=[]; save(events); ready.write_text(json.dumps({'pid':os.getpid(),'window':w.id,'keycode':code})+'\n')
while True:
 if d.pending_events():
  e=d.next_event()
  if e.type in (X.KeyPress,X.KeyRelease) and (e.detail==code or kind=='fresh'):
   events.append({'type':'press' if e.type==X.KeyPress else 'release','ns':time.monotonic_ns(),'window':getattr(e.window,'id',e.window),'detail':e.detail}); save(events)
 else: time.sleep(.001)
'''

def wait_file(p,timeout=5):
 end=time.monotonic()+timeout
 while time.monotonic()<end:
  if p.exists(): return json.loads(p.read_text())
  time.sleep(.005)
 raise TimeoutError('file '+str(p))
def proc_state(pid):
 t=Path('/proc',str(pid),'stat').read_text(); return t[t.rfind(')')+1:].split()[0]
def down(d,code):
 m=d.query_keymap(); return bool(m[code//8]&(1<<(code%8)))
def spawn(kind):
 err=(ROOT/(kind+'.stderr')).open('ab'); p=subprocess.Popen([sys.executable,'-c',APP,str(ROOT),kind],env=os.environ.copy(),stdout=subprocess.DEVNULL,stderr=err); info=wait_file(ROOT/(kind+'.ready')); return p,info
def spawn_owned(kind):
 handle=OwnedTargetProcess.launch([sys.executable,'-c',APP,str(ROOT),kind],disposable=True,env=os.environ.copy()); info=wait_file(ROOT/(kind+'.ready')); return handle,info
def md(x):
 if isinstance(x,dict): return x
 return _metadata(x)
async def call(server,tool,args): return md(await asyncio.wait_for(server.call_tool(tool,args),5))
async def terminal(server,initial,timeout=5):
 if initial.get('status')!='pending': return initial
 cid=initial['call_id']; end=time.monotonic()+timeout
 while time.monotonic()<end:
  row=await call(server,'interface_results',{'call_id':cid,'include_image':False})
  if row.get('status')!='pending': return row
  await asyncio.sleep(.01)
 raise TimeoutError('terminal result pending')
async def main():
 result={'schema':'r101-public-mcp-owned-target-retirement-v1','status':'RUNNING','timing_ns':{},'checks':{},'old':{},'cancel':{},'recovery':{},'cleanup':{}}
 xvfb=None; observer=None; old=None; fresh=None; old_server=None; fresh_server=None; xlog=(ROOT/'xvfb.log').open('wb')
 try:
  xvfb=subprocess.Popen(['Xvfb',':98','-screen','0','640x480x24','-nolisten','tcp'],stdout=xlog,stderr=subprocess.STDOUT); result['xvfb_pid']=xvfb.pid
  end=time.monotonic()+5
  while time.monotonic()<end:
   try: observer=display.Display(':98'); break
   except Exception: time.sleep(.02)
  if observer is None: raise RuntimeError('Xvfb startup failed')
  rep=observer.get_keyboard_control().global_auto_repeat
  if rep!=X.AutoRepeatModeOn: observer.change_keyboard_control(auto_repeat_mode=X.AutoRepeatModeOn); observer.sync()
  result['repeat_mode']=observer.get_keyboard_control().global_auto_repeat
  if result['repeat_mode']!=X.AutoRepeatModeOn: raise RuntimeError('repeat ON readback failed')
  old_handle,oi=spawn_owned('old'); old=old_handle._process; result['old'].update(pid=oi['pid'],window=oi['window'],keycode=oi['keycode'])
  result['timing_ns']['server_create_started']=time.monotonic_ns()
  old_root=ROOT/'mcp-old'; old_server=create_server({'app':oi['window']},old_root,session_mode='guarded-x11',guarded_process_identity=True,guarded_query_worker=True,guarded_window_lifecycle=True,guarded_owned_process=True,guarded_prestarted_cancel_supervisor=True,_guarded_owner_factory=_xvfb_blocking_owner_factory,_guarded_owned_target_process=(old_handle if MODE=='retire' else None),_guarded_prestarted_target_identity=True)
  result['timing_ns']['server_create_returned']=time.monotonic_ns()
  obs=await call(old_server,'interface_guarded_observe',{}); result['timing_ns']['first_observe_returned']=time.monotonic_ns(); result['old']['observe']=obs
  if obs.get('status')!='observed': raise RuntimeError('old public observe failed')
  src=obs['source']; minted=await call(old_server,'interface_guarded_mint',{'alias':'field','source_sequence':src['sequence'],'point':[88,88],'region_size':[24,24]}); result['old']['mint']=minted
  if minted.get('status')!='minted': raise RuntimeError('old public mint failed')
  action=await call(old_server,'interface_guarded_input',{'alias':'field','offset':minted['offset'],'interaction':'keyboard','observe_after':False,'wait_for_result_ms':0,'tail':[{'op':'key_chord','keys':['a']}]}); result['old']['action_initial']=action
  if action.get('status')!='pending': raise RuntimeError('old action did not remain pending')
  cid=action['call_id']; marker=old_root/'xvfb-owner-sync-entered.json'; delayed=old_root/'xvfb-delayed-request-queued.json'
  wait_file(marker,4); result['old']['delayed_marker']=wait_file(delayed,4)
  end=time.monotonic()+3
  while time.monotonic()<end:
   f=ROOT/'old.json'
   if f.exists() and len([e for e in json.loads(f.read_text())['events'] if e['type']=='press'])>=1: break
   time.sleep(.005)
  old_events=json.loads((ROOT/'old.json').read_text())['events']; result['old']['events_before_stop']=old_events
  result['old']['effect_before_stop']=len([e for e in old_events if e['type']=='press'])
  if result['old']['effect_before_stop']!=1: raise RuntimeError('old effect not exactly one before cancellation')
  xv_id=xvfb.pid; os.kill(xv_id,signal.SIGSTOP); result['timing_ns']['stop_requested']=time.monotonic_ns()
  end=time.monotonic()+2
  while time.monotonic()<end and proc_state(xv_id) not in ('T','t'): time.sleep(.005)
  if proc_state(xv_id) not in ('T','t'): raise TimeoutError('Xvfb did not stop')
  result['timing_ns']['stopped']=time.monotonic_ns()
  original_pidfd_signal=signal.pidfd_send_signal; faults={'count':0}
  def injected_pidfd_signal(fd, sig, *args, **kwargs):
   if fd==old_handle._pidfd and faults['count']==0:
    faults['count']+=1
    raise PermissionError('injected target pidfd signal failure')
   return original_pidfd_signal(fd,sig,*args,**kwargs)
  signal.pidfd_send_signal=injected_pidfd_signal
  cancel=await call(old_server,'interface_guarded_cancel',{'call_id':cid}); result['cancel']['response']=cancel; result['timing_ns']['cancel_returned']=time.monotonic_ns()
  end=time.monotonic()+2
  while time.monotonic()<end and faults['count']==0: await asyncio.sleep(.005)
  if faults['count']!=1: raise TimeoutError('injected signal failure not observed before resume')
  result['old']['injected_signal_failure_count']=faults['count']
  result['old']['retired_exitcode']=old.poll(); result['timing_ns']['old_process_retired']=time.monotonic_ns(); result['old']['alive_before_resume']=old.poll() is None
  remaining=0.650-(time.monotonic_ns()-result['timing_ns']['stopped'])/1000000000
  if remaining>0: await asyncio.sleep(remaining)
  os.kill(xv_id,signal.SIGCONT); result['timing_ns']['resume_requested']=time.monotonic_ns()
  end=time.monotonic()+2
  while time.monotonic()<end and proc_state(xv_id) in ('T','t'): time.sleep(.005)
  if proc_state(xv_id) in ('T','t'): raise TimeoutError('Xvfb did not resume')
  result['timing_ns']['resumed']=time.monotonic_ns()
  cancel_terminal=await call(old_server,'interface_guarded_cancel',{'call_id':cid})
  cancel_deadline=time.monotonic()+5
  while cancel_terminal.get('status')=='pending' and time.monotonic()<cancel_deadline:
   await asyncio.sleep(.01); cancel_terminal=await call(old_server,'interface_guarded_cancel',{'call_id':cid})
  result['cancel']['terminal']=cancel_terminal
  old_cancel=(cancel_terminal.get('result') or cancel_terminal)
  result['old']['target_retirement']=old_cancel.get('owned_target_retirement')
  result['old']['target_binding']=old_cancel.get('owned_target_binding')
  result['old']['keymap_after_release']={k:down(observer,observer.keysym_to_keycode(XK.string_to_keysym(k))) for k in ('a','b')}
  result['timing_ns']['independent_keymap_readback']=time.monotonic_ns()
  # Ensure exact old call terminal state using the original call id, even if cancel has its own shape.
  old_terminal=await call(old_server,'interface_results',{'call_id':cid,'include_image':False});
  if old_terminal.get('status')=='pending': old_terminal=await terminal(old_server,old_terminal,5)
  result['old']['terminal']=old_terminal
  try: result['old']['close']=await call(old_server,'interface_close',{}); result['old']['exitcode_after_close']=old.poll()
  except Exception as e: result['old']['close_error']=repr(e)
  result['timing_ns']['old_delay_horizon_start']=time.monotonic_ns()
  result['old']['keymap_after_horizon']={k:down(observer,observer.keysym_to_keycode(XK.string_to_keysym(k))) for k in ('a','b')}
  final_old=json.loads((ROOT/'old.json').read_text())['events']; result['old']['events_after_horizon']=final_old; result['old']['effect_after_horizon']=len([e for e in final_old if e['type']=='press'])
  fresh,fi=spawn('fresh'); result['timing_ns']['fresh_ready']=time.monotonic_ns(); result['recovery']['fresh_pid']=fi['pid']; result['recovery']['fresh_window']=fi['window']; result['recovery']['fresh_distinct_pid']=fi['pid']!=oi['pid']; result['recovery']['fresh_distinct_window']=fi['window']!=oi['window']
  result['recovery']['old_generation']=src.get('pointer_binding',{}).get('process_generation')
  fresh_root=ROOT/'mcp-fresh'; fresh_server=create_server({'app':fi['window']},fresh_root,session_mode='guarded-x11',guarded_process_identity=True,guarded_query_worker=True,guarded_window_lifecycle=True,guarded_owned_process=True,guarded_prestarted_cancel_supervisor=True); fresh_obs=await call(fresh_server,'interface_guarded_observe',{}); result['recovery']['observe']=fresh_obs
  if fresh_obs.get('status')!='observed': raise RuntimeError('fresh public observe failed')
  fresh_src=fresh_obs['source']; new_gen=fresh_src.get('pointer_binding',{}).get('process_generation'); result['recovery']['fresh_generation']=new_gen; result['recovery']['generation_distinct']=new_gen!=result['recovery']['old_generation']
  stale=await call(fresh_server,'interface_guarded_input',{'alias':'field','offset':minted['offset'],'interaction':'keyboard','observe_after':False,'wait_for_result_ms':0,'tail':[{'op':'key_chord','keys':['b']}]}); result['recovery']['stale_attempt']=stale
  if stale.get('status')=='pending': stale=await terminal(fresh_server,stale,4)
  result['recovery']['stale_terminal']=stale
  fresh_mint=await call(fresh_server,'interface_guarded_mint',{'alias':'recovered','source_sequence':fresh_src['sequence'],'point':[88,88],'region_size':[24,24]}); result['recovery']['mint']=fresh_mint
  if fresh_mint.get('status')!='minted': raise RuntimeError('fresh mint failed')
  result['timing_ns']['fresh_input_started']=time.monotonic_ns()
  fresh_action=await call(fresh_server,'interface_guarded_input',{'alias':'recovered','offset':fresh_mint['offset'],'interaction':'keyboard','observe_after':False,'wait_for_result_ms':0,'tail':[{'op':'key_chord','keys':['b']}]}); result['recovery']['action_initial']=fresh_action
  fresh_terminal=await terminal(fresh_server,fresh_action,5); result['recovery']['terminal']=fresh_terminal; result['timing_ns']['fresh_terminal']=time.monotonic_ns()
  await asyncio.sleep(.2); ev=json.loads((ROOT/'fresh.json').read_text())['events']; result['recovery']['events_before_horizon']=ev; result['recovery']['B_press_before_horizon']=len([e for e in ev if e['type']=='press' and e['detail']==fi['keycode']]); result['recovery']['keymap_after_action']={k:down(observer,observer.keysym_to_keycode(XK.string_to_keysym(k))) for k in ('a','b')}
  result['timing_ns']['fresh_horizon_start']=time.monotonic_ns(); await asyncio.sleep(8.5); result['timing_ns']['fresh_horizon_end']=time.monotonic_ns(); ev=json.loads((ROOT/'fresh.json').read_text())['events']; result['recovery']['events_after_horizon']=ev; result['recovery']['B_press_after_horizon']=len([e for e in ev if e['type']=='press' and e['detail']==fi['keycode']]); result['recovery']['keymap_after_horizon']={k:down(observer,observer.keysym_to_keycode(XK.string_to_keysym(k))) for k in ('a','b')}
  result['old']['keymap_after_horizon']={k:down(observer,observer.keysym_to_keycode(XK.string_to_keysym(k))) for k in ('a','b')}
  result['old']['events_after_horizon']=json.loads((ROOT/'old.json').read_text())['events']
  result['old']['effect_after_horizon']=len([e for e in result['old']['events_after_horizon'] if e['type']=='press'])
  result['recovery']['release_receipts']=fresh_terminal.get('result',{}).get('execution',{}).get('releases',[])
  result['recovery']['runtime_task_success']=fresh_terminal.get('task_success')
  result['checks']={'runtime_release_verified':(result['old'].get('close',{}).get('owner_release_attempt') or {}).get('status')=='readback_verified','close_target_receipt':(result['old'].get('close',{}).get('owned_target_retirement') or {}).get('process_exit_verified') is True and (result['old'].get('close',{}).get('owned_target_retirement') or {}).get('status')=='retired','old_unknown':old_terminal.get('cleanup_status')=='UNKNOWN' and old_terminal.get('task_success') is None and old_terminal.get('replay_allowed') is False,'target_lifecycle_as_assigned':(result['old']['alive_before_resume'] if MODE=='control' else result['old']['retired_exitcode'] is not None and result['timing_ns']['old_process_retired']<result['timing_ns']['resume_requested']),'runtime_target_receipt_verified':(result['old']['target_retirement'] is None if MODE=='control' else (result['old']['target_retirement'] or {}).get('status')=='retired' and (result['old']['target_retirement'] or {}).get('target_identity_verified') is True and (result['old']['target_retirement'] or {}).get('process_exit_verified') is True),'horizon_elapsed':result['timing_ns']['fresh_horizon_end']-result['timing_ns']['fresh_horizon_start']>=8500000000,'old_keys_up_after_release_and_horizon':not any(result['old']['keymap_after_release'].values()) and not any(result['old']['keymap_after_horizon'].values()),'stale_alias_refused_before_dispatch':stale.get('status')=='refused' and stale.get('result',{}).get('input_dispatched') is False,'fresh_ready_before_delayed_b_deadline':result['timing_ns']['fresh_ready'] < result['old']['delayed_marker']['flushed_ns']+8000000000,'fresh_no_old_a_through_horizon':not any(e['type']=='press' and e['detail']==oi['keycode'] for e in result['recovery']['events_after_horizon']),'fresh_identity_distinct':result['recovery']['fresh_distinct_pid'] and result['recovery']['fresh_distinct_window'] and result['recovery']['generation_distinct'],'fresh_B_exactly_once_through_horizon':result['recovery']['B_press_before_horizon']==result['recovery']['B_press_after_horizon']==1,'fresh_keys_up_through_horizon':not any(result['recovery']['keymap_after_action'].values()) and not any(result['recovery']['keymap_after_horizon'].values()),'fresh_release_receipt_verified':bool(result['recovery']['release_receipts']) and result['recovery']['release_receipts'][-1].get('verified') is True}
  initial_retirement=result['old'].get('target_retirement') or {}
  close_retirement=(result['old'].get('close') or {}).get('owned_target_retirement') or {}
  result['checks']['target_lifecycle_as_assigned']=(result['old']['alive_before_resume'] and result['old']['exitcode_after_close'] is not None)
  result['checks']['runtime_target_receipt_verified']=(initial_retirement.get('status')=='unknown' and initial_retirement.get('reason')=='pidfd_signal_failed' and initial_retirement.get('process_exit_verified') is False and result['old']['injected_signal_failure_count']==1)
  result['checks']['close_retry_preserves_initial_receipt']=(close_retirement.get('status')=='retired' and close_retirement.get('process_exit_verified') is True and close_retirement.get('previous_attempt',{}).get('reason')=='pidfd_signal_failed')
  iq=(result['old'].get('target_binding') or {}).get('identity_query') or {}
  result['checks']['prestarted_identity_receipt']=(iq.get('status')=='observed' and iq.get('worker_retired') is True and iq.get('worker_exitcode')==0 and iq.get('session_id')==result['old']['observe']['session']['session_id'])
  result['status']='PASS' if all(result['checks'].values()) else 'FAIL'
 except BaseException as e: result.update(status='FAIL',error_type=type(e).__name__,error=str(e))
 finally:
  for server in (fresh_server,old_server):
   if server is not None:
    try: await asyncio.wait_for(server.call_tool('interface_close',{}),3)
    except BaseException: pass
  for p in (old,fresh):
   if p is not None and p.poll() is None: p.terminate();
   if p is not None:
    try:p.wait(timeout=1)
    except Exception: p.kill();p.wait()
  if observer is not None:
   try: observer.close()
   except Exception: pass
  if xvfb is not None and xvfb.poll() is None:
   try:
    if proc_state(xvfb.pid) in ('T','t'): os.kill(xvfb.pid,signal.SIGCONT)
   except Exception: pass
   xvfb.terminate()
   try:xvfb.wait(timeout=1)
   except subprocess.TimeoutExpired:xvfb.kill();xvfb.wait()
  result['cleanup']={'xvfb_exitcode':xvfb.returncode if xvfb else None,'old_exitcode':old.returncode if old else None,'fresh_exitcode':fresh.returncode if fresh else None}
  (ROOT/'result.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
  xlog.close()
 print(json.dumps(result,sort_keys=True))
 return 0 if result.get('status')=='PASS' else 1
if __name__ == '__main__':
 raise SystemExit(asyncio.run(main()))