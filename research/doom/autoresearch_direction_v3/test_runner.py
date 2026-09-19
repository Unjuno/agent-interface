import importlib.util, json, tempfile, unittest
from pathlib import Path
HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('runner',HERE/'runner.py');r=importlib.util.module_from_spec(spec);spec.loader.exec_module(r)
def row(state,pair,policy,success,death=0,hard=True):
 return {'case':{'state':state,'pair_id':pair,'policy':policy,'case_id':f'{pair}-{policy}'},'hard_pass':hard,'scorer':{'progress_success_predeadline':success,'kill_delta_predeadline':int(success),'death_delta_predeadline':death}}
class T(unittest.TestCase):
 def make(self,counts):
  out=[]
  for st,(b,c) in counts.items():
   for i in range(3):
    pid=f'{st}-{i}';out += [row(st,pid,'attack_only',i<b),row(st,pid,'back_left_attack',i<c)]
  return out
 def test_pass(self): self.assertEqual(r.decide(self.make({'original':(2,3),'left':(0,3),'right':(1,3)}))['decision'],'PASS_SCOPED_DIRECTION_TRANSFER')
 def test_hold_on_tie(self): self.assertEqual(r.decide(self.make({'original':(2,3),'left':(1,1),'right':(0,3)}))['decision'],'HOLD_INSUFFICIENT_DISCRIMINATION')
 def test_fail_on_regression(self): self.assertEqual(r.decide(self.make({'original':(2,3),'left':(2,1),'right':(0,3)}))['decision'],'FAIL_FIXED_DIRECTION_GENERALITY')
 def test_fail_measurement_gate(self):
  x=self.make({'original':(2,3),'left':(0,3),'right':(1,3)});x[0]['hard_pass']=False
  self.assertEqual(r.decide(x)['decision'],'FAIL_MEASUREMENT_INTEGRITY')
 def test_latest_typed(self):
  ev=[{'event':'typed_observation','id':'x','capture_ns':10,'sequence':1,'signals':{'health':{'status':'observed','value':9},'ammo':{'status':'observed','value':4}}},{'event':'typed_observation','id':'x','capture_ns':20,'sequence':2,'signals':{'health':{'status':'observed','value':8},'ammo':{'status':'observed','value':3}}}]
  self.assertEqual(r.latest_typed_before(ev,'x',15)['health'],9)
 def test_queue_reader_preserves_buffered_lines(self):
  import queue as qmod
  class P:
   def poll(self): return None
  p=P(); p._event_q=qmod.Queue(); p._event_q.put('{"event":"clock","sequence":7}\n'); p._event_q.put('{"event":"accepted","id":"x"}\n')
  a,_=r._next_json(p,0.01); b,_=r._next_json(p,0.01)
  self.assertEqual((a['event'],a['sequence'],b['event']),('clock',7,'accepted'))
if __name__=='__main__':unittest.main()
