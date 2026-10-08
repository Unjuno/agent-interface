"""Scorer harness: fresh MAP01; controller gets only OS pixels and a fixed task."""
from pathlib import Path
import argparse,sys,time,json,os,subprocess,contextlib,math
import vizdoom as vd
from common import desktop,context,Inputs,screenshot,write,sha
p=argparse.ArgumentParser();p.add_argument('--source',required=True);p.add_argument('--out',required=True);p.add_argument('--seed',type=int,required=True);p.add_argument('--turn',type=float,default=0);p.add_argument('--mode',default='search-feedback');p.add_argument('--probe',action='store_true');a=p.parse_args()
out=Path(a.out);out.mkdir(parents=True,exist_ok=False);s=g=inp=None;score=dict(seed=a.seed,turn=a.turn,mode=a.mode,development=True,model_calls=0,score_only_game_variables=True);events=[]
# Fixed predeclared short motor program. Not a map route or hidden-state controller.
program=[['w',.25]]*16+[['e',.08]]+[['w',.25]]*8
try:
 with (out/'startup.txt').open('w') as log,contextlib.redirect_stdout(log):
  s=desktop(a.source);cfg=s.tmp/'map.ini';cfg.write_text('[Doom.Bindings]\nleftarrow=+left\nrightarrow=+right\nw=+forward\ne=+use\nspace=+attack\n')
  g=vd.DoomGame();g.set_doom_game_path(str(Path(vd.__file__).parent/'freedoom2.wad'));g.set_doom_scenario_path('');g.set_doom_map('MAP01');g.set_doom_config_path(str(cfg));g.set_mode(vd.Mode.ASYNC_SPECTATOR);g.set_ticrate(35);g.set_seed(a.seed);g.set_doom_skill(1);g.set_episode_timeout(35*45);g.set_window_visible(True);g.set_sound_enabled(False);g.set_console_enabled(False);g.set_screen_resolution(vd.ScreenResolution.RES_640X480);g.set_render_all_frames(True);g.set_render_hud(True)
  g.set_available_buttons([vd.Button.MOVE_FORWARD,vd.Button.TURN_LEFT,vd.Button.TURN_RIGHT,vd.Button.USE]);g.set_available_game_variables([vd.GameVariable.POSITION_X,vd.GameVariable.POSITION_Y,vd.GameVariable.POSITION_Z,vd.GameVariable.ANGLE,vd.GameVariable.HEALTH,vd.GameVariable.KILLCOUNT,vd.GameVariable.DEATHCOUNT]);g.init()
 time.sleep(.4);ctx=context(s,'doom');g.advance_action(1,True);time.sleep(.2)
 def state():
  g.advance_action(1,True)
  return {k:float(g.get_game_variable(getattr(vd.GameVariable,k))) for k in ('POSITION_X','POSITION_Y','POSITION_Z','ANGLE','HEALTH','KILLCOUNT','DEATHCOUNT')}
 box=ctx['geometry'];score['initial']=state();screenshot(s.name,box).save(out/'reference.png');inp=Inputs(a.source,ctx,events)
 if a.turn:inp.press('Right' if a.turn>0 else 'Left',abs(a.turn),.14,'disturbance')
 inp.close();score['setup_input_records']=inp.owner.records;inp=None;score['perturbed']=state()
 config=dict(domain='doom',mode=a.mode,context=ctx,box=box,reference=str(out/'reference.png'),gain=-348.3987247242647,program=program)
 write(out/'controller-config.json',config);t0=time.perf_counter_ns();tic0=g.get_episode_time()
 r=subprocess.run([sys.executable,str(Path(__file__).with_name('controller.py')),'--source',a.source,'--config',str(out/'controller-config.json'),'--out',str(out/'controller')],capture_output=True,text=True,timeout=25)
 (out/'controller.stdout').write_text(r.stdout);(out/'controller.stderr').write_text(r.stderr);score['controller_exit_code']=r.returncode
 score['final']=state();t1=time.perf_counter_ns();score['wall_s']=(t1-t0)/1e9;score['tics']=g.get_episode_time()-tic0
 ini=score['initial'];end=score['final'];ang=math.radians(ini['ANGLE']);dx=end['POSITION_X']-ini['POSITION_X'];dy=end['POSITION_Y']-ini['POSITION_Y']
 score['forward_displacement']=dx*math.cos(ang)+dy*math.sin(ang);score['cross_track_displacement']=-dx*math.sin(ang)+dy*math.cos(ang)
 from oracle import doom_outcome
 score['dead']=bool(g.is_player_dead());score['finished']=bool(g.is_episode_finished());score['timeout']=bool(g.is_episode_timeout_reached());screenshot(s.name,box).save(out/'final.png');score.update(doom_outcome(score))
except Exception as exc:score['error']=repr(exc)
finally:
 if inp:inp.close()
 if g:g.close()
 if s:s.close()
 score['setup_events']=events;score['runner_sha256']=sha(__file__);score['controller_sha256']=sha(Path(__file__).with_name('controller.py'));write(out/'score.json',score);print(json.dumps(score))
