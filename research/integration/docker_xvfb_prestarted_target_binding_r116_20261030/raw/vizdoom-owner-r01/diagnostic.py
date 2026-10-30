import json, os, subprocess, time, traceback
from pathlib import Path
from Xlib import display
import vizdoom as vd
root=Path('/evidence'); result={'status':'RUNNING','input_sent':False}; xvfb=None; d=None; game=None
try:
 os.environ['DISPLAY']=':91'; os.environ['XDG_CACHE_HOME']='/tmp/cache'
 xvfb=subprocess.Popen(['Xvfb',':91','-screen','0','1280x1024x24','-cc','4','-nolisten','tcp'],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
 for _ in range(150):
  try: d=display.Display(':91'); break
  except Exception: time.sleep(.02)
 if d is None: raise RuntimeError('Xvfb unavailable')
 game=vd.DoomGame(); game.set_doom_game_path(str(Path(vd.__file__).resolve().parent/'freedoom2.wad'));game.set_doom_map('MAP01');game.set_mode(vd.Mode.ASYNC_SPECTATOR);game.set_window_visible(True);game.set_sound_enabled(False);game.set_console_enabled(False);game.set_screen_resolution(vd.ScreenResolution.RES_640X480);game.init()
 windows=[]
 for w in d.screen().root.query_tree().children:
  title=w.get_wm_name()
  if title and 'VIZDOOM' in title.upper() and w.get_attributes().map_state==2: windows.append(w)
 if len(windows)!=1: raise RuntimeError('expected exactly one visible game window: '+str(len(windows)))
 w=windows[0];ver=d.res_query_version();reply=d.res_query_client_ids([{'client':w.id,'mask':2}]);item=reply.ids[0];pid=item.value[0]
 def proc(pid):
  stat=Path('/proc',str(pid),'stat').read_text(); fields=stat[stat.rfind(')')+1:].split();return {'pid':pid,'ppid':int(fields[1]),'start_ticks':int(fields[19]),'state':fields[0]}
 ancestry=[];current=pid
 for _ in range(8):
  entry=proc(current);ancestry.append(entry)
  if entry['ppid']<=0 or entry['ppid']==current:break
  current=entry['ppid']
 result.update(status='PASS',xres_version=[ver.server_major,ver.server_minor],xid=w.id,xres_pid=pid,launcher_pid=os.getpid(),launcher_is_xres_pid=pid==os.getpid(),launcher_is_ancestor=any(v['pid']==os.getpid() for v in ancestry),ancestry=ancestry)
except BaseException as e: result.update(status='FAIL',error_type=type(e).__name__,error=str(e),traceback=traceback.format_exc())
finally:
 if game is not None:
  try:game.close();result['game_close']='returned'
  except Exception as e:result['game_close']=repr(e)
 if d is not None:d.close()
 if xvfb is not None:
  if xvfb.poll() is None:xvfb.terminate()
  try:xvfb.wait(timeout=3)
  except subprocess.TimeoutExpired:xvfb.kill();xvfb.wait()
  result['xvfb_exitcode']=xvfb.returncode
 (root/'result.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result));raise SystemExit(0 if result['status']=='PASS' else 1)
