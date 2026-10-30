import asyncio,json,math,os,secrets,signal,subprocess,time,tempfile,threading
import vizdoom as vd
from runtime.cli_v1.mcp_server import create_server
from runtime.cli_v1.test_mcp_xvfb_blocked_release_integration import _metadata,_xvfb_blocking_owner_factory
from runtime.guarded_x11_v1.owned_target_process import OwnedTargetProcess
from pathlib import Path
from Xlib import X,XK,display
from Xlib.ext import xtest,record
from Xlib.protocol import rq
E=Path('/evidence')
def state(pid):
 s=Path('/proc',str(pid),'stat').read_text();return s[s.rfind(')')+1:].split()[0]
def start(auth):
 p=subprocess.Popen(['Xvfb',':93','-screen','0','640x480x24','-nolisten','tcp','-nolisten','unix','-auth',str(auth)],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL);fd=os.pidfd_open(p.pid,0);os.environ['XAUTHORITY']=str(auth);end=time.monotonic()+4
 while time.monotonic()<end:
  if p.poll() is not None:raise RuntimeError('Xvfb exited before ready')
  try:return p,fd,display.Display(':93')
  except Exception:time.sleep(.03)
 raise RuntimeError('Xvfb unavailable')
async def run():
 ps=[];fds=[];ds=[];rc=None;rd=None;ctx=None;thread=None;game=None;server=None;old_target=None;old_server=None;r={'checks':{},'times':{}}
 try:
  with tempfile.TemporaryDirectory() as tmp:
   os.chdir(tmp)  # ViZDoom writes ./_vizdoom; keep source mount read-only.
   a=Path(tmp)/'old';b=Path(tmp)/'new';a.touch();b.touch()
   for f in (a,b):subprocess.run(['xauth','-f',str(f),'add',':93','MIT-MAGIC-COOKIE-1',secrets.token_hex(16)],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,check=True)
   oldp,oldfd,old=start(a);ps.append(oldp);fds.append(oldfd);ds.append(old);os.environ['DISPLAY']=':93';os.environ['XDG_CACHE_HOME']='/tmp/cache'
   pkg=Path(vd.__file__).resolve().parent;cfgold=Path(tmp)/'old.ini';cfgold.write_text('[Doom.Bindings]\nw=+forward\n');old_args=[str(pkg/'vizdoom'),'-iwad',str(pkg/'freedoom2.wad'),'-config',str(cfgold),'-warp','1','-window','-nosound','-nojoy','-width','640','-height','480'];old_target=OwnedTargetProcess.launch(old_args,disposable=True,env=os.environ.copy());ow=None
   for _ in range(250):
    if not old_target.running:break
    for candidate in old.screen().root.query_tree().children:
     try:
      title=candidate.get_wm_name()
      if title and 'DOOM' in title.upper() and candidate.get_attributes().map_state==2:ow=candidate;break
     except Exception:pass
    if ow is not None:break
    await asyncio.sleep(.02)
   if ow is None:raise RuntimeError('old game window unavailable')
   await asyncio.sleep(1);old_server=create_server({'app':ow.id},E/'old-mcp',display_name=':93',session_mode='guarded-x11',guarded_process_identity=True,guarded_query_worker=True,guarded_window_lifecycle=True,guarded_owned_process=True,guarded_prestarted_cancel_supervisor=True,_guarded_cancel_transaction_timeout_s=.45,_guarded_owner_factory=_xvfb_blocking_owner_factory,_guarded_owned_target_process=old_target,_guarded_prestarted_target_identity=True)
   async def oldcall(name,args):return _metadata(await asyncio.wait_for(old_server.call_tool(name,args),10))
   obs=await oldcall('interface_guarded_observe',{});g=obs['source']['pointer_binding']['geometry'];mint=await oldcall('interface_guarded_mint',{'alias':'field','source_sequence':obs['source']['sequence'],'point':[g[0]+44,g[1]+g[3]-54],'region_size':[24,38]});action=await oldcall('interface_guarded_input',{'alias':'field','offset':mint['offset'],'interaction':'keyboard','observe_after':False,'tail':[{'op':'key_chord','keys':['w']}],'wait_for_result_ms':0});r['old_action']=action
   if action.get('status')!='pending':raise RuntimeError('old input not pending')
   async def marker(path):
    end=time.monotonic()+4
    while time.monotonic()<end:
     try:return json.loads(path.read_text())
     except FileNotFoundError:pass
     await asyncio.sleep(.005)
    raise TimeoutError(str(path))
   queued=await marker(E/'old-mcp/xvfb-delayed-request-queued.json');await marker(E/'old-mcp/xvfb-owner-sync-entered.json');r['old_marker']=queued;r['times']['old_queued']=queued['flushed_ns'];r['old_w_down']=bool(old.query_keymap()[old.keysym_to_keycode(XK.string_to_keysym('w'))//8] & (1<<(old.keysym_to_keycode(XK.string_to_keysym('w'))%8)))
   signal.pidfd_send_signal(oldfd,signal.SIGSTOP);end=time.monotonic()+1
   while time.monotonic()<end and state(oldp.pid) not in ('T','t'):await asyncio.sleep(.005)
   stopped=state(oldp.pid) in ('T','t');cancel=await oldcall('interface_guarded_cancel',{'call_id':action['call_id']});end=time.monotonic()+3
   while cancel.get('status')=='pending' and time.monotonic()<end:
    await asyncio.sleep(.01);cancel=await oldcall('interface_guarded_cancel',{'call_id':action['call_id']})
   r['old_cancel']=cancel;r['old_target_exit_before_display_kill']=old_target._process.poll();signal.pidfd_send_signal(oldfd,signal.SIGKILL);oldp.wait(timeout=2);r['times']['old_exit']=time.monotonic_ns();r['old_terminal']=await oldcall('interface_results',{'call_id':action['call_id'],'include_image':False});r['old_close']=await oldcall('interface_close',{})
   newp,newfd,fresh=start(b);ps.append(newp);fds.append(newfd);ds.append(fresh);r['times']['fresh_started']=time.monotonic_ns()
   try:old.sync();old_error=None
   except Exception as e:old_error=type(e).__name__
   os.environ['XAUTHORITY']=str(a)
   try:unauthorized=display.Display(':93');unauthorized.close();old_auth_denied=False;auth_error=None
   except Exception as e:old_auth_denied=True;auth_error=type(e).__name__
   os.environ['XAUTHORITY']=str(b);rc=display.Display(':93');rd=display.Display(':93');events=[];errors=[];ready=threading.Event();ctx=rd.record_create_context(0,[record.AllClients],[{'core_requests':(0,0),'core_replies':(0,0),'ext_requests':(0,0,0,0),'ext_replies':(0,0,0,0),'delivered_events':(0,0),'device_events':(X.KeyPress,X.KeyRelease),'errors':(0,0),'client_started':False,'client_died':False}])
   def callback(reply):
    if reply.category==record.StartOfData:ready.set();return
    if reply.category!=record.FromServer or reply.client_swapped:return
    data=reply.data
    while data:
     event,data=rq.EventField(None).parse_binary_value(data,rd.display,None,None)
     if event.type in (X.KeyPress,X.KeyRelease):events.append({'type':event.type,'detail':event.detail,'ns':time.monotonic_ns()})
   def run_rec():
    try:rd.record_enable_context(ctx,callback)
    except BaseException as e:errors.append(type(e).__name__);ready.set()
   thread=threading.Thread(target=run_rec,daemon=True);thread.start()
   if not ready.wait(3) or errors:raise RuntimeError('record unavailable')
   r['times']['recorder_ready']=time.monotonic_ns();os.environ['DISPLAY']=':93';os.environ['SDL_VIDEODRIVER']='x11';os.environ['XDG_CACHE_HOME']='/tmp/cache'
   cfg=Path(tmp)/'doom.ini';cfg.write_text('[Doom.Bindings]\nw=+forward\n');pkg=Path(vd.__file__).resolve().parent;game=vd.DoomGame();game.set_doom_game_path(str(pkg/'freedoom2.wad'));game.set_doom_scenario_path('');game.set_doom_map('MAP01');game.set_doom_config_path(str(cfg));game.set_mode(vd.Mode.ASYNC_SPECTATOR);game.set_ticrate(35);game.set_seed(990619);game.set_doom_skill(1);game.add_game_args('-nomonsters');game.set_episode_timeout(2100);game.set_window_visible(True);game.set_console_enabled(False);game.set_sound_enabled(False);game.set_screen_resolution(vd.ScreenResolution.RES_640X480);game.set_available_buttons([vd.Button.MOVE_FORWARD]);game.set_available_game_variables([vd.GameVariable.POSITION_X,vd.GameVariable.POSITION_Y]);game.init()
   window=None
   for _ in range(250):
    for candidate in fresh.screen().root.query_tree().children:
     try:
      title=candidate.get_wm_name()
      if title and 'DOOM' in title.upper() and candidate.get_attributes().map_state==2:window=candidate;break
     except Exception:pass
    if window is not None:break
    time.sleep(.02)
   if window is None:raise RuntimeError('game window unavailable')
   r['times']['fresh_game_ready']=time.monotonic_ns();window.set_input_focus(X.RevertToParent,X.CurrentTime);fresh.sync();time.sleep(.5)
   async def action():
    nonlocal server
    server=create_server({'app':window.id},E/'mcp',display_name=':93',session_mode='guarded-x11',guarded_process_identity=True,guarded_query_worker=True,guarded_window_lifecycle=True,guarded_owned_process=True)
    async def call(n,a):return _metadata(await asyncio.wait_for(server.call_tool(n,a),15))
    try:
     obs=await call('interface_guarded_observe',{});g=obs['source']['pointer_binding']['geometry'];mint=await call('interface_guarded_mint',{'alias':'fresh','source_sequence':obs['source']['sequence'],'point':[g[0]+44,g[1]+g[3]-54],'region_size':[24,38]})
     game.advance_action(1,True)
     def pos():return [game.get_game_variable(vd.GameVariable.POSITION_X),game.get_game_variable(vd.GameVariable.POSITION_Y)]
     r['coast_before']=pos();await asyncio.sleep(.6);game.advance_action(1,True);r['coast_after']=pos();r['coast_displacement']=math.dist(r['coast_before'],r['coast_after']);r['times']['action_started']=time.monotonic_ns()
     r['action']=await call('interface_guarded_input',{'alias':'fresh','offset':mint['offset'],'interaction':'keyboard','observe_after':False,'tail':[{'op':'key_state','key':'w','down':True},{'op':'wait_update','timeout_ms':600},{'op':'key_state','key':'w','down':False}],'wait_for_result_ms':10000});await asyncio.sleep(.3);game.advance_action(1,True);r['move_after']=pos();r['move_displacement']=math.dist(r['coast_after'],r['move_after'])
    finally:r['fresh_close']=await call('interface_close',{})
   await action();w=fresh.keysym_to_keycode(XK.string_to_keysym('w'))
   time.sleep(max(0,(r['times']['old_queued']+9_000_000_000-time.monotonic_ns())/1e9));r['times']['horizon_end']=time.monotonic_ns();nb=fresh.keysym_to_keycode(XK.string_to_keysym('b'));xtest.fake_input(fresh,X.KeyPress,detail=nb);xtest.fake_input(fresh,X.KeyRelease,detail=nb);fresh.sync();time.sleep(.3);rc.record_disable_context(ctx);rc.sync();thread.join(timeout=2)
   r['events']=events;r['checks']={'old_w_down':r['old_w_down'],'old_target_exited':r['old_target_exit_before_display_kill'] is not None,'old_unknown_no_replay':r['old_terminal'].get('cleanup_status')=='UNKNOWN' and r['old_terminal'].get('replay_allowed') is False,'old_stopped':stopped,'old_exited':oldp.returncode is not None,'distinct_pid':oldp.pid!=newp.pid,'new_same_display_before_delay':r['times']['fresh_started']<r['times']['old_queued']+8_000_000_000,'old_connection_closed':old_error=='ConnectionClosedError','old_cookie_denied':old_auth_denied and auth_error=='DisplayConnectionError','recorder_covers_old_delay':r['times']['recorder_ready']<r['times']['old_queued']+8_000_000_000<r['times']['horizon_end'] and not errors and not thread.is_alive(),'new_w_press_release':all(any(e['type']==t and e['detail']==w and e['ns']>=r['times']['action_started'] and e['ns']<r['times']['horizon_end'] for e in events) for t in (X.KeyPress,X.KeyRelease)),'fresh_game_ready_before_delay':r['times']['fresh_game_ready']<r['times']['old_queued']+8_000_000_000,'coast_lt_1':r['coast_displacement']<1,'move_gt_5':r['move_displacement']>5,'mcp_action_completed':r['action'].get('status')=='completed' and r['action'].get('result',{}).get('status')=='completed','fresh_close_verified':r['fresh_close'].get('verified') is True,'no_b_before_horizon':not any(e['type']==X.KeyPress and e['detail']==nb and e['ns']<r['times']['horizon_end'] for e in events),'b_positive_after':any(e['type']==X.KeyPress and e['detail']==nb and e['ns']>=r['times']['horizon_end'] for e in events)};r.update(status='PASS' if all(r['checks'].values()) else 'FAIL',old_error=old_error,old_auth_error=auth_error)
 except BaseException as e:r.update(status='FAIL',error_type=type(e).__name__,error=str(e))
 finally:
  if rc is not None and ctx is not None and thread is not None and thread.is_alive():
   try:rc.record_disable_context(ctx);rc.sync();thread.join(timeout=2)
   except Exception:pass
  if old_target is not None:
   if old_target.running:
    try:signal.pidfd_send_signal(old_target._pidfd,signal.SIGKILL);old_target._process.wait(timeout=2)
    except Exception as e:r['old_target_cleanup_error']=type(e).__name__
   try:old_target.close()
   except Exception:pass
  if game is not None:
   try:game.close()
   except Exception as e:r['game_close_error']=type(e).__name__
  for d in [rd,rc]+ds:
   if d is not None:
    try:d.close()
    except Exception:pass
  for p in ps:
   if p.poll() is None:p.terminate();p.wait(timeout=3)
  for fd in fds:os.close(fd)
 (E/'result.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r));return 0 if r['status']=='PASS' else 1
if __name__=='__main__':
 watchdog=threading.Timer(35,lambda:os._exit(124));watchdog.daemon=True;watchdog.start()
 try:raise SystemExit(asyncio.run(run()))
 finally:watchdog.cancel()
