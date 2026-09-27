from __future__ import annotations
import hashlib, importlib.util, json, sys, time
from pathlib import Path
import vizdoom as vd

sys.path.insert(0,'/scorer')
from session_map01_v13 import _coherent_progress_sample
WAD=Path('/assets/freedoom2.wad'); OUT=Path('/results/raw.jsonl')
WAD_SHA='a8772e088847032510d97ba2312406a6998f21cbab44d4ff10696faa9c0ecd4b'
SCORER=Path('/scorer/session_map01_v13.py')
NAMES={'get_episode_time','is_episode_finished','is_player_dead','get_game_variable','get_ticrate','is_episode_timeout_reached'}

class Capture:
    def __init__(self,g): self.g=g; self.events=[]
    def __getattr__(self,n):
        f=getattr(self.g,n)
        if n not in NAMES or not callable(f): return f
        def call(*args,**kwargs):
            start=time.monotonic_ns()
            try:
                v=f(*args,**kwargs); end=time.monotonic_ns()
                x=getattr(v,'name',v)
                self.events.append({'name':n,'start_ns':start,'end_ns':end,'value':x,'status':'ok'})
                return v
            except BaseException as e:
                end=time.monotonic_ns(); self.events.append({'name':n,'start_ns':start,'end_ns':end,'error':type(e).__name__+': '+str(e),'status':'raised'}); raise
        return call

def passive(g,duration):
    out=[]; deadline=time.monotonic()+duration
    while time.monotonic()<deadline:
        t0=time.monotonic_ns(); tic=int(g.get_episode_time()); t1=time.monotonic_ns()
        out.append({'tic':tic,'start_ns':t0,'end_ns':t1}); time.sleep(.01)
    return out

def main():
    i=int(sys.argv[1]); exe=Path(vd.__file__).parent/'vizdoom'
    row={'schema':'issue3453-construction-clock50-v1','index':i,'seed':349500+i,
      'engine_binary_sha256':hashlib.sha256(exe.read_bytes()).hexdigest(),
      'scorer_sha256':hashlib.sha256(SCORER.read_bytes()).hexdigest(),
      'wad_sha256':hashlib.sha256(WAD.read_bytes()).hexdigest(),'setup_status':'not_started','cleanup':{'game_closed':False},'action_calls':0}
    g=vd.DoomGame()
    try:
        if row['wad_sha256']!=WAD_SHA: raise RuntimeError('STOP_WAD_HASH')
        g.set_doom_game_path(str(WAD)); g.set_doom_map('map01'); g.set_window_visible(False); g.set_sound_enabled(False)
        g.set_mode(vd.Mode.ASYNC_SPECTATOR); g.set_ticrate(35); g.set_available_buttons([]); g.set_episode_timeout(350); g.set_seed(row['seed']); g.init(); g.new_episode()
        row.update({'setup_status':'ok','mode':str(g.get_mode()),'ticrate':int(g.get_ticrate())})
        row['pre_passive_reads']=passive(g,1.5)
        capture=Capture(g); row['scorer_start_ns']=time.monotonic_ns()
        try:
            row['scorer_return']=_coherent_progress_sample(capture,vd.GameVariable,10.0).as_dict(); row['scorer_status']='returned'
        except BaseException as e:
            row['scorer_status']='raised'; row['scorer_error']={'type':type(e).__name__,'message':str(e)}
        row['scorer_end_ns']=time.monotonic_ns(); row['scorer_getters']=capture.events
        row['post_passive_reads']=passive(g,.5)
    except BaseException as e:
        row['setup_status']='STOP_SETUP_OR_IDENTITY'; row['error']={'type':type(e).__name__,'message':str(e)}
    finally:
        try: g.close(); row['cleanup']['game_closed']=True
        except BaseException as e: row['cleanup_error']={'type':type(e).__name__,'message':str(e)}
        with OUT.open('a') as f: f.write(json.dumps(row,sort_keys=True)+'\n'); f.flush()
        print(json.dumps(row,sort_keys=True))
if __name__=='__main__': main()
