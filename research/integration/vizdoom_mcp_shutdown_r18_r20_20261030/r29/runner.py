import json,os,subprocess,time,traceback,math
from pathlib import Path
from Xlib import X,XK,display,error
from Xlib.ext import xtest
import vizdoom as vd
E=Path('/evidence')
def down(d,k):
 c=d.keysym_to_keycode(XK.string_to_keysym(k));m=d.query_keymap();return bool(m[c//8] & 1<<(c%8))
def one(name,number):
 result={'arm':name,'input_sent':False};x=None;d=None;game=None
 try:
  disp=':'+str(number);os.environ['DISPLAY']=disp;os.environ['SDL_VIDEODRIVER']='x11';os.environ['XDG_CACHE_HOME']='/tmp/cache';x=subprocess.Popen(['Xvfb',disp,'-screen','0','1280x1024x24','-cc','4','-nolisten','tcp'],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
  for _ in range(200):
   try:d=display.Display(disp);break
   except Exception:time.sleep(.02)
  if d is None:raise RuntimeError('Xvfb unavailable')
  cfg=Path('/tmp')/('oracle-'+name+'.ini');cfg.write_text('[Doom.Bindings]\nw=+forward\n')
  game=vd.DoomGame();game.set_doom_game_path(str(Path(vd.__file__).resolve().parent/'freedoom2.wad'));game.set_doom_scenario_path('');game.set_doom_map('MAP01');game.set_doom_config_path(str(cfg));game.set_mode(vd.Mode.ASYNC_SPECTATOR);game.set_ticrate(35);game.set_seed(990619);game.set_doom_skill(1);game.add_game_args('-nomonsters');game.set_episode_timeout(2100);game.set_window_visible(True);game.set_console_enabled(False);game.set_sound_enabled(False);game.set_screen_resolution(vd.ScreenResolution.RES_640X480);game.set_available_buttons([vd.Button.MOVE_FORWARD]);game.set_available_game_variables([vd.GameVariable.POSITION_X,vd.GameVariable.POSITION_Y]);game.init()
  w=None
  for _ in range(250):
   for candidate in d.screen().root.query_tree().children:
    try:
     title=candidate.get_wm_name()
     if title and 'DOOM' in title.upper() and candidate.get_attributes().map_state==2:w=candidate;break
    except error.BadWindow:pass
   if w:break
   time.sleep(.02)
  if w is None:raise RuntimeError('window unavailable')
  w.set_input_focus(X.RevertToParent,X.CurrentTime);d.sync();time.sleep(1);game.advance_action(1,True)
  def score():return [game.get_game_variable(vd.GameVariable.POSITION_X),game.get_game_variable(vd.GameVariable.POSITION_Y)]
  result['before']=score();result['tic_before']=game.get_episode_time();result['started_ns']=time.monotonic_ns()
  if name=='move':
   code=d.keysym_to_keycode(XK.string_to_keysym('w'));xtest.fake_input(d,X.KeyPress,detail=code);d.sync();result['input_sent']=True
  time.sleep(.6)
  if name=='move':xtest.fake_input(d,X.KeyRelease,detail=code);d.sync()
  result['ended_ns']=time.monotonic_ns();time.sleep(.3);game.advance_action(1,True);result['after']=score();result['tic_after']=game.get_episode_time();result['w_down']=down(d,'w');result['displacement']=math.dist(result['before'],result['after']);result['status']='completed'
 except BaseException as e:result.update(status='FAIL',error=str(e),traceback=traceback.format_exc())
 finally:
  if game is not None:
   try:game.close()
   except Exception as e:result['game_close_error']=repr(e)
  if d is not None:d.close()
  if x is not None and x.poll() is None:x.terminate();x.wait(timeout=3)
 (E/(name+'.json')).write_text(json.dumps(result,indent=2)+'\n');return result
if __name__=='__main__':
 a=one('coast',91);b=one('move',92);valid=all(x.get('status')=='completed' and x.get('w_down') is False for x in (a,b));same=valid and math.dist(a['before'],b['before'])<1;effect=same and a['displacement']<1 and b['displacement']>5
 report={'status':'PASS' if effect else 'FAIL','valid':valid,'same_initial_position':same,'coast_displacement':a.get('displacement'),'move_displacement':b.get('displacement'),'no_model_calls':True,'limits':'standalone scorer calibration, no MCP, ownership or recovery'};(E/'result.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report));raise SystemExit(0 if effect else 1)
