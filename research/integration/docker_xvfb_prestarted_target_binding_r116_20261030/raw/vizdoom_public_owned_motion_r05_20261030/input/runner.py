import asyncio, hashlib, json, os, signal, subprocess, sys, time, traceback
from pathlib import Path
from PIL import Image, ImageChops
from Xlib import X, XK, display
import vizdoom as vd
from runtime.cli_v1.mcp_server import create_server
from runtime.guarded_x11_v1.owned_target_process import OwnedTargetProcess
from runtime.cli_v1.test_mcp_xvfb_blocked_release_integration import _metadata
ROOT=Path('/evidence'); ARM=os.environ['ARM']
def capture(w,path):
 g=w.get_geometry(); raw=w.get_image(0,0,g.width,g.height,X.ZPixmap,0xffffffff)
 if raw is None:raise RuntimeError('capture unavailable')
 img=Image.frombytes('RGB',(g.width,g.height),raw.data,'raw','BGRX');img.save(path);return img
async def call(server,name,args):return _metadata(await asyncio.wait_for(server.call_tool(name,args),15))
async def main():
 result={'arm':ARM,'status':'RUNNING','task_success':None,'no_model_calls':True}; xvfb=None;d=None;owner=None;server=None
 try:
  os.environ['DISPLAY']=':91';os.environ['XDG_CACHE_HOME']='/tmp/cache'
  xvfb=subprocess.Popen(['Xvfb',':91','-screen','0','1280x1024x24','-cc','4','-nolisten','tcp'],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
  for _ in range(150):
   try:d=display.Display(':91');break
   except Exception:await asyncio.sleep(.02)
  if d is None:raise RuntimeError('Xvfb unavailable')
  cfg=Path('/tmp/direct-motion.ini');cfg.write_text('[Doom.Bindings]\nw=+forward\n')
  pkg=Path(vd.__file__).resolve().parent;args=[str(pkg/'vizdoom'),'-iwad',str(pkg/'freedoom2.wad'),'-config',str(cfg),'-warp','1','-window','-nosound','-nojoy','-width','640','-height','480']
  owner=OwnedTargetProcess.launch(args,disposable=True,env=os.environ.copy());result['target_pid']=owner.pid
  windows=[]
  for _ in range(250):
   if not owner.running:break
   windows=[]
   for w in d.screen().root.query_tree().children:
    title=w.get_wm_name()
    if title and 'DOOM' in title.upper() and w.get_attributes().map_state==2:windows.append(w)
   if len(windows)==1:break
   await asyncio.sleep(.02)
  if len(windows)!=1:raise RuntimeError('no unique mapped window')
  w=windows[0];result['xid']=w.id;await asyncio.sleep(2)
  server=create_server({'app':w.id},ROOT/'mcp',session_mode='guarded-x11',guarded_process_identity=True,guarded_query_worker=True,guarded_window_lifecycle=True,guarded_owned_process=True,_guarded_owned_target_process=owner)
  obs=await call(server,'interface_guarded_observe',{});result['observe']=obs
  if obs.get('status')!='observed':raise RuntimeError('observe failed')
  source=obs['source'];native=source['native'];result['capture_before_ns']=time.monotonic_ns();before=capture(w,ROOT/'before.png')
  code=d.keysym_to_keycode(XK.string_to_keysym('w'));result['keycode']=code
  if ARM=='input':
   geo=w.get_geometry();point=[44,geo.height-54]
   minted=await call(server,'interface_guarded_mint',{'alias':'field','source_sequence':source['sequence'],'point':point,'region_size':[24,38]});result['mint']=minted
   if minted.get('status')!='minted':raise RuntimeError('mint failed')
   result['action_started_ns']=time.monotonic_ns()
   action=await call(server,'interface_guarded_input',{'alias':'field','offset':minted['offset'],'interaction':'keyboard','observe_after':False,'tail':[{'op':'key_state','key':'w','down':True},{'op':'wait_update','timeout_ms':600},{'op':'key_state','key':'w','down':False}],'wait_for_result_ms':10000})
   result['action']=action
   if action.get('status')=='pending':
    end=time.monotonic()+10
    while time.monotonic()<end:
     action=await call(server,'interface_results',{'call_id':action['call_id'],'include_image':False})
     if action.get('status')!='pending':break
     await asyncio.sleep(.02)
    result['action_terminal']=action
  else:
   result['action_started_ns']=time.monotonic_ns();await asyncio.sleep(.6)
  result['action_returned_ns']=time.monotonic_ns();await asyncio.sleep(.15)
  result['capture_after_ns']=time.monotonic_ns();after=capture(w,ROOT/'after.png')
  before=before.crop((0,0,before.width,before.height-80));after=after.crop((0,0,after.width,after.height-80))
  diff=ImageChops.difference(before,after); result['visual_changed_fraction']=sum(1 for p in diff.getdata() if max(p)>10)/(diff.width*diff.height)
  keymap=d.query_keymap();result['w_down_after']=bool(keymap[code//8] & (1 << (code%8)))
  result['close']=await call(server,'interface_close',{})
  result['target_retirement']=owner.retire_bound_target()
  result['status']='COMPLETE' if result['target_retirement'].get('process_exit_verified') is True else 'FAIL'
 except BaseException as e:result.update(status='FAIL',error_type=type(e).__name__,error=str(e),traceback=traceback.format_exc())
 finally:
  if server is not None:
   try:await asyncio.wait_for(server.call_tool('interface_close',{}),3)
   except BaseException:pass
  if owner is not None:
   if owner.running:
    signal.pidfd_send_signal(owner._pidfd,signal.SIGKILL)
    try:owner._process.wait(timeout=2)
    except subprocess.TimeoutExpired:result['cleanup_error']='target did not exit'
   try:owner.close()
   except Exception as e:result['handle_close_error']=repr(e)
  if d is not None:d.close()
  if xvfb is not None:
   if xvfb.poll() is None:xvfb.terminate()
   try:xvfb.wait(timeout=3)
   except subprocess.TimeoutExpired:xvfb.kill();xvfb.wait()
   result['xvfb_exitcode']=xvfb.returncode
  (ROOT/'result.json').write_text(json.dumps(result,indent=2)+'\n')
 print(json.dumps(result));return 0 if result['status']=='COMPLETE' else 1
if __name__=='__main__':raise SystemExit(asyncio.run(main()))
