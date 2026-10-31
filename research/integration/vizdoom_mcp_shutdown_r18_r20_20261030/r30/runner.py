import asyncio,json,os,subprocess,time,traceback,math
from runtime.cli_v1.mcp_server import create_server
from runtime.cli_v1.test_mcp_xvfb_blocked_release_integration import _metadata
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
  async def control():
   server=create_server({'app':w.id},E/(name+'-mcp'),display_name=disp,session_mode='guarded-x11',guarded_process_identity=True,guarded_query_worker=True,guarded_window_lifecycle=True,guarded_owned_process=True)
   async def call(method,args):return _metadata(await asyncio.wait_for(server.call_tool(method,args),15))
   try:
    observation=await call('interface_guarded_observe',{});result['observe_status']=observation.get('status')
    if observation.get('status')!='observed':raise RuntimeError('observe failed')
    geom=observation['source']['pointer_binding']['geometry'];point=[geom[0]+44,geom[1]+geom[3]-54]
    minted=await call('interface_guarded_mint',{'alias':'fresh','source_sequence':observation['source']['sequence'],'point':point,'region_size':[24,38]});result['mint_status']=minted.get('status')
    if minted.get('status')!='minted':raise RuntimeError('mint failed')
    game.advance_action(1,True);result['before']=score();result['tic_before']=game.get_episode_time();result['started_ns']=time.monotonic_ns()
    if name=='move':
     action=await call('interface_guarded_input',{'alias':'fresh','offset':minted['offset'],'interaction':'keyboard','observe_after':False,'tail':[{'op':'key_state','key':'w','down':True},{'op':'wait_update','timeout_ms':600},{'op':'key_state','key':'w','down':False}],'wait_for_result_ms':10000});result['action']=action;result['input_sent']=True
    else:await asyncio.sleep(.6)
    result['ended_ns']=time.monotonic_ns();await asyncio.sleep(.3);game.advance_action(1,True);result['after']=score();result['tic_after']=game.get_episode_time();result['w_down']=down(d,'w');result['displacement']=math.dist(result['before'],result['after'])
   finally:result['close']=await call('interface_close',{})
  asyncio.run(control())
  result['status']='completed'
 except BaseException as e:result.update(status='FAIL',error=str(e),traceback=traceback.format_exc())
 finally:
  if game is not None:
   try:game.close()
   except Exception as e:result['game_close_error']=repr(e)
  if d is not None:d.close()
  if x is not None and x.poll() is None:x.terminate();x.wait(timeout=3)
 (E/(name+'.json')).write_text(json.dumps(result,indent=2)+'\n');return result
if __name__=='__main__':
 a=one('coast',91);b=one('move',92);valid=all(x.get('status')=='completed' and x.get('w_down') is False and x.get('close',{}).get('verified') is True for x in (a,b)) and b.get('action',{}).get('status')=='completed' and b.get('action',{}).get('result',{}).get('status')=='completed';same=valid and math.dist(a['before'],b['before'])<1;effect=same and a['displacement']<1 and b['displacement']>5
 report={'status':'PASS' if effect else 'FAIL','valid':valid,'same_initial_position':same,'coast_displacement':a.get('displacement'),'move_displacement':b.get('displacement'),'no_model_calls':True,'limits':'MCP movement calibration; no owned target handle or recovery'};(E/'result.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report));raise SystemExit(0 if effect else 1)
