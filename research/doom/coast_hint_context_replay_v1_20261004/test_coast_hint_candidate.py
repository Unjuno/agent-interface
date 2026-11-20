import copy, importlib.util, json, unittest
from pathlib import Path
P=Path(__file__).with_name('coast_hint_candidate.py');spec=importlib.util.spec_from_file_location('coast_hint_candidate',P);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
B={'focus':1,'surface':2,'geometry':[0,0,640,480]}
def event(seq=7,health=77,ammo=42):
 return {'event':'typed_observation','schema':'doom-typed-observation-v1','id':'cover-0','step':seq,'sequence':seq,'capture_ns':1000+seq,'pointer_binding':B,'frame_rgb_sha256':'a'*64,'artifact_published':False,'grants_input_authority':False,'signals':{n:{'signal_id':n,'sequence':seq,'capture_ns':1000+seq,'binding':B,'status':'observed','value':v} for n,v in [('health',health),('ammo',ammo)]}}
def full(e,**overrides):
 r={k:e[k] for k in ('id','step','sequence','capture_ns','pointer_binding','frame_rgb_sha256')};r.update(event='observation',exact=True);r.update(overrides);return r
class Test(unittest.TestCase):
 def test_bound_pending_reconciles_to_history_not_current_state(self):
  h=m.CoastHistory();e=event();self.assertTrue(h.observe_typed(e));self.assertEqual(h.observe_full(full(e))['health'],77);later=full(event(8,health=84));c=h.prompt_context(later);self.assertEqual(c['current_sequence'],8);self.assertEqual(c['coast_history'][0]['health'],77);self.assertLess(c['coast_history'][0]['sequence'],c['current_sequence']);self.assertFalse(c['grants_input_authority']);self.assertFalse(c['coast_history'][0]['task_success_verified'])
 def test_identity_binding_and_hash_mismatch_are_dropped(self):
  for changes in ({'sequence':8},{'frame_rgb_sha256':'b'*64},{'pointer_binding':{'focus':9,'surface':2,'geometry':[0,0,640,480]}},{'id':'cover-x'}):
   h=m.CoastHistory();e=event();h.observe_typed(e);h.observe_full(full(e,**changes));self.assertEqual(h.reconciled,[]);self.assertEqual(h.prompt_context(full(event(9)))['coast_history'],[])
 def test_unknown_malformed_and_out_of_order_fail_closed(self):
  e=event();e['signals']['health']['status']='unknown';e['signals']['health']['value']=None;self.assertIsNone(m.capture_coast_sample(e,0));e=event();e['signals']['ammo']['sequence']=9;self.assertIsNone(m.capture_coast_sample(e,0));h=m.CoastHistory();self.assertTrue(h.observe_typed(event(4)));self.assertFalse(h.observe_typed(event(4)));self.assertFalse(h.observe_typed(event(3)))
 def test_pending_and_history_are_bounded(self):
  h=m.CoastHistory()
  for i in range(1,7):
   e=event(i);h.observe_typed(e);h.observe_full(full(e))
  self.assertLessEqual(len(h.pending),m.MAX_HISTORY);self.assertEqual([x['sequence'] for x in h.reconciled],[4,5,6]);c=h.prompt_context(full(event(7)));self.assertLessEqual(len(c['coast_history']),m.MAX_HISTORY);self.assertLessEqual(len(json.dumps(c,separators=(',',':')).encode()),3*m.MAX_HINT_BYTES+128)
 def test_ineligible_current_snapshot_cannot_be_used(self):
  h=m.CoastHistory();self.assertEqual(h.prompt_context({'event':'observation','exact':False,'sequence':8})['coast_history'],[])
if __name__=='__main__':unittest.main(verbosity=2)
