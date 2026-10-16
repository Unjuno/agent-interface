"""Executor controls: expiry stays expired, release failure or explicit stop suppresses samples."""
import json,time,types
from pathlib import Path
from executor_v9 import Executor
from lease import Expired
H=Path(__file__).resolve().parent;R=H/'results/expiry-observation-controls-01';R.mkdir(exist_ok=False);rows=[]
for case in ['expiry','release_failed','explicit_stop']:
 events=[]
 class Backend:
  sequence=1
  decoder=types.SimpleNamespace(frame='unchanged')
  observed_pointer={'focus':7}
  def validate(self,steps):pass
  def execute(self,step,cancel,identifier,index):
   if case=='explicit_stop':cancel.cancel.set()
   raise Expired()
  def release_all(self):return {'verified':case!='release_failed','keys_down':[],'buttons_down':[]}
  def snapshot(self,*args):self.sequence+=1
 backend=Backend();executor=Executor(backend,events.append)
 executor.submit('control',[{'op':'observe'}],1,time.perf_counter_ns()+1000000000)
 with executor.lock:thread=executor.active[2]
 thread.join(timeout=2);assert not thread.is_alive();executor.close()
 terminal=next(e for e in events if e['event']=='terminal');post=terminal['post_release_observation']
 if case=='expiry':assert terminal['status']=='expired' and post['captures']==2
 elif case=='release_failed':assert terminal['status']=='failed' and post is None
 else:assert terminal['status']=='expired' and post['captures']==0 and post['stopped']
 rows.append({'case':case,'terminal':terminal})
(R/'result.json').write_text(json.dumps(rows,indent=2)+'\n');print('three executor control groups passed')
