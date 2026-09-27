from pathlib import Path
import argparse,json,math,sys,time
import vizdoom as vd
sys.path.insert(0,'/mnt/data/sector165-gated-continuation-lab/source')
import base_fixture as base
from common import desktop,context,Inputs,screenshot,write
SRC=Path('/mnt/data/offline_lab_extract/source');WAD=base.WAD
DUR={'short_control':1.25,'bounded_macro':1.60}
def derr(t,c):return ((t-c+180)%360)-180
def align(g,inp,target):
 for _ in range(50):
  a=float(g.get_game_variable(vd.GameVariable.ANGLE));e=derr(target,a)
  if abs(e)<6:break
  inp.press('Left' if e>0 else 'Right',.08,.005,'setup_align');time.sleep(.015);g.advance_action(1,True)
 a=float(g.get_game_variable(vd.GameVariable.ANGLE));return a,derr(target,a)
def st(g):
 x=float(g.get_game_variable(vd.GameVariable.POSITION_X));y=float(g.get_game_variable(vd.GameVariable.POSITION_Y));z=float(g.get_game_variable(vd.GameVariable.POSITION_Z));a=float(g.get_game_variable(vd.GameVariable.ANGLE));return {'x':x,'y':y,'z':z,'angle':a,'sector':base.sector(x,y)}
def main():
 p=argparse.ArgumentParser();p.add_argument('--out',required=True);p.add_argument('--arm',choices=sorted(DUR),required=True);p.add_argument('--heading',type=float,required=True);p.add_argument('--seed',type=int,required=True);a=p.parse_args();dur=DUR[a.arm];out=Path(a.out);out.mkdir(parents=True,exist_ok=False);s=desktop(SRC);g=inp=None;ev=[];score={'schema':'agent-interface/map01-sector38-ascent-macro-case-v1','arm':a.arm,'seed':a.seed,'heading':a.heading,'requested_duration_s':dur}
 try:
  cfg=s.tmp/'doom.ini';cfg.write_text('[Doom.Bindings]\nleftarrow=+left\nrightarrow=+right\nw=+forward\ne=+use\n')
  g=vd.DoomGame();g.set_doom_game_path(str(WAD));g.set_doom_map('MAP01');g.set_doom_config_path(str(cfg));g.add_game_args('-nomonsters');g.set_mode(vd.Mode.ASYNC_SPECTATOR);g.set_ticrate(35);g.set_seed(a.seed);g.set_doom_skill(1);g.set_episode_timeout(35*90);g.set_window_visible(True);g.set_sound_enabled(False);g.set_console_enabled(False);g.set_screen_resolution(vd.ScreenResolution.RES_640X480);g.set_render_all_frames(True);g.set_render_hud(True);g.set_available_buttons([vd.Button.TURN_LEFT,vd.Button.TURN_RIGHT,vd.Button.MOVE_FORWARD,vd.Button.USE]);g.set_available_game_variables([vd.GameVariable.POSITION_X,vd.GameVariable.POSITION_Y,vd.GameVariable.POSITION_Z,vd.GameVariable.ANGLE,vd.GameVariable.HEALTH]);g.init();time.sleep(.3);ctx=context(s,'doom');inp=Inputs(SRC,ctx,ev);g.advance_action(1,True)
  score['setup_decisions']=base.navigate_to_165(g,s,ctx,inp);drop=base.align_boundary(g,inp,624);score['drop_alignment']=drop
  if drop['sector']!=165:raise RuntimeError('setup_not_sector165')
  inp.press('e',.08,.01,'drop_use');inp.press('w',.45,.04,'drop_forward');time.sleep(.35);g.advance_action(1,True);time.sleep(.03);before=st(g);score['before']=before
  if before['sector']!=38 or before['z']>-120:raise RuntimeError('setup_drop_failed')
  aa,er=align(g,inp,a.heading);score['heading_alignment']={'actual':aa,'error':er}
  if abs(er)>=6:raise RuntimeError('setup_heading_failed')
  screenshot(s.name,ctx['geometry']).save(out/'pre.png')
  lease=inp.lease(dur+.12);inp.owner.call('down',lease,'w');t0=time.perf_counter_ns()
  try:time.sleep(dur)
  finally:inp.owner.call('up',lease,'w');release=inp.release(lease)
  t1=time.perf_counter_ns();score['hold_elapsed_ns']=t1-t0;score['release']=release
  time.sleep(.05);g.advance_action(1,True);time.sleep(.03);after=st(g);score['after']=after;score['upper_complete']=bool(after['z']>=-64);score['release_ok']=bool(release.get('verified') and not release.get('keys_down') and not release.get('buttons_down'));score['dead']=bool(g.is_player_dead());score['error']=None;screenshot(s.name,ctx['geometry']).save(out/'post.png')
 except Exception as e:score['error']=repr(e)
 finally:
  try:
   if inp:write(out/'owner-records.json',inp.owner.records);inp.close()
  except:pass
  try:
   if g:g.close()
  except:pass
  try:s.close()
  except:pass
  write(out/'score.json',score);write(out/'events.json',ev);print(json.dumps(score,sort_keys=True))
if __name__=='__main__':main()
