import asyncio,json,os,signal,subprocess,time,traceback,threading
from pathlib import Path
from Xlib import X,XK,display,error
from Xlib.ext import record,xtest
from Xlib.protocol import rq
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
 r={'status':'RUNNING','task_success':None,'no_model_calls':True,'times':{},'checks':{}};x=None;d=None;owner=None;server=None;lifespan=None;shutdown=None;watchdog=None;rec_control=None;rec_display=None;rec_ctx=None;rec_thread=None
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
  lifespan=server.settings.lifespan(server);await lifespan.__aenter__()
  obs=await call(server,'interface_guarded_observe',{});r['observe']=obs
  if obs.get('status')!='observed':raise RuntimeError('observe failed')
  source=obs['source'];g=source['pointer_binding']['geometry'];point=[g[0]+44,g[1]+g[3]-54]
  minted=await call(server,'interface_guarded_mint',{'alias':'field','source_sequence':source['sequence'],'point':point,'region_size':[24,38]});r['mint']=minted
  if minted.get('status')!='minted':raise RuntimeError('mint failed')
  rec_control=display.Display(':91');rec_display=display.Display(':91');events=[];rec_errors=[];ready=threading.Event()
  if not rec_control.has_extension('RECORD'):raise RuntimeError('XRecord unavailable')
  rec_ctx=rec_display.record_create_context(0,[record.AllClients],[{'core_requests':(0,0),'core_replies':(0,0),'ext_requests':(0,0,0,0),'ext_replies':(0,0,0,0),'delivered_events':(0,0),'device_events':(X.KeyPress,X.KeyRelease),'errors':(0,0),'client_started':False,'client_died':False}])
  def rec_callback(reply):
   if reply.category==record.StartOfData:ready.set();return
   if reply.category!=record.FromServer or reply.client_swapped:return
   data=reply.data
   while data:
    event,data=rq.EventField(None).parse_binary_value(data,rec_display.display,None,None)
    if event.type in (X.KeyPress,X.KeyRelease):events.append({'type':event.type,'detail':event.detail,'ns':time.monotonic_ns()})
  def rec_run():
   try:rec_display.record_enable_context(rec_ctx,rec_callback)
   except BaseException as e:rec_errors.append(repr(e));ready.set()
  rec_thread=threading.Thread(target=rec_run,daemon=True);rec_thread.start()
  if not await asyncio.to_thread(ready.wait,3) or rec_errors:raise RuntimeError('recorder unavailable '+repr(rec_errors))
  r['times']['recorder_ready']=time.monotonic_ns()
  action=await call(server,'interface_guarded_input',{'alias':'field','offset':minted['offset'],'interaction':'keyboard','observe_after':False,'tail':[{'op':'key_chord','keys':['w']}],'wait_for_result_ms':0});r['action']=action
  if action.get('status')!='pending':raise RuntimeError('action not pending')
  cid=action['call_id'];r['marker']=await wait_file(ROOT/'mcp/xvfb-delayed-request-queued.json',4);r['sync_marker']=await wait_file(ROOT/'mcp/xvfb-owner-sync-entered.json',4)
  r['w_down_before_stop']=down(d,'w');os.kill(x.pid,signal.SIGSTOP);r['times']['stop_requested']=time.monotonic_ns()
  end=time.monotonic()+2
  while time.monotonic()<end and state(x.pid) not in ('T','t'):await asyncio.sleep(.005)
  if state(x.pid) not in ('T','t'):raise RuntimeError('Xvfb did not stop')
  r['times']['stopped']=time.monotonic_ns()
  def watchdog_resume():
   try:os.kill(x.pid,signal.SIGCONT)
   except ProcessLookupError:pass
  watchdog=threading.Timer(14,watchdog_resume);watchdog.daemon=True;watchdog.start()
  shutdown=asyncio.create_task(lifespan.__aexit__(None,None,None))
  end=time.monotonic()+9
  while time.monotonic()<end and owner._process.poll() is None:
   await asyncio.sleep(.01)
  r['target_exit_before_resume']=owner._process.poll();r['times']['target_exit_observed']=time.monotonic_ns()
  r['xvfb_state_before_resume']=state(x.pid)
  os.kill(x.pid,signal.SIGCONT);r['times']['resume']=time.monotonic_ns()
  await asyncio.wait_for(shutdown,8);lifespan=None
  r['old_terminal']=await call(server,'interface_results',{'call_id':cid,'include_image':False})
  close_files=list((ROOT/'mcp').glob('session-*-close.json'))
  r['close']=json.loads(close_files[0].read_text()) if len(close_files)==1 else None
  r['keys_after_shutdown']={k:down(d,k) for k in ('w','b')}
  end_ns=r['marker']['flushed_ns']+9_000_000_000
  await asyncio.sleep(max(0,(end_ns-time.monotonic_ns())/1e9))
  r['times']['horizon_end']=time.monotonic_ns();bcode=d.keysym_to_keycode(XK.string_to_keysym('b'))
  xtest.fake_input(d,X.KeyPress,detail=bcode);xtest.fake_input(d,X.KeyRelease,detail=bcode);d.sync()
  r['times']['positive_control_sent']=time.monotonic_ns();await asyncio.sleep(.3)
  rec_control.record_disable_context(rec_ctx);rec_control.sync();rec_thread.join(timeout=2)
  r['events']=events;r['recorder_errors']=rec_errors;r['recorder_thread_alive']=rec_thread.is_alive();r['b_keycode']=bcode
  r['checks']={'w_down_before_stop':r['w_down_before_stop'] is True,
   'xvfb_stopped_until_target_exit':r['xvfb_state_before_resume'] in ('T','t'),
   'target_exit_before_resume':r['target_exit_before_resume'] is not None,
   'old_not_success':r['old_terminal'].get('status') != 'completed',
   'w_b_up_after_shutdown':not any(r['keys_after_shutdown'].values()),
   'close_report_present':r['close'] is not None,
   'recorder_alive_until_horizon':not rec_errors and not rec_thread.is_alive(),
   'no_b_press_before_horizon':not any(e['type']==X.KeyPress and e['detail']==bcode and e['ns']<r['times']['horizon_end'] for e in events),
   'positive_b_recorded':any(e['type']==X.KeyPress and e['detail']==bcode and e['ns']>=r['times']['horizon_end'] for e in events)}
  r['status']='PASS' if all(r['checks'].values()) else 'FAIL'
 except BaseException as e:r.update(status='FAIL',error_type=type(e).__name__,error=str(e),traceback=traceback.format_exc())
 finally:
  if watchdog is not None:watchdog.cancel()
  if x is not None and x.poll() is None:
   try:
    if state(x.pid) in ('T','t'):os.kill(x.pid,signal.SIGCONT)
   except Exception:pass
  if rec_control is not None and rec_ctx is not None and rec_thread is not None and rec_thread.is_alive():
   try:rec_control.record_disable_context(rec_ctx);rec_control.sync();rec_thread.join(timeout=2)
   except Exception:pass
  if rec_display is not None:rec_display.close()
  if rec_control is not None:rec_control.close()
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
