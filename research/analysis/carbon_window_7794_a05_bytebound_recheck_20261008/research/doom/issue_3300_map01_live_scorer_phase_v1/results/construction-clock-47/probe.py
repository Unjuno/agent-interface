from __future__ import annotations
import hashlib,json,os,sys,time
from pathlib import Path
import vizdoom as vd
sys.path.insert(0,'/scorer')
from session_map01_v13 import _coherent_progress_sample

WAD=Path('/assets/freedoom2.wad'); SCORER=Path('/scorer/session_map01_v13.py'); OUT=Path('/results/raw.jsonl')
EXPECTED='a8772e088847032510d97ba2312406a6998f21cbab44d4ff10696faa9c0ecd4b'
GETTERS={'get_episode_time','is_episode_finished','is_player_dead','get_game_variable','get_ticrate','is_episode_timeout_reached'}
class Proxy:
 def __init__(self,g): self.g=g; self.events=[]
 def __getattr__(self,n):
  f=getattr(self.g,n)
  if n not in GETTERS or not callable(f): return f
  def call(*a,**kw):
   start=time.monotonic_ns()
   try: result=f(*a,**kw)
   except BaseException as e:
    self.events.append({'name':n,'start_ns':start,'end_ns':time.monotonic_ns(),'status':'error','error':type(e).__name__}); raise
   self.events.append({'name':n,'start_ns':start,'end_ns':time.monotonic_ns(),'status':'ok','result':getattr(result,'name',result)}); return result
  return call
def sample(g):
 p=Proxy(g)
 try: result=_coherent_progress_sample(p,vd.GameVariable,10.0).as_dict(); status='returned'; error=None
 except BaseException as e: result=None; status='raised'; error={'type':type(e).__name__,'message':str(e)}
 return {'status':status,'result':result,'error':error,'getters':p.events}
def main():
 if hashlib.sha256(WAD.read_bytes()).hexdigest()!=EXPECTED or not SCORER.is_file(): raise SystemExit('STOP_SETUP_OR_INFRA: input identity')
 rows=[]
 for i in range(3):
  g=vd.DoomGame(); r={'schema':'issue3453-construction-clock47-v1','index':i,'setup_status':'not_started','wad_sha256':hashlib.sha256(WAD.read_bytes()).hexdigest(),'scorer_sha256':hashlib.sha256(SCORER.read_bytes()).hexdigest(),'cleanup':{'game_closed':False}}
  try:
   g.set_doom_game_path(str(WAD)); g.set_doom_map('map01'); g.set_window_visible(False); g.set_sound_enabled(False); g.set_mode(vd.Mode.ASYNC_SPECTATOR); g.set_ticrate(35); g.set_available_buttons([]); g.set_episode_timeout(350); g.set_seed(345700+i); g.init(); g.new_episode(); r['setup_status']='ok'; r['mode']=str(g.get_mode()); r['ticrate']=int(g.get_ticrate())
   r['passive_reads']=[]; end=time.monotonic()+1.5
   while time.monotonic()<end:
    a=time.monotonic_ns(); t=int(g.get_episode_time()); b=time.monotonic_ns(); r['passive_reads'].append({'start_ns':a,'end_ns':b,'tic':t}); time.sleep(.01)
   r['api_tic_before_zero']=int(g.get_episode_time()); r['scorer_before_zero']=sample(g); r['zero_call_start_ns']=time.monotonic_ns()
   try: g.advance_action(0); r['zero_call_status']='returned'
   except BaseException as e: r['zero_call_status']='raised'; r['zero_call_error']={'type':type(e).__name__,'message':str(e)}
   r['zero_call_end_ns']=time.monotonic_ns(); r['api_tic_after_zero']=int(g.get_episode_time()); r['scorer_after_zero']=sample(g)
  except BaseException as e: r['setup_status']='STOP_SETUP_OR_INFRA'; r['setup_error']={'type':type(e).__name__,'message':str(e)}
  finally:
   try: g.close(); r['cleanup']['game_closed']=True
   except BaseException as e: r['cleanup_error']={'type':type(e).__name__,'message':str(e)}
   tr=Path('/tmp/vizdoom-tic-entry-v2.bin')
   if tr.exists():
    import struct; d=tr.read_bytes(); r['tic_entry_records']=[list(struct.unpack_from('<QQii',d,j)) for j in range(0,len(d)-23,24)]; r['trace_sha256']=hashlib.sha256(d).hexdigest()
   r['exit_ns']=time.monotonic_ns(); rows.append(r)
   with OUT.open('a') as f: f.write(json.dumps(r,sort_keys=True)+'\n'); f.flush(); os.fsync(f.fileno())
 print(json.dumps({'rows':len(rows),'setup_ok':sum(x['setup_status']=='ok' for x in rows),'zero_returned':sum(x.get('zero_call_status')=='returned' for x in rows),'closed':sum(x['cleanup']['game_closed'] for x in rows)},sort_keys=True))
if __name__=='__main__': main()
