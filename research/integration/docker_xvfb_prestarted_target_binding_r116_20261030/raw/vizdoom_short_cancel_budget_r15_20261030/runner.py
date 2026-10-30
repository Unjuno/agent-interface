import asyncio,json,os,signal,subprocess,time,traceback
from pathlib import Path
from Xlib import XK,display,error
import vizdoom as vd
from runtime.cli_v1.mcp_server import create_server
from runtime.cli_v1.test_mcp_xvfb_blocked_release_integration import _metadata,_xvfb_blocking_owner_factory
from runtime.guarded_x11_v1.owned_target_process import OwnedTargetProcess
ROOT=Path('/evidence')
def state(pid):
 s=Path('/proc',str(pid),'stat').read_text();return s[s.rfind(')')+1:].split()[0]
def down(d,k):
 code=d.keysym_to_keycode(XK.string_to_keysym(k));m=d.query_keymap();return bool(m[code//8] & (1<<(code%8)))
async def call(s,name,args):return _metadata(await asyncio.wait_for(s.call_tool(name,args),8))
async def wait_file(path,timeout):
 end=time.monotonic()+timeout
 while time.monotonic()<end:
  if path.exists():return json.loads(path.read_text())
  await asyncio.sleep(.005)
 raise TimeoutError(str(path))
async def main():
 r={'status':'RUNNING','task_success':None,'no_model_calls':True,'times':{},'checks':{}};x=None;d=None;owner=None;server=None
 try:
  os.environ['DISPLAY']=':91';os.environ['XDG_CACHE_HOME']='/tmp/cache'
  x=subprocess.Popen(['Xvfb',':91','-screen','0','1280x1024x24','-cc','4','-nolisten','tcp'],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
  for _ in range(150):
   try:d=display.Display(':91');break
   except Exception:await asyncio.sleep(.02)
  if d is None:raise RuntimeError('Xvfb unavailable')
  cfg=Path('/tmp/direct-cancel.ini');cfg.write_text('[Doom.Bindings]\nw=+forward\n')
  pkg=Path(vd.__file__).resolve().parent;args=[str(pkg/'vizdoom'),'-iwad',str(pkg/'freedoom2.wad'),'-config',str(cfg),'-warp','1','-window','-nosound','-nojoy','-width','640','-height','480']
  owner=OwnedTargetProcess.launch(args,disposable=True,env=os.environ.copy());r['target_pid']=owner.pid
  windows=[]
  for _ in range(250):
   if not owner.running:break
   windows=[]
   for w in d.screen().root.query_tree().children:
    try:
     title=w.get_wm_name()
     if title and 'DOOM' in title.upper() and w.get_attributes().map_state==2:windows.append(w)
    except error.BadWindow:
     r['transient_window_disappearances']=r.get('transient_window_disappearances',0)+1
   if len(windows)==1:break
   await asyncio.sleep(.02)
  if len(windows)!=1:raise RuntimeError('no unique mapped game window')
  w=windows[0];r['xid']=w.id;await asyncio.sleep(2)
  server=create_server({'app':w.id},ROOT/'mcp',session_mode='guarded-x11',guarded_process_identity=True,guarded_query_worker=True,guarded_window_lifecycle=True,guarded_owned_process=True,guarded_prestarted_cancel_supervisor=True,_guarded_cancel_transaction_timeout_s=0.45,_guarded_owner_factory=_xvfb_blocking_owner_factory,_guarded_owned_target_process=owner,_guarded_prestarted_target_identity=True)
  obs=await call(server,'interface_guarded_observe',{});r['observe']=obs
  if obs.get('status')!='observed':raise RuntimeError('observe failed')
  source=obs['source'];g=source['pointer_binding']['geometry'];point=[g[0]+44,g[1]+g[3]-54]
  minted=await call(server,'interface_guarded_mint',{'alias':'field','source_sequence':source['sequence'],'point':point,'region_size':[24,38]});r['mint']=minted
  if minted.get('status')!='minted':raise RuntimeError('mint failed')
  action=await call(server,'interface_guarded_input',{'alias':'field','offset':minted['offset'],'interaction':'keyboard','observe_after':False,'tail':[{'op':'key_chord','keys':['w']}],'wait_for_result_ms':0});r['action']=action
  if action.get('status')!='pending':raise RuntimeError('action not pending')
  cid=action['call_id'];r['marker']=await wait_file(ROOT/'mcp/xvfb-delayed-request-queued.json',4);r['sync_marker']=await wait_file(ROOT/'mcp/xvfb-owner-sync-entered.json',4)
  r['w_down_before_stop']=down(d,'w');os.kill(x.pid,signal.SIGSTOP);r['times']['stop_requested']=time.monotonic_ns()
  end=time.monotonic()+2
  while time.monotonic()<end and state(x.pid) not in ('T','t'):await asyncio.sleep(.005)
  if state(x.pid) not in ('T','t'):raise RuntimeError('Xvfb did not stop')
  r['times']['stopped']=time.monotonic_ns();signals=[];original_pidfd_signal=signal.pidfd_send_signal
  def logged_pidfd_signal(fd,sig,*args,**kwargs):
   if fd==owner._pidfd:signals.append({'signal':int(sig),'ns':time.monotonic_ns()})
   return original_pidfd_signal(fd,sig,*args,**kwargs)
  signal.pidfd_send_signal=logged_pidfd_signal
  r['cancel']=await call(server,'interface_guarded_cancel',{'call_id':cid});r['times']['cancel_returned']=time.monotonic_ns()
  r['times']['transaction_deadline']=r['cancel']['cancellation']['transaction_deadline_monotonic_ns']
  wait_s=max(0,(r['times']['transaction_deadline']+50_000_000-time.monotonic_ns())/1e9)
  await asyncio.sleep(wait_s)
  r['target_exit_before_resume']=owner._process.poll();r['times']['target_exit_observed']=time.monotonic_ns()
  remaining=.650-(time.monotonic_ns()-r['times']['stopped'])/1e9
  if remaining>0:await asyncio.sleep(remaining)
  os.kill(x.pid,signal.SIGCONT);r['times']['resume']=time.monotonic_ns()
  cancel=await call(server,'interface_guarded_cancel',{'call_id':cid});end=time.monotonic()+5
  while cancel.get('status')=='pending' and time.monotonic()<end:
   await asyncio.sleep(.01);cancel=await call(server,'interface_guarded_cancel',{'call_id':cid})
  r['cancel_terminal']=cancel; r['old_terminal']=await call(server,'interface_results',{'call_id':cid,'include_image':False})
  r['times']['close_started']=time.monotonic_ns();r['close']=await call(server,'interface_close',{});r['keys_after_close']={k:down(d,k) for k in ('w','b')}
  outcome=(cancel.get('result') or cancel);target=outcome.get('owned_target_retirement') or {};release=(r['close'].get('owner_release_attempt') or {})
  r['target_signal_log']=signals
  cancel_signals=[entry for entry in signals if entry['ns']<r['times']['close_started']]
  r['checks']={'observed_owned_binding':(outcome.get('owned_target_binding') or {}).get('status')=='bound','w_down_before_stop':r['w_down_before_stop'] is True,'original_unknown_no_replay':r['old_terminal'].get('cleanup_status')=='UNKNOWN' and r['old_terminal'].get('replay_allowed') is False and r['old_terminal'].get('task_success') is None,'signal_log_before_reserved_deadline':all(entry['ns']<r['times']['transaction_deadline']-250000000 for entry in cancel_signals),'stop_at_least_650ms':r['times']['resume']-r['times']['stopped']>=650000000,'w_b_up_after_close':not any(r['keys_after_close'].values()),'close_preserves_unknown':r['close'].get('cleanup_status')=='UNKNOWN' and r['close'].get('replay_allowed') is False}
  r['status']='PASS' if all(r['checks'].values()) else 'FAIL'
 except BaseException as e:r.update(status='FAIL',error_type=type(e).__name__,error=str(e),traceback=traceback.format_exc())
 finally:
  if x is not None and x.poll() is None:
   try:
    if state(x.pid) in ('T','t'):os.kill(x.pid,signal.SIGCONT)
   except Exception:pass
  if server is not None:
   try:await asyncio.wait_for(server.call_tool('interface_close',{}),3)
   except BaseException:pass
  if owner is not None:
   if owner.running:
    try:signal.pidfd_send_signal(owner._pidfd,signal.SIGKILL);owner._process.wait(timeout=2)
    except Exception as e:r['cleanup_target_error']=repr(e)
   try:owner.close()
   except Exception as e:r['cleanup_handle_error']=repr(e)
  if d is not None:d.close()
  if x is not None:
   if x.poll() is None:x.terminate()
   try:x.wait(timeout=3)
   except subprocess.TimeoutExpired:x.kill();x.wait()
   r['xvfb_exitcode']=x.returncode
  (ROOT/'result.json').write_text(json.dumps(r,indent=2)+'\n')
 print(json.dumps(r));return 0 if r['status']=='PASS' else 1
if __name__=='__main__':raise SystemExit(asyncio.run(main()))
