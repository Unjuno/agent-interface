from pathlib import Path
import argparse,json,os,subprocess,sys,time
import vizdoom as vd
import base_fixture as base
from common import desktop,context,Inputs,screenshot,write

def derr(t,c):return ((t-c+180)%360)-180

def align_heading(g,inp,line_id,heading):
 row=base.align_boundary(g,inp,line_id)
 if heading is None:return row
 for _ in range(32):
  ang=float(g.get_game_variable(vd.GameVariable.ANGLE));err=derr(heading,ang)
  if abs(err)<8:break
  inp.press('Left' if err>0 else 'Right',.19,.01,'setup_heading');time.sleep(.08);g.advance_action(1,True);time.sleep(.02)
 ang=float(g.get_game_variable(vd.GameVariable.ANGLE));err=derr(heading,ang);row.update(requested_heading=heading,actual_heading=ang,heading_error=err,angle=ang,angle_error=err);return row

def state(g):return {'x':float(g.get_game_variable(vd.GameVariable.POSITION_X)),'y':float(g.get_game_variable(vd.GameVariable.POSITION_Y)),'z':float(g.get_game_variable(vd.GameVariable.POSITION_Z)),'angle':float(g.get_game_variable(vd.GameVariable.ANGLE))}

def main():
 p=argparse.ArgumentParser();p.add_argument('--out',required=True);p.add_argument('--class',dest='klass',choices=['drop','wall'],required=True);p.add_argument('--seed',type=int,required=True);p.add_argument('--gate',choices=['endpoint_gate','temporal_gate'],required=True);p.add_argument('--heading',type=float);p.add_argument('--source',default=str(base.SRC));a=p.parse_args()
 out=Path(a.out);out.mkdir(parents=True,exist_ok=False);source=Path(a.source);events=[];s=desktop(source);g=inp=None;score={'seed':a.seed,'class':a.klass,'gate':a.gate,'requested_heading':a.heading}
 try:
  cfg=s.tmp/'doom.ini';cfg.write_text('[Doom.Bindings]\nleftarrow=+left\nrightarrow=+right\nw=+forward\ne=+use\n')
  g=vd.DoomGame();g.set_doom_game_path(str(base.WAD));g.set_doom_map('MAP01');g.set_doom_config_path(str(cfg));g.add_game_args('-nomonsters');g.set_mode(vd.Mode.ASYNC_SPECTATOR);g.set_ticrate(35);g.set_seed(a.seed);g.set_doom_skill(1);g.set_episode_timeout(35*90);g.set_window_visible(True);g.set_sound_enabled(False);g.set_console_enabled(False);g.set_screen_resolution(vd.ScreenResolution.RES_640X480);g.set_render_all_frames(True);g.set_render_hud(True);g.set_available_buttons([vd.Button.TURN_LEFT,vd.Button.TURN_RIGHT,vd.Button.MOVE_FORWARD,vd.Button.USE]);g.set_available_game_variables([vd.GameVariable.POSITION_X,vd.GameVariable.POSITION_Y,vd.GameVariable.POSITION_Z,vd.GameVariable.ANGLE,vd.GameVariable.HEALTH]);g.init();time.sleep(.3);ctx=context(s,'doom');inp=Inputs(source,ctx,events);g.advance_action(1,True)
  score['setup_decisions']=base.navigate_to_165(g,s,ctx,inp);align=align_heading(g,inp,base.BOUNDARY_LINES[a.klass],a.heading);score['setup_alignment']=align
  if align['sector']!=165 or (a.heading is not None and abs(align['heading_error'])>=8):raise RuntimeError('SETUP_ALIGNMENT_INVALID')
  write(out/'controller-context.json',ctx);before=state(g);before['sector']=base.sector(before['x'],before['y']);score['before']=before
  p1=out/'phase1';cmd=[sys.executable,str(Path(__file__).with_name('phase1.py')),'--source',str(source),'--ctx',str(out/'controller-context.json'),'--out',str(p1),'--gate',a.gate];env=os.environ.copy();env['DISPLAY']=ctx['display'];cp=subprocess.run(cmd,env=env,text=True,capture_output=True,timeout=8);(out/'phase1.stdout').write_text(cp.stdout);(out/'phase1.stderr').write_text(cp.stderr);score['phase1_returncode']=cp.returncode
  if cp.returncode!=0:raise RuntimeError('PHASE1_FAILED')
  r=json.loads((p1/'result.json').read_text());score['phase1']=r;time.sleep(.05);g.advance_action(1,True);time.sleep(.03);mid=state(g);mid['sector']=base.sector(mid['x'],mid['y']);score['after_phase1']=mid;score['hidden_phase1_drop']=bool(mid['z']<=-120)
  score['extra_forward_issued']=bool(r['extra_forward_needed'])
  if r['extra_forward_needed']:
   p2=out/'phase2';cmd=[sys.executable,str(Path(__file__).with_name('extra_forward.py')),'--source',str(source),'--ctx',str(out/'controller-context.json'),'--out',str(p2)];cp=subprocess.run(cmd,env=env,text=True,capture_output=True,timeout=4);(out/'phase2.stdout').write_text(cp.stdout);(out/'phase2.stderr').write_text(cp.stderr);score['phase2_returncode']=cp.returncode
   if cp.returncode!=0:raise RuntimeError('PHASE2_FAILED')
  time.sleep(.05);g.advance_action(1,True);time.sleep(.03);after=state(g);after['sector']=base.sector(after['x'],after['y']);score['after']=after
  owner=[]
  for pth in [p1/'owner-records.json',out/'phase2'/'owner-records.json']:
   if pth.exists():owner.extend(json.loads(pth.read_text()))
  score['controller_release_ok']=all(r.get('verified') and not r.get('keys_down') and not r.get('buttons_down') for r in owner if r.get('event')=='owner_release')
  score['setup_release_ok']=all(r.get('verified') and not r.get('keys_down') and not r.get('buttons_down') for r in inp.owner.records if r.get('event')=='owner_release');score['error']=None
 except Exception as e:score['error']=repr(e)
 finally:
  try:
   if inp:write(out/'setup-owner-records.json',inp.owner.records);inp.close()
  except Exception:pass
  try:
   if g:g.close()
  except Exception:pass
  try:s.close()
  except Exception:pass
  write(out/'score.json',score);write(out/'setup-events.json',events);print(json.dumps(score,sort_keys=True))
if __name__=='__main__':main()
