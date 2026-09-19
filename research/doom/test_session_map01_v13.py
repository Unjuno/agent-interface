import json,os,sys,tempfile,threading,time,types,unittest
from pathlib import Path
import session_map01_v13 as candidate
class FakeGame:
 def __init__(self):self.calls=[]
 def _c(self,n):self.calls.append((n,threading.get_ident()))
 def init(self):self._c('init')
 def close(self):self._c('close')
 def is_episode_finished(self):self._c('finished');return False
 def is_player_dead(self):self._c('dead');return False
 def get_game_variable(self,v):self._c('var');return 0
 def get_episode_time(self):self._c('tic');return 100
 def get_ticrate(self):self._c('rate');return 35
 def is_episode_timeout_reached(self):self._c('timeout');return False
class Tests(unittest.TestCase):
 def test_composition_keeps_game_calls_on_main_thread_and_hashes_latest_primitives(self):
  with tempfile.TemporaryDirectory() as tmp:
   out=Path(tmp)/'run';box={};base=types.ModuleType('session_map01_v12')
   class GV:KILLCOUNT='k';DEATHCOUNT='d'
   def ctor():g=FakeGame();box['g']=g;return g
   base.vd=types.SimpleNamespace(DoomGame=ctor,GameVariable=GV);base.sys=sys;base.Backend=object
   def base_main():
    out.mkdir();(out/'sources.json').write_text('{}');g=base.vd.DoomGame();g.init()
    for line in base.sys.stdin:
     if json.loads(line)['op']=='finish':break
    g.close();(out/'events.jsonl').write_text('{"event":"post_control_score"}\n');(out/'delivered.jsonl').write_text('{"event":"post_control_score"}\n')
   base.main=base_main;tele=types.ModuleType('doom_retained_input_backend_v3');tele.Backend=type('B',(),{})
   oldb=sys.modules.get('session_map01_v12');oldt=sys.modules.get('doom_retained_input_backend_v3');sys.modules['session_map01_v12']=base;sys.modules['doom_retained_input_backend_v3']=tele
   r,w=os.pipe();stdin=os.fdopen(r,'r');oldstdin=sys.stdin;oldargv=sys.argv;sys.stdin=stdin;sys.argv=['x','--out',str(out)]
   def writer():time.sleep(.07);os.write(w,b'{"op":"finish"}\n');os.close(w)
   t=threading.Thread(target=writer);t.start();owner=threading.get_ident()
   try:candidate.main()
   finally:
    t.join();stdin.close();sys.stdin=oldstdin;sys.argv=oldargv
    if oldb is None:sys.modules.pop('session_map01_v12',None)
    else:sys.modules['session_map01_v12']=oldb
    if oldt is None:sys.modules.pop('doom_retained_input_backend_v3',None)
    else:sys.modules['doom_retained_input_backend_v3']=oldt
   summary=json.loads((out/'scorer-summary.json').read_text());self.assertGreaterEqual(summary['sample_count'],3);self.assertTrue(all(tid==owner for _,tid in box['g'].calls))
   sources=json.loads((out/'sources.json').read_text());self.assertIn('doom/main_thread_scorer_polling_v1.py',sources);self.assertIn('doom/doom_retained_input_backend_v3.py',sources);self.assertIn('doom/independent_progress_clock_v2.py',sources);self.assertIn('live_control/input_transition_owner_v3.py',sources)

 def test_coherent_progress_sample_retries_tic_change(self):
  class GV:KILLCOUNT='k';DEATHCOUNT='d'
  class G(FakeGame):
   def __init__(self):super().__init__();self.tics=iter([10,11,12,12])
   def get_episode_time(self):self._c('tic');return next(self.tics)
  sample=candidate._coherent_progress_sample(G(),GV,60,clock_ns=lambda:999,attempts=2)
  self.assertEqual(sample.sample_ns,999);self.assertEqual(sample.kill_count,0)
 def test_coherent_progress_sample_fails_closed_when_tic_never_stable(self):
  class GV:KILLCOUNT='k';DEATHCOUNT='d'
  class G(FakeGame):
   def __init__(self):super().__init__();self.t=0
   def get_episode_time(self):self._c('tic');self.t+=1;return self.t
  with self.assertRaisesRegex(RuntimeError,'one-tic coherent'):candidate._coherent_progress_sample(G(),GV,60,attempts=2)
 def test_missing_option_fails(self):
  old=sys.argv;sys.argv=['x']
  try:
   with self.assertRaises(ValueError):candidate._option('--out')
  finally:sys.argv=old
if __name__=='__main__':unittest.main()
