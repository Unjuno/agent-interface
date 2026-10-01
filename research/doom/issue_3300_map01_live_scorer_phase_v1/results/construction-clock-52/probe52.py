from __future__ import annotations
import hashlib,json,sys,time
from pathlib import Path
import vizdoom as vd
sys.path.insert(0,'/scorer')
from session_map01_v13 import _coherent_progress_sample
WAD=Path('/assets/freedoom2.wad'); WAD_SHA='a8772e088847032510d97ba2312406a6998f21cbab44d4ff10696faa9c0ecd4b'
SCORER=Path('/scorer/session_map01_v13.py'); OUT=Path('/results/raw.jsonl')
GETTERS={'get_episode_time','is_episode_finished','is_player_dead','get_game_variable','get_ticrate','is_episode_timeout_reached'}
class Proxy:
    def __init__(self,g): self.g=g; self.events=[]
    def __getattr__(self,n):
        f=getattr(self.g,n)
        if n not in GETTERS or not callable(f): return f
        def call(*args,**kwargs):
            a=time.monotonic_ns()
            try:
                v=f(*args,**kwargs); b=time.monotonic_ns(); self.events.append({'name':n,'start_ns':a,'end_ns':b,'value':getattr(v,'name',v),'status':'ok'}); return v
            except BaseException as e:
                b=time.monotonic_ns(); self.events.append({'name':n,'start_ns':a,'end_ns':b,'status':'raised','error':type(e).__name__+': '+str(e)}); raise
        return call
def main():
    i=int(sys.argv[1]); delay=[.5,2,6,10,14,20][i]; exe=Path(vd.__file__).parent/'vizdoom'; g=vd.DoomGame()
    r={'schema':'issue3453-construction-clock52-v1','index':i,'delay_s':delay,'seed':349600+i,
       'engine_binary_sha256':hashlib.sha256(exe.read_bytes()).hexdigest(),'scorer_sha256':hashlib.sha256(SCORER.read_bytes()).hexdigest(),
       'wad_sha256':hashlib.sha256(WAD.read_bytes()).hexdigest(),'setup_status':'not_started','cleanup':{'game_closed':False},'action_calls':0}
    try:
        if r['wad_sha256']!=WAD_SHA: raise RuntimeError('STOP_WAD_HASH')
        g.set_doom_game_path(str(WAD)); g.set_doom_map('map01'); g.set_window_visible(False); g.set_sound_enabled(False)
        g.set_mode(vd.Mode.ASYNC_SPECTATOR); g.set_ticrate(35); g.set_available_buttons([]); g.set_episode_timeout(350); g.set_seed(r['seed']); g.init(); g.new_episode()
        r.update({'setup_status':'ok','mode':str(g.get_mode()),'ticrate':int(g.get_ticrate())})
        start=time.monotonic_ns(); deadline=time.monotonic()+delay; r['passive_reads']=[]
        while time.monotonic()<deadline:
            a=time.monotonic_ns(); tic=int(g.get_episode_time()); b=time.monotonic_ns(); finished=bool(g.is_episode_finished()); c=time.monotonic_ns()
            r['passive_reads'].append({'tic':tic,'finished':finished,'start_ns':a,'end_ns':b,'finished_read_ns':c}); time.sleep(.1)
        r['passive_window_start_ns']=start; r['passive_window_end_ns']=time.monotonic_ns()
        r['final_tic']=int(g.get_episode_time()); r['final_finished']=bool(g.is_episode_finished())
        p=Proxy(g); r['scorer_start_ns']=time.monotonic_ns()
        try: r['scorer_return']=_coherent_progress_sample(p,vd.GameVariable,10.0).as_dict(); r['scorer_status']='returned'
        except BaseException as e: r['scorer_status']='raised'; r['scorer_error']={'type':type(e).__name__,'message':str(e)}
        r['scorer_end_ns']=time.monotonic_ns(); r['scorer_getters']=p.events
    except BaseException as e: r['setup_status']='STOP_SETUP_OR_IDENTITY'; r['error']={'type':type(e).__name__,'message':str(e)}
    finally:
        try: g.close(); r['cleanup']['game_closed']=True
        except BaseException as e: r['cleanup_error']={'type':type(e).__name__,'message':str(e)}
        with OUT.open('a') as f: f.write(json.dumps(r,sort_keys=True)+'\n'); f.flush()
        print(json.dumps({'index':i,'delay_s':delay,'setup':r['setup_status'],'scorer':r.get('scorer_status'),
          'final_tic':r.get('final_tic'),'finished':r.get('final_finished'),'cleanup':r['cleanup']},sort_keys=True))
if __name__=='__main__': main()
