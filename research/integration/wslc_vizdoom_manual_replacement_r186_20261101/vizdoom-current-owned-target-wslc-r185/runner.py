import asyncio,json,os,signal,subprocess,time,traceback
from pathlib import Path
from Xlib import X,XK,display,error
from Xlib.ext import xtest
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
  try:return json.loads(path.read_text())
  except FileNotFoundError:pass
  await asyncio.sleep(.005)
 raise TimeoutError(str(path))
async def main():
 r={'status':'RUNNING','task_success':None,'no_model_calls':True,'times':{},'checks':{}};x=None;d=None;owner=None;server=None;new_actor=None
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
  r['times']['stopped']=time.monotonic_ns()
  cancel=await call(server,'interface_guarded_cancel',{'call_id':cid});end=time.monotonic()+4
  while cancel.get('status')=='pending' and time.monotonic()<end:
   await asyncio.sleep(.01);cancel=await call(server,'interface_guarded_cancel',{'call_id':cid})
  r['cancel_terminal']=cancel;r['target_exit_before_resume']=owner._process.poll();r['xvfb_state_before_resume']=state(x.pid)
  os.kill(x.pid,signal.SIGCONT);r['times']['resume']=time.monotonic_ns()
  r['old_terminal']=await call(server,'interface_results',{'call_id':cid,'include_image':False})
  r['old_w_before_new']=down(d,'w');new_actor=display.Display(':91');new_w=new_actor.keysym_to_keycode(XK.string_to_keysym('w'))
  xtest.fake_input(new_actor,X.KeyRelease,detail=new_w);new_actor.sync();xtest.fake_input(new_actor,X.KeyPress,detail=new_w);new_actor.sync();r['new_w_before_close']=down(new_actor,'w')
  r['close']=await call(server,'interface_close',{});r['new_w_after_close']=down(new_actor,'w')
  xtest.fake_input(new_actor,X.KeyRelease,detail=new_w);new_actor.sync();r['new_w_after_actor_release']=down(new_actor,'w')
  outcome=cancel.get('result') or cancel;previous=outcome.get('owner_release_attempt') or {}
  r['checks']={'w_down_before_stop':r['w_down_before_stop'] is True,'target_exited_before_resume':r['target_exit_before_resume'] is not None,'xvfb_stopped':r['xvfb_state_before_resume'] in ('T','t'),'cancel_terminal':cancel.get('status')!='pending','prior_release_unconfirmed':previous.get('status')!='readback_verified','old_unknown_no_replay':r['old_terminal'].get('cleanup_status')=='UNKNOWN' and r['old_terminal'].get('replay_allowed') is False,'new_w_held_before_close':r['new_w_before_close'] is True,'new_w_still_held_after_close':r['new_w_after_close'] is True,'actor_release_up':r['new_w_after_actor_release'] is False,'close_unknown_no_replay':r['close'].get('cleanup_status')=='UNKNOWN' and r['close'].get('replay_allowed') is False}
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
  if new_actor is not None:new_actor.close()
  if d is not None:d.close()
  if x is not None:
   if x.poll() is None:x.terminate()
   try:x.wait(timeout=3)
   except subprocess.TimeoutExpired:x.kill();x.wait()
   r['xvfb_exitcode']=x.returncode
  (ROOT/'result.json').write_text(json.dumps(r,indent=2)+'\n')
 print(json.dumps(r));return 0 if r['status']=='PASS' else 1
if __name__=='__main__':raise SystemExit(asyncio.run(main()))
