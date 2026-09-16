from pathlib import Path
import sys,time,json,math,argparse,hashlib
import numpy as np
from PIL import Image
import vizdoom as vd
from common import desktop,context,Inputs,screenshot,write
SOURCE_DEFAULT='/mnt/data/offline_lab_extract/source'
MOTION_THRESHOLD=0.055
FORWARD_SECONDS=0.35
TURN_SECONDS=0.19
ESCALATE_PULSES=6
REPEAT_WINDOW=4
DECISIONS=45

def descriptor(im):
    a=np.asarray(im.convert('L'),dtype=np.float32)[35:325,55:585]
    a=np.asarray(Image.fromarray(a.astype(np.uint8)).resize((48,26),Image.Resampling.BILINEAR),dtype=np.float32)/255.0
    a=(a-a.mean())/(a.std()+1e-4)
    return a.astype(np.float32).ravel()

def run(out,arm,seed,source=SOURCE_DEFAULT):
    out=Path(out);out.mkdir(parents=True,exist_ok=False);source=Path(source);s=desktop(source);g=inp=None;events=[];rows=[];before_desc=[];after_desc=[];last_np=None;escalations=0
    try:
      cfg=s.tmp/'doom.ini';cfg.write_text('[Doom.Bindings]\nleftarrow=+left\nrightarrow=+right\nw=+forward\ne=+use\n')
      pkg=Path(vd.__file__).parent;g=vd.DoomGame();g.set_doom_game_path(str(pkg/'freedoom2.wad'));g.set_doom_map('MAP01');g.set_doom_config_path(str(cfg));g.set_game_args('-nomonsters');g.set_mode(vd.Mode.ASYNC_SPECTATOR);g.set_ticrate(35);g.set_seed(seed);g.set_doom_skill(1);g.set_episode_timeout(35*90);g.set_window_visible(True);g.set_sound_enabled(False);g.set_console_enabled(False);g.set_screen_resolution(vd.ScreenResolution.RES_640X480);g.set_render_all_frames(True);g.set_render_hud(True);g.set_available_buttons([vd.Button.TURN_LEFT,vd.Button.TURN_RIGHT,vd.Button.MOVE_FORWARD,vd.Button.USE]);g.set_available_game_variables([vd.GameVariable.POSITION_X,vd.GameVariable.POSITION_Y,vd.GameVariable.ANGLE,vd.GameVariable.DEATHCOUNT]);g.init();time.sleep(.3);ctx=context(s,'doom');inp=Inputs(source,ctx,events);g.advance_action(1,True)
      start=time.perf_counter();prev_pos=None
      for i in range(DECISIONS):
        if g.is_episode_finished():break
        x=float(g.get_game_variable(vd.GameVariable.POSITION_X));y=float(g.get_game_variable(vd.GameVariable.POSITION_Y));ang=float(g.get_game_variable(vd.GameVariable.ANGLE))
        before=screenshot(s.name,ctx['geometry']);bd=descriptor(before);inp.press('w',FORWARD_SECONDS,.04,'forward');g.advance_action(1,True);after=screenshot(s.name,ctx['geometry']);ad=descriptor(after);motion=float(np.mean((ad-bd)**2));no_progress=motion<MOTION_THRESHOLD
        before_desc.append(bd);after_desc.append(ad);repair=None
        if no_progress:
          inp.press('e',.04,.03,'use_probe');repeated=last_np is not None and i-last_np<=REPEAT_WINDOW;pulses=ESCALATE_PULSES if arm=='escalate' and repeated else 1
          for _ in range(pulses):inp.press('Right',TURN_SECONDS,.01,'repair_turn')
          repair={'repeated':repeated,'pulses':pulses}
          if arm=='escalate' and repeated:escalations+=1
          last_np=i
        elif (i+1)%9==0:
          inp.press('e',.04,.03,'periodic_use')
          for _ in range(3):inp.press('Right',TURN_SECONDS,.01,'periodic_turn')
        rows.append({'i':i,'x':x,'y':y,'angle':ang,'motion_mse':motion,'no_progress':no_progress,'repair':repair})
      release_ok=all(r.get('verified') and not r.get('keys_down') and not r.get('buttons_down') for r in inp.owner.records if r.get('event')=='owner_release')
      score={'schema':'agent-interface/map01-no-progress-deopt-case-v1','arm':arm,'seed':seed,'decisions':len(rows),'deopt_escalations':escalations,'map_exit':bool(g.is_episode_finished() and not g.is_player_dead()),'player_dead':bool(g.is_player_dead()),'wall_seconds':time.perf_counter()-start,'release_ok':release_ok,'nomonsters':True}
      write(out/'score.json',score);write(out/'trajectory.json',rows);write(out/'owner-records.json',inp.owner.records);np.savez_compressed(out/'descriptors.npz',before=np.asarray(before_desc,np.float32),after=np.asarray(after_desc,np.float32));write(out/'events.json',events)
    finally:
      if inp:inp.close()
      if g:g.close()
      s.close()
    return score
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--out',required=True);p.add_argument('--arm',choices=['repeat_small','escalate'],required=True);p.add_argument('--seed',type=int,required=True);p.add_argument('--source',default=SOURCE_DEFAULT);a=p.parse_args();print(json.dumps(run(a.out,a.arm,a.seed,a.source)))
