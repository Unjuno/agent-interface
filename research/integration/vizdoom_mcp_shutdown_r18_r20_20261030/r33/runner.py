import asyncio,json,os,signal,subprocess,time,traceback,threading,sys,math
from pathlib import Path
from Xlib import X,XK,display,error
from Xlib.ext import record,xtest
from Xlib.protocol import rq
from PIL import Image,ImageChops
import vizdoom as vd
from runtime.cli_v1.mcp_server import create_server
from runtime.cli_v1.owned_target_session import OwnedTargetGuardedSessionOwner
from unittest.mock import patch
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
 r={'status':'RUNNING','task_success':None,'no_model_calls':True,'times':{},'checks':{}};x=None;d=None;owner=None;server=None;lifespan=None;shutdown=None;watchdog=None;rec_control=None;rec_display=None;rec_ctx=None;rec_thread=None;witness=None;focus_display=None;witness_xvfb=None;fresh_owner=None;fresh_game=None;fresh_server=None;fresh_rc=None;fresh_rd=None;fresh_ctx=None;fresh_rt=None
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
  captured=[];original_init=OwnedTargetGuardedSessionOwner.__init__
  def capture_owner(self,*args,**kwargs):
   original_init(self,*args,**kwargs);captured.append(self)
  with patch.object(OwnedTargetGuardedSessionOwner,'__init__',capture_owner):
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
  witness_xvfb=subprocess.Popen(['Xvfb',':92','-screen','0','800x600x24','-nolisten','tcp'],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
  for _ in range(150):
   try:focus_display=display.Display(':92');break
   except Exception:await asyncio.sleep(.02)
  if focus_display is None:raise RuntimeError('witness Xvfb unavailable')
  witness_code = """import json,os,sys,time
from Xlib import X,display
d=display.Display(os.environ['DISPLAY'])
w=d.screen().root.create_window(20,20,120,100,0,d.screen().root_depth,X.InputOutput,X.CopyFromParent,event_mask=X.KeyPressMask|X.KeyReleaseMask)
w.set_wm_name('Witness');w.map();d.sync()
open(sys.argv[1],'w').write(str(w.id))
while True:
 e=d.next_event()
 if e.type in (X.KeyPress,X.KeyRelease):
  with open(sys.argv[2],'a') as f:f.write(json.dumps({'type':e.type,'detail':e.detail,'ns':time.monotonic_ns()})+'\\n')
"""
  (ROOT/'witness.py').write_text(witness_code);witness=subprocess.Popen([sys.executable,str(ROOT/'witness.py'),str(ROOT/'witness.xid'),str(ROOT/'witness-events.jsonl')],env=dict(os.environ,DISPLAY=':92'))
  for _ in range(300):
   if (ROOT/'witness.xid').exists():break
   if witness.poll() is not None:raise RuntimeError('witness exited')
   await asyncio.sleep(.01)
  if not (ROOT/'witness.xid').exists():raise RuntimeError('witness unavailable')
  witness_xid=int((ROOT/'witness.xid').read_text());focus_display.set_input_focus(witness_xid,X.RevertToParent,X.CurrentTime);focus_display.sync();r['times']['witness_focused']=time.monotonic_ns()
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
  await asyncio.sleep(max(0,10-(time.monotonic_ns()-r['times']['stopped'])/1e9));r['shutdown_done_before_resume']=shutdown.done();r['times']['shutdown_observed']=time.monotonic_ns()
  os.kill(x.pid,signal.SIGCONT);r['times']['resume']=time.monotonic_ns()
  await asyncio.wait_for(shutdown,8);lifespan=None
  r['old_terminal']=await call(server,'interface_results',{'call_id':cid,'include_image':False})
  close_files=list((ROOT/'mcp').glob('session-*-close.json'))
  r['close']=json.loads(close_files[0].read_text()) if len(close_files)==1 else None
  r['keys_after_shutdown']={k:down(d,k) for k in ('w','b')}
  if len(captured)!=1:raise RuntimeError('owner capture unavailable')
  retained=captured[0];r['times']['recheck_started']=time.monotonic_ns()
  disconnected,released=await asyncio.to_thread(retained._cleanup_after_owner_retirement,retained._retirement,disconnect_timeout_s=.75,retry_after_resume=True)
  r['recheck']={'disconnect':disconnected,'release':released};r['times']['recheck_finished']=time.monotonic_ns()
  r['keys_after_recheck']={k:down(d,k) for k in ('w','b')}
  os.environ['DISPLAY']=':92';os.environ['SDL_VIDEODRIVER']='x11'
  fresh_game=vd.DoomGame();fresh_game.set_doom_game_path(str(pkg/'freedoom2.wad'));fresh_game.set_doom_scenario_path('');fresh_game.set_doom_map('MAP01');fresh_game.set_doom_config_path(str(cfg));fresh_game.set_mode(vd.Mode.ASYNC_SPECTATOR);fresh_game.set_ticrate(35);fresh_game.set_seed(990619);fresh_game.set_doom_skill(1);fresh_game.add_game_args('-nomonsters');fresh_game.set_episode_timeout(2100);fresh_game.set_window_visible(True);fresh_game.set_console_enabled(False);fresh_game.set_sound_enabled(False);fresh_game.set_screen_resolution(vd.ScreenResolution.RES_640X480);fresh_game.set_available_buttons([vd.Button.MOVE_FORWARD]);fresh_game.set_available_game_variables([vd.GameVariable.POSITION_X,vd.GameVariable.POSITION_Y]);fresh_game.init();r['fresh']={}
  fw=None
  for _ in range(250):
   for candidate in focus_display.screen().root.query_tree().children:
    try:
     title=candidate.get_wm_name()
     if title and 'DOOM' in title.upper() and candidate.get_attributes().map_state==2:fw=candidate;break
    except error.BadWindow:pass
   if fw is not None:break
   await asyncio.sleep(.02)
  if fw is None:raise RuntimeError('fresh game window unavailable')
  r['times']['fresh_window_ready']=time.monotonic_ns();r['fresh']['xid']=fw.id
  ids=focus_display.res_query_client_ids([{'client':fw.id,'mask':2}]).ids
  if len(ids)!=1 or len(ids[0].value)!=1:raise RuntimeError('fresh XRes PID unavailable')
  r['fresh']['pid']=ids[0].value[0]
  fresh_rc=display.Display(':92');fresh_rd=display.Display(':92');fresh_events=[];fresh_errors=[];fresh_ready=threading.Event()
  fresh_ctx=fresh_rd.record_create_context(0,[record.AllClients],[{'core_requests':(0,0),'core_replies':(0,0),'ext_requests':(0,0,0,0),'ext_replies':(0,0,0,0),'delivered_events':(0,0),'device_events':(X.KeyPress,X.KeyRelease),'errors':(0,0),'client_started':False,'client_died':False}])
  def fresh_callback(reply):
   if reply.category==record.StartOfData:fresh_ready.set();return
   if reply.category!=record.FromServer or reply.client_swapped:return
   data=reply.data
   while data:
    event,data=rq.EventField(None).parse_binary_value(data,fresh_rd.display,None,None)
    if event.type in (X.KeyPress,X.KeyRelease):fresh_events.append({'type':event.type,'detail':event.detail,'ns':time.monotonic_ns()})
  def fresh_record():
   try:fresh_rd.record_enable_context(fresh_ctx,fresh_callback)
   except BaseException as e:fresh_errors.append(repr(e));fresh_ready.set()
  fresh_rt=threading.Thread(target=fresh_record,daemon=True);fresh_rt.start()
  if not await asyncio.to_thread(fresh_ready.wait,3) or fresh_errors:raise RuntimeError('fresh recorder unavailable')
  r['times']['fresh_recorder_ready']=time.monotonic_ns()
  await asyncio.sleep(1)
  fresh_server=create_server({'app':fw.id},ROOT/'fresh-mcp',display_name=':92',session_mode='guarded-x11',guarded_process_identity=True,guarded_query_worker=True,guarded_window_lifecycle=True,guarded_owned_process=True)
  fo=await call(fresh_server,'interface_guarded_observe',{});r['fresh']['observe']=fo
  if fo.get('status')!='observed':raise RuntimeError('fresh observe failed')
  stale=await call(fresh_server,'interface_guarded_input',{'alias':'field','offset':minted['offset'],'interaction':'keyboard','observe_after':False,'tail':[{'op':'key_chord','keys':['b']}],'wait_for_result_ms':10000});r['fresh']['stale']=stale
  gg=fw.get_geometry()
  def capture(path):
   raw=fw.get_image(0,0,gg.width,gg.height,X.ZPixmap,0xffffffff)
   img=Image.frombytes('RGB',(gg.width,gg.height),raw.data,'raw','BGRX');img.save(path);return img.crop((0,0,gg.width,gg.height-80))
  before=capture(ROOT/'fresh-before.png');g=fo['source']['pointer_binding']['geometry'];point=[g[0]+44,g[1]+g[3]-54]
  fm=await call(fresh_server,'interface_guarded_mint',{'alias':'fresh','source_sequence':fo['source']['sequence'],'point':point,'region_size':[24,38]});r['fresh']['mint']=fm
  if fm.get('status')!='minted':raise RuntimeError('fresh mint failed')
  fresh_game.advance_action(1,True)
  def position():return [fresh_game.get_game_variable(vd.GameVariable.POSITION_X),fresh_game.get_game_variable(vd.GameVariable.POSITION_Y)]
  r['fresh']['coast_before']=position();await asyncio.sleep(.6);fresh_game.advance_action(1,True);r['fresh']['coast_after']=position()
  r['fresh']['coast_displacement']=math.dist(r['fresh']['coast_before'],r['fresh']['coast_after'])
  r['times']['fresh_action_started']=time.monotonic_ns()
  fa=await call(fresh_server,'interface_guarded_input',{'alias':'fresh','offset':fm['offset'],'interaction':'keyboard','observe_after':False,'tail':[{'op':'key_state','key':'w','down':True},{'op':'wait_update','timeout_ms':600},{'op':'key_state','key':'w','down':False}],'wait_for_result_ms':10000});r['fresh']['action']=fa
  await asyncio.sleep(.3);fresh_game.advance_action(1,True);r['fresh']['move_after']=position();r['fresh']['move_displacement']=math.dist(r['fresh']['coast_after'],r['fresh']['move_after'])
  after=capture(ROOT/'fresh-after.png');diff=ImageChops.difference(before,after);r['fresh']['visual_changed_fraction']=sum(1 for px in diff.getdata() if max(px)>10)/(diff.width*diff.height)
  focus_display.set_input_focus(witness_xid,X.RevertToParent,X.CurrentTime);focus_display.sync()
  end_ns=max(r['marker']['flushed_ns']+9_000_000_000,r['times']['fresh_recorder_ready']+2_000_000_000)
  await asyncio.sleep(max(0,(end_ns-time.monotonic_ns())/1e9))
  r['times']['horizon_end']=time.monotonic_ns();bcode=d.keysym_to_keycode(XK.string_to_keysym('b'))
  xtest.fake_input(d,X.KeyPress,detail=bcode);xtest.fake_input(d,X.KeyRelease,detail=bcode);d.sync()
  fresh_bcode=focus_display.keysym_to_keycode(XK.string_to_keysym('b'));xtest.fake_input(focus_display,X.KeyPress,detail=fresh_bcode);xtest.fake_input(focus_display,X.KeyRelease,detail=fresh_bcode);focus_display.sync()
  r['times']['positive_control_sent']=time.monotonic_ns();wcode=focus_display.keysym_to_keycode(XK.string_to_keysym('w'));xtest.fake_input(focus_display,X.KeyPress,detail=wcode);xtest.fake_input(focus_display,X.KeyRelease,detail=wcode);focus_display.sync();await asyncio.sleep(.3)
  r['witness_events']=[json.loads(line) for line in (ROOT/'witness-events.jsonl').read_text().splitlines()] if (ROOT/'witness-events.jsonl').exists() else []
  rec_control.record_disable_context(rec_ctx);rec_control.sync();rec_thread.join(timeout=2)
  fresh_rc.record_disable_context(fresh_ctx);fresh_rc.sync();fresh_rt.join(timeout=2);r['fresh']['events']=fresh_events;r['fresh']['recorder_errors']=fresh_errors;r['fresh']['recorder_thread_alive']=fresh_rt.is_alive()
  r['events']=events;r['recorder_errors']=rec_errors;r['recorder_thread_alive']=rec_thread.is_alive();r['b_keycode']=bcode
  r['checks']={'w_down_before_stop':r['w_down_before_stop'] is True,
   'xvfb_stopped_until_target_exit':r['xvfb_state_before_resume'] in ('T','t'),
   'target_exit_before_resume':r['target_exit_before_resume'] is not None,
   'old_not_success':r['old_terminal'].get('status') != 'completed',
   'old_w_down_after_shutdown':r['keys_after_shutdown']['w'] is True,
   'w_b_up_after_recheck':not any(r['keys_after_recheck'].values()),
   'recheck_verified':r['recheck']['release'].get('status')=='readback_verified',
   'old_close_remains_unknown':r['close'].get('cleanup_status')=='UNKNOWN' and r['close'].get('replay_allowed') is False,
   'close_report_present':r['close'] is not None,
   'recorder_alive_until_horizon':not rec_errors and not rec_thread.is_alive(),
   'no_b_press_before_horizon':not any(e['type']==X.KeyPress and e['detail']==bcode and e['ns']<r['times']['horizon_end'] for e in events),
   'positive_b_recorded':any(e['type']==X.KeyPress and e['detail']==bcode and e['ns']>=r['times']['horizon_end'] for e in events),
   'witness_no_w_or_b_before_horizon':not any(e['type']==X.KeyPress and e['detail'] in (wcode,bcode) and e['ns']<r['times']['horizon_end'] for e in r['witness_events']),
   'witness_positive_w':any(e['type']==X.KeyPress and e['detail']==wcode and e['ns']>=r['times']['horizon_end'] for e in r['witness_events']),
   'fresh_distinct_process':r['fresh']['pid']!=owner.pid,
   'shutdown_finished_while_stopped':r['shutdown_done_before_resume'],
   'stop_at_least_10s':r['times']['resume']-r['times']['stopped']>=10_000_000_000,
   'stale_alias_refused':stale.get('status')=='refused' and stale.get('result',{}).get('input_dispatched') is False,
   'fresh_action_completed':fa.get('status')=='completed' and fa.get('result',{}).get('status')=='completed',
   'fresh_scene_changed':r['fresh']['visual_changed_fraction']>=.05,
   'position_coast_lt_1':r['fresh']['coast_displacement']<1,
   'position_move_gt_5':r['fresh']['move_displacement']>5,
   'fresh_recorder_covers_new_horizon':r['times']['fresh_recorder_ready']<r['times']['horizon_end'] and not fresh_errors and not fresh_rt.is_alive(),
   'fresh_no_b_before_horizon':not any(e['type']==X.KeyPress and e['detail']==fresh_bcode and e['ns']<r['times']['horizon_end'] for e in fresh_events),
   'fresh_b_positive':any(e['type']==X.KeyPress and e['detail']==fresh_bcode and e['ns']>=r['times']['horizon_end'] for e in fresh_events),
   'fresh_w_press_and_release':all(any(e['type']==t and e['detail']==wcode and e['ns']>=r['times']['fresh_action_started'] and e['ns']<r['times']['horizon_end'] for e in fresh_events) for t in (X.KeyPress,X.KeyRelease))}
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
  if fresh_rc is not None and fresh_ctx is not None and fresh_rt is not None and fresh_rt.is_alive():
   try:fresh_rc.record_disable_context(fresh_ctx);fresh_rc.sync();fresh_rt.join(timeout=2)
   except Exception:pass
  if fresh_rd is not None:fresh_rd.close()
  if fresh_rc is not None:fresh_rc.close()
  if fresh_server is not None:
   try:await asyncio.wait_for(fresh_server.call_tool('interface_close',{}),3)
   except BaseException:pass
  if fresh_game is not None:
   try:fresh_game.close()
   except Exception as e:r['fresh_game_close_error']=repr(e)
  if witness is not None and witness.poll() is None:witness.terminate();witness.wait(timeout=2)
  if focus_display is not None:focus_display.close()
  if witness_xvfb is not None and witness_xvfb.poll() is None:witness_xvfb.terminate();witness_xvfb.wait(timeout=2)
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
