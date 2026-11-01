import asyncio,json,os,signal,subprocess,threading,time,traceback
from pathlib import Path
from Xlib import X,XK,display
from Xlib.ext import record
from Xlib.protocol import rq
from PIL import Image,ImageChops
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
 r={'status':'RUNNING','task_success':None,'no_model_calls':True,'times':{},'checks':{}};x=None;d=None;owner=None;server=None;fresh_owner=None;fresh_server=None;sample_stop=None;sample_thread=None;rec_control=None;rec_display=None;rec_ctx=None;rec_thread=None
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
    title=w.get_wm_name()
    if title and 'DOOM' in title.upper() and w.get_attributes().map_state==2:windows.append(w)
   if len(windows)==1:break
   await asyncio.sleep(.02)
  if len(windows)!=1:raise RuntimeError('no unique mapped game window')
  w=windows[0];r['xid']=w.id;await asyncio.sleep(2)
  server=create_server({'app':w.id},ROOT/'mcp',session_mode='guarded-x11',guarded_process_identity=True,guarded_query_worker=True,guarded_window_lifecycle=True,guarded_owned_process=True,guarded_prestarted_cancel_supervisor=True,_guarded_owner_factory=_xvfb_blocking_owner_factory,_guarded_owned_target_process=owner,_guarded_prestarted_target_identity=True)
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
  r['times']['stopped']=time.monotonic_ns();r['cancel']=await call(server,'interface_guarded_cancel',{'call_id':cid});r['times']['cancel_returned']=time.monotonic_ns()
  end=time.monotonic()+3
  while time.monotonic()<end and owner._process.poll() is None:await asyncio.sleep(.005)
  r['target_exit_before_resume']=owner._process.poll();r['times']['target_exit_observed']=time.monotonic_ns()
  remaining=.650-(time.monotonic_ns()-r['times']['stopped'])/1e9
  if remaining>0:await asyncio.sleep(remaining)
  os.kill(x.pid,signal.SIGCONT);r['times']['resume']=time.monotonic_ns()
  cancel=await call(server,'interface_guarded_cancel',{'call_id':cid});end=time.monotonic()+5
  while cancel.get('status')=='pending' and time.monotonic()<end:
   await asyncio.sleep(.01);cancel=await call(server,'interface_guarded_cancel',{'call_id':cid})
  r['cancel_terminal']=cancel; r['old_terminal']=await call(server,'interface_results',{'call_id':cid,'include_image':False})
  r['close']=await call(server,'interface_close',{});r['keys_after_close']={k:down(d,k) for k in ('w','b')}
  outcome=(cancel.get('result') or cancel);target=outcome.get('owned_target_retirement') or {};release=(r['close'].get('owner_release_attempt') or {})
  r['checks']={'observed_owned_binding':(outcome.get('owned_target_binding') or {}).get('status')=='bound','w_down_before_stop':r['w_down_before_stop'] is True,'target_exit_before_resume':r['target_exit_before_resume'] is not None,'target_exit_verified':target.get('process_exit_verified') is True,'original_unknown_no_replay':r['old_terminal'].get('cleanup_status')=='UNKNOWN' and r['old_terminal'].get('replay_allowed') is False and r['old_terminal'].get('task_success') is None,'close_release_readback':release.get('status')=='readback_verified','w_b_up_after_close':not any(r['keys_after_close'].values()),'stop_at_least_650ms':r['times']['resume']-r['times']['stopped']>=650000000}
  fresh_owner=OwnedTargetProcess.launch(args,disposable=True,env=os.environ.copy());r['fresh']={'pid':fresh_owner.pid};fresh_windows=[]
  for _ in range(250):
   if not fresh_owner.running:break
   fresh_windows=[]
   for fw in d.screen().root.query_tree().children:
    title=fw.get_wm_name()
    if title and 'DOOM' in title.upper() and fw.get_attributes().map_state==2:fresh_windows.append(fw)
   if len(fresh_windows)==1:break
   await asyncio.sleep(.02)
  if len(fresh_windows)!=1:raise RuntimeError('fresh game window unavailable')
  fw=fresh_windows[0];r['fresh']['xid']=fw.id;r['times']['fresh_ready']=time.monotonic_ns()
  rec_control=display.Display(':91');rec_display=display.Display(':91');rec_events=[];rec_errors=[];rec_ready=threading.Event()
  if not rec_control.has_extension('RECORD'):raise RuntimeError('RECORD unavailable')
  rec_ctx=rec_display.record_create_context(0,[record.AllClients],[{'core_requests':(0,0),'core_replies':(0,0),'ext_requests':(0,0,0,0),'ext_replies':(0,0,0,0),'delivered_events':(0,0),'device_events':(X.KeyPress,X.KeyRelease),'errors':(0,0),'client_started':False,'client_died':False}])
  def rec_callback(reply):
   if reply.category==record.StartOfData:rec_ready.set();return
   if reply.category!=record.FromServer or reply.client_swapped:return
   data=reply.data
   while data:
    event,data=rq.EventField(None).parse_binary_value(data,rec_display.display,None,None)
    if event.type in (X.KeyPress,X.KeyRelease):rec_events.append({'type':event.type,'detail':event.detail,'ns':time.monotonic_ns()})
  def rec_run():
   try:rec_display.record_enable_context(rec_ctx,rec_callback)
   except BaseException as e:rec_errors.append(repr(e));rec_ready.set()
  rec_thread=threading.Thread(target=rec_run,daemon=True);rec_thread.start()
  if not await asyncio.to_thread(rec_ready.wait,3) or rec_errors:raise RuntimeError('recorder not ready '+repr(rec_errors))
  r['times']['recorder_ready']=time.monotonic_ns()
  samples=[];sample_stop=threading.Event()
  def sample_keys():
   observer=display.Display(':91')
   try:
    while not sample_stop.is_set():
     samples.append({'ns':time.monotonic_ns(),'b':down(observer,'b')});time.sleep(.01)
   finally:observer.close()
  sample_thread=threading.Thread(target=sample_keys,daemon=True);sample_thread.start();await asyncio.sleep(2)
  fresh_server=create_server({'app':fw.id},ROOT/'fresh-mcp',session_mode='guarded-x11',guarded_process_identity=True,guarded_query_worker=True,guarded_window_lifecycle=True,guarded_owned_process=True,_guarded_owned_target_process=fresh_owner)
  fo=await call(fresh_server,'interface_guarded_observe',{});r['fresh']['observe']=fo
  if fo.get('status')!='observed':raise RuntimeError('fresh game observe failed')
  stale=await call(fresh_server,'interface_guarded_input',{'alias':'field','offset':minted['offset'],'interaction':'keyboard','observe_after':False,'tail':[{'op':'key_chord','keys':['b']}],'wait_for_result_ms':10000});r['fresh']['stale_attempt']=stale
  if stale.get('status')=='pending':
   end=time.monotonic()+5
   while time.monotonic()<end:
    stale=await call(fresh_server,'interface_results',{'call_id':stale['call_id'],'include_image':False})
    if stale.get('status')!='pending':break
    await asyncio.sleep(.01)
   r['fresh']['stale_terminal']=stale

  def capture(path):
   gg=fw.get_geometry();raw=fw.get_image(0,0,gg.width,gg.height,X.ZPixmap,0xffffffff)
   if raw is None:raise RuntimeError('fresh game capture failed')
   img=Image.frombytes('RGB',(gg.width,gg.height),raw.data,'raw','BGRX');img.save(path);return img.crop((0,0,gg.width,gg.height-80))
  before=capture(ROOT/'fresh-before.png');fg=fo['source']['pointer_binding']['geometry'];point=[fg[0]+44,fg[1]+fg[3]-54]
  fm=await call(fresh_server,'interface_guarded_mint',{'alias':'fresh','source_sequence':fo['source']['sequence'],'point':point,'region_size':[24,38]});r['fresh']['mint']=fm
  if fm.get('status')!='minted':raise RuntimeError('fresh game mint failed')
  r['times']['fresh_action_started']=time.monotonic_ns()
  fa=await call(fresh_server,'interface_guarded_input',{'alias':'fresh','offset':fm['offset'],'interaction':'keyboard','observe_after':False,'tail':[{'op':'key_state','key':'w','down':True},{'op':'wait_update','timeout_ms':600},{'op':'key_state','key':'w','down':False}],'wait_for_result_ms':10000});r['fresh']['action']=fa
  if fa.get('status')=='pending':
   end=time.monotonic()+5
   while time.monotonic()<end:
    fa=await call(fresh_server,'interface_results',{'call_id':fa['call_id'],'include_image':False})
    if fa.get('status')!='pending':break
    await asyncio.sleep(.01)
   r['fresh']['action_terminal']=fa
  after=capture(ROOT/'fresh-after.png');diff=ImageChops.difference(before,after);r['fresh']['visual_changed_fraction']=sum(1 for px in diff.getdata() if max(px)>10)/(diff.width*diff.height)
  r['times']['fresh_horizon_start']=time.monotonic_ns();await asyncio.sleep(8.5);r['times']['fresh_horizon_end']=time.monotonic_ns()
  rec_control.record_disable_context(rec_ctx);rec_control.sync();rec_thread.join(timeout=2)
  r['times']['recorder_stopped']=time.monotonic_ns();r['fresh']['xrecord_events']=rec_events;r['fresh']['xrecord_errors']=rec_errors;r['fresh']['xrecord_thread_alive']=rec_thread.is_alive()
  sample_stop.set();sample_thread.join(timeout=2);r['fresh']['b_samples']=samples;r['fresh']['sampler_alive']=sample_thread.is_alive()
  gaps=[(b['ns']-a['ns'])/1e6 for a,b in zip(samples,samples[1:])];r['fresh']['max_sample_gap_ms']=max(gaps) if gaps else None
  r['fresh']['keys_after_horizon']={k:down(d,k) for k in ('w','b')};release=(fa.get('result',{}).get('execution',{}).get('releases') or [])
  r['checks'].update({'fresh_distinct_process':fresh_owner.pid!=r['target_pid'],'xid_reused':fw.id==r['xid'],'process_generation_distinct':fo['source']['pointer_binding']['process_generation']!=source['pointer_binding']['process_generation'],'stale_alias_refused_before_dispatch':stale.get('status')=='refused' and stale.get('result',{}).get('input_dispatched') is False,'fresh_before_old_delayed_deadline':r['times']['fresh_ready']<r['marker']['flushed_ns']+8000000000,'fresh_horizon_elapsed':r['times']['fresh_horizon_end']-r['times']['fresh_horizon_start']>=8500000000,'fresh_action_completed':fa.get('status')=='completed' and fa.get('result',{}).get('status')=='completed','fresh_release_verified':bool(release) and release[-1].get('verified') is True,'fresh_scene_changed':r['fresh']['visual_changed_fraction']>=.05,'b_not_observed_down':bool(samples) and samples[0]['ns']<r['marker']['flushed_ns']+8000000000 and samples[-1]['ns']>r['marker']['flushed_ns']+8000000000 and not any(a['b'] for a in samples) and not r['fresh']['sampler_alive'] and r['fresh']['max_sample_gap_ms']<=200,'fresh_keys_up_after_horizon':not any(r['fresh']['keys_after_horizon'].values())})
  bcode=d.keysym_to_keycode(XK.string_to_keysym('b'));wcode=d.keysym_to_keycode(XK.string_to_keysym('w'))
  recorded_b=[e for e in rec_events if e['type']==X.KeyPress and e['detail']==bcode]
  recorded_w=[e for e in rec_events if e['detail']==wcode and e['ns']>=r['times']['fresh_action_started']]
  r['checks'].update({'recorder_covers_delayed_deadline':r['times']['recorder_ready']<r['marker']['flushed_ns']+8000000000<r['times']['recorder_stopped'],'recorded_fresh_w_press_and_release':any(e['type']==X.KeyPress for e in recorded_w) and any(e['type']==X.KeyRelease for e in recorded_w),'no_recorded_b_press':not recorded_b,'recorder_exited_without_error':not rec_errors and not rec_thread.is_alive()})
  if all(r['checks'].values()):r['status']='PASS'
  elif not r['checks']['xid_reused'] and all(v for k,v in r['checks'].items() if k!='xid_reused'):r['status']='HOLD_NO_XID_REUSE'
  else:r['status']='FAIL'
 except BaseException as e:r.update(status='FAIL',error_type=type(e).__name__,error=str(e),traceback=traceback.format_exc())
 finally:
  if x is not None and x.poll() is None:
   try:
    if state(x.pid) in ('T','t'):os.kill(x.pid,signal.SIGCONT)
   except Exception:pass
  if rec_control is not None and rec_ctx is not None:
   try:rec_control.record_disable_context(rec_ctx);rec_control.sync()
   except Exception:pass
  if rec_thread is not None:rec_thread.join(timeout=2)
  if rec_display is not None:
   try:rec_display.close()
   except Exception:pass
  if rec_control is not None:rec_control.close()
  if sample_stop is not None:sample_stop.set()
  if sample_thread is not None:sample_thread.join(timeout=2)
  if fresh_server is not None:
   try:await asyncio.wait_for(fresh_server.call_tool('interface_close',{}),3)
   except BaseException:pass
  if fresh_owner is not None:
   if fresh_owner.running:
    try:signal.pidfd_send_signal(fresh_owner._pidfd,signal.SIGKILL);fresh_owner._process.wait(timeout=2)
    except Exception as e:r['fresh_cleanup_error']=repr(e)
   try:fresh_owner.close()
   except Exception as e:r['fresh_handle_close_error']=repr(e)
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
