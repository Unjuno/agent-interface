from pathlib import Path
import argparse,sys,time,json,subprocess,hashlib,threading
from collections import deque
import numpy as np
import vizdoom as vd
from common import desktop,context,Inputs,screenshot,write

def sync(g):g.advance_action(1,True);return int(g.get_episode_time())
def wait(g,o,t):
    end=time.time()+8
    while True:
        x=sync(g);r=x-o
        if r>=t:return r
        if time.time()>end:raise TimeoutError((r,t))
        time.sleep(.001)
def cap(s,ctx):
    t0=time.perf_counter_ns();im=screenshot(s.name,ctx['geometry']);t1=time.perf_counter_ns();arr=np.asarray(im);return dict(start_ns=t0,end_ns=t1,im=im,rgb_sha256=hashlib.sha256(arr.tobytes()).hexdigest())
class Rolling:
    def __init__(self,s,ctx,period_s,maxlen=64):
        self.s=s;self.ctx=ctx;self.period_s=period_s;self.rows=deque(maxlen=maxlen);self.stop_evt=threading.Event();self.lock=threading.Lock();self.error=None;self.t=threading.Thread(target=self._run,daemon=True)
    def _run(self):
        try:
            while not self.stop_evt.is_set():
                row=cap(self.s,self.ctx)
                with self.lock:self.rows.append(row)
                remain=self.period_s-(time.perf_counter_ns()-row['start_ns'])/1e9
                if remain>0:self.stop_evt.wait(remain)
        except Exception as exc:self.error=repr(exc);self.stop_evt.set()
    def start(self):self.t.start()
    def snapshot(self):
        with self.lock:return list(self.rows)
    def stop(self):self.stop_evt.set();self.t.join(timeout=2)
def freshest_pair(rows,lo,hi,target):
    cand=[]
    for ci,cur in enumerate(rows[1:],1):
        for pi,prev in enumerate(rows[:ci]):
            gap=cur['end_ns']-prev['end_ns']
            if lo<=gap<=hi:cand.append((-cur['end_ns'],abs(gap-target),pi,ci,prev,cur))
    if not cand:raise RuntimeError('rolling_temporal_binding_unavailable')
    _,_,pi,ci,prev,cur=min(cand);return prev,cur,pi,ci
def main():
 p=argparse.ArgumentParser();p.add_argument('--source',required=True);p.add_argument('--plan',required=True);p.add_argument('--calibration',required=True);p.add_argument('--case',type=int,required=True);p.add_argument('--out-root',type=Path,required=True);a=p.parse_args();plan=json.loads(Path(a.plan).read_text());case=[x for x in plan['cases'] if x['case']==a.case][0];out=a.out_root/f"case-{a.case:02d}";out.mkdir(parents=True,exist_ok=False);s=g=inp=roll=None;setup=[];score={'case':case,'task':plan['task'],'runtime_source':a.source}
 try:
  source=Path(a.source);s=desktop(source);cfg=s.tmp/'map.ini';cfg.write_text('[Doom.Bindings]\nw=+forward\ne=+use\nleftarrow=+left\nrightarrow=+right\n');g=vd.DoomGame();g.set_doom_game_path(str(Path(vd.__file__).parent/'freedoom2.wad'));g.set_doom_map('MAP01');g.set_doom_config_path(str(cfg));g.set_mode(vd.Mode.ASYNC_SPECTATOR);g.set_ticrate(35);g.set_seed(case['seed']);g.set_doom_skill(1);g.set_episode_timeout(35*30);g.set_window_visible(True);g.set_sound_enabled(False);g.set_console_enabled(False);g.set_screen_resolution(vd.ScreenResolution.RES_640X480);g.set_render_all_frames(True);g.set_render_hud(True);g.set_available_buttons([vd.Button.MOVE_FORWARD,vd.Button.USE,vd.Button.TURN_LEFT,vd.Button.TURN_RIGHT]);g.set_available_game_variables([vd.GameVariable.POSITION_X]);g.init();time.sleep(.35);ctx=context(s,'doom');sync(g);time.sleep(.1);inp=Inputs(source,ctx,setup)
  for _ in range(8):inp.press('w',.5,.02,'setup')
  sync(g);score['door_x']=float(g.get_game_variable(vd.GameVariable.POSITION_X));inp.press('e',.03,0,'setup_use');origin=sync(g);acq_start=time.perf_counter_ns()
  if case['acquisition']=='rolling':
   roll=Rolling(s,ctx,plan['rolling_period_s']);roll.start();time.sleep(.08);target=7 if case['state']=='opening' else 161;score['current_rel']=wait(g,origin,target);time.sleep(plan['rolling_period_s']*1.15);rows=roll.snapshot()
   if roll.error:raise RuntimeError('rolling_capture:'+roll.error)
   prev,cur,pi,ci=freshest_pair(rows,plan['history_min_gap_ns'],plan['history_max_gap_ns'],plan['history_target_gap_ns']);score['selected_indices']=[pi,ci];write(out/'rolling-ledger.json',[{'index':i,'start_ns':r['start_ns'],'end_ns':r['end_ns'],'rgb_sha256':r['rgb_sha256']} for i,r in enumerate(rows)]);score['rolling_capture_count']=len(rows)
  else:
   targets=(5,7) if case['state']=='opening' else (158,161);score['previous_rel']=wait(g,origin,targets[0]);prev=cap(s,ctx);score['current_rel']=wait(g,origin,targets[1]);cur=cap(s,ctx);score['selected_indices']=None;score['rolling_capture_count']=None
  score['acquisition_wall_ns']=time.perf_counter_ns()-acq_start;score['selected_gap_ns']=cur['end_ns']-prev['end_ns'];prev['im'].save(out/'previous.png');cur['im'].save(out/'current.png');score['evidence_write_age_ns']=time.perf_counter_ns()-cur['end_ns'];score['setup_owner_records']=inp.owner.records.copy();score['setup_release_ok']=all(r.get('verified') and not r.get('keys_down') and not r.get('buttons_down') for r in inp.owner.records if r['event']=='owner_release');inp.close();inp=None
  evidence={'schema':'map01-os-history-acquisition-v5','previous_path':str((out/'previous.png').resolve()),'current_path':str((out/'current.png').resolve()),'previous_capture_started_ns':prev['start_ns'],'previous_capture_ns':prev['end_ns'],'current_capture_started_ns':cur['start_ns'],'current_capture_ns':cur['end_ns'],'previous_rgb_sha256':prev['rgb_sha256'],'current_rgb_sha256':cur['rgb_sha256'],'selected_gap_ns':cur['end_ns']-prev['end_ns'],'acquisition':case['acquisition']};write(out/'evidence.json',evidence);write(out/'context.json',ctx)
  cmd=[sys.executable,str(Path(__file__).with_name('controller.py')),'--source',str(source),'--context',str(out/'context.json'),'--evidence',str(out/'evidence.json'),'--calibration',a.calibration,'--mode','history','--out',str(out/'controller')];t0=time.perf_counter_ns();r=subprocess.run(cmd,capture_output=True,text=True,timeout=8);score['controller_rc']=r.returncode;score['controller_wall_ns']=time.perf_counter_ns()-t0;(out/'controller.stdout').write_text(r.stdout);(out/'controller.stderr').write_text(r.stderr);sync(g);score['final_x']=float(g.get_game_variable(vd.GameVariable.POSITION_X));tr=json.loads((out/'controller'/'trace.json').read_text());score['predicted_label']=tr['predicted_label'];score['use_count']=tr['use_count'];score['observation_age_ns_at_start']=tr['observation_age_ns_at_start'];score['transit_success']=score['final_x']>705;score['semantic_action_correct']=score['predicted_label']==(0 if case['state']=='opening' else 1);score['controller_release_ok']=tr['all_release_verified'];score['condition_success']=bool(score['transit_success'] and score['semantic_action_correct'] and score['setup_release_ok'] and score['controller_release_ok'] and score['observation_age_ns_at_start']<=plan['observation_max_age_ns']);score['error']=None
 except Exception as exc:score['error']=repr(exc)
 finally:
  if roll:roll.stop()
  if inp:inp.close()
  if g:g.close()
  if s:s.close()
  write(out/'score.json',score);print(json.dumps(score))
if __name__=='__main__':main()
