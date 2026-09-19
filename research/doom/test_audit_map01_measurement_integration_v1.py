import hashlib,json,tempfile,unittest
from pathlib import Path
from audit_map01_measurement_integration_v1 import audit,REQUIRED_SOURCES
def writej(p,x):p.write_text(''.join(json.dumps(r)+'\n' for r in x))
class Tests(unittest.TestCase):
 def make(self,tmp,verified=True,leak=False,bad_batch=False):
  root=Path(tmp)/'run';root.mkdir();rr=Path(tmp)/'research';rr.mkdir();src={}
  for n in REQUIRED_SOURCES:
   p=rr/n;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(n);src[n]=hashlib.sha256(n.encode()).hexdigest()
  (root/'sources.json').write_text(json.dumps(src));adm=[{'event':'input_admission','intent_token':'t','key':'a','admitted_ns':1,'input_ack_ns':2},{'event':'input_admission','intent_token':'t','key':'d','admitted_ns':3,'input_ack_ns':4}]
  trans=[]
  for pos,(key,start,ret) in enumerate([('a',10,12),('d',13,15)]):trans.append({'event':'input_release_transition','operation':'up','transition_schema':'input-release-transition-v3','intent_token':'t','key':key,'release_batch_schema':'input-release-batch-v3','release_batch_size':2 if not bad_batch else 3,'release_batch_position':pos,'release_batch_identifier':'h','release_batch_step':0,'owner_transition_verified':verified,'owned_keycodes_after_batch':[] if verified else [1],'ordinary_release_candidate':verified,'release_call_started_ns':start,'release_call_returned_ns':ret})
  ev=[{'event':'step_started','id':'h','step':0,'operation':'hold'},*adm,*trans,{'event':'step_completed','id':'h','step':0},{'event':'terminal','id':'h','release':{'verified':True,'keys_down':[],'buttons_down':[]}}]
  if leak:ev.append({'schema':'independent-progress-event-v2'})
  writej(root/'events.jsonl',ev);writej(root/'delivered.jsonl',ev)
  sample=lambda ns:{'controller_visible':False,'payload':{'schema':'independent-progress-sample-v2','sample_ns':ns,'kill_count':0,'death_count':0,'episode_finished':False,'player_dead':False,'map_exit':False}}
  writej(root/'scorer-samples.jsonl',[sample(100),sample(200),sample(300),sample(400)]);writej(root/'scorer-events.jsonl',[]);(root/'scorer-summary.json').write_text(json.dumps({'controller_visible':False,'scheduler':{'missed_sample_periods':0}}))
  return root,rr
 def test_pass_zero_events(self):
  with tempfile.TemporaryDirectory() as t:
   root,rr=self.make(t);r=audit(root,rr);self.assertTrue(r['pass'],r);self.assertTrue(r['direct_retained_input']['measurement_ready']);self.assertEqual(r['positive_useful_event_count'],0)
 def test_unverified_transition_fails(self):
  with tempfile.TemporaryDirectory() as t:
   root,rr=self.make(t,False);self.assertFalse(audit(root,rr)['pass'])
 def test_bad_batch_shape_fails(self):
  with tempfile.TemporaryDirectory() as t:
   root,rr=self.make(t,True,False,True);self.assertFalse(audit(root,rr)['pass'])

 def test_missed_scorer_period_fails(self):
  with tempfile.TemporaryDirectory() as t:
   root,rr=self.make(t);(root/'scorer-summary.json').write_text(json.dumps({'controller_visible':False,'scheduler':{'missed_sample_periods':1}}));self.assertFalse(audit(root,rr)['pass'])
 def test_leak_fails(self):
  with tempfile.TemporaryDirectory() as t:
   root,rr=self.make(t,True,True);self.assertFalse(audit(root,rr)['pass'])
if __name__=='__main__':unittest.main()
