"""Read-only G10-derived fixtures against the current compiled core.

No G10 actor, OCR, native bridge or historical auditor is executed.
"""
import copy, hashlib, json, unittest
from pathlib import Path
from runtime.core_v1.compiled_gui import run

ROOT=Path(__file__).parent/'calc_current_shared_3311_4d74_20261004'/'calc-compiled-ocrlive-4d74'/'runs'/'compiled_ocrlive10'

class RetainedG10CoreTests(unittest.TestCase):
 def run_fixture(self,unknown_second=False,stale_second=False):
  raw_bytes=(ROOT/'raw.json').read_bytes()
  self.assertEqual(hashlib.sha256(raw_bytes).hexdigest(),'890c68f13e5fa8598bcbb2f456b8ee5319c584249c19492744a7c96f170014bf')
  raw=json.loads(raw_bytes);old=raw['compiled_result'];observations=copy.deepcopy(old['observations']);transitions=old['transitions']
  self.assertEqual((old['outcome'],len(observations),len(transitions)),('TASK_SUCCEEDED',3,2))
  if unknown_second:observations[1]['predicates']['row_visible']='unknown'
  if stale_second:observations[1]['captured_ns']=observations[0]['captured_ns']
  state={'time':old['started_ns'],'observe':0,'execute':0,'verify':0}
  def clock():state['time']+=1;return state['time']
  def observe(_):
   index=state['observe'];state['observe']+=1
   row=copy.deepcopy(observations[index]);state['time']=max(state['time'],row['captured_ns']);row['surface']='owned';return row
  def admit(payload):
   return {'eligible':True,'status':'revalidated','authorization':'fixture-only',
    'expected_sequence':payload['observation']['sequence'],'valid_until_ns':state['time']+1_000_000_000}
  def execute(_):
   row=transitions[state['execute']];state['execute']+=1
   return {'status':'completed','action_id':row['action_id'],'effect_ref':row['effect_ref'],
    'release':{'verified':row['release_verified'],'keys_down':[],'buttons_down':[]}}
  def verify(_):state['verify']+=1;return {'status':'succeeded','evidence_ref':'fixture-effect'}
  result=run(raw['interface'],{'observe':observe,'admit':admit,'execute':execute,'verify_effect':verify,'cancelled':lambda:False},clock=clock)
  return state,result
 def test_retained_observations_and_terminals_drive_two_transitions(self):
  state,result=self.run_fixture()
  self.assertEqual(result['outcome'],'TASK_SUCCEEDED');self.assertEqual(result['completed_transitions'],2)
  self.assertEqual((state['observe'],state['execute'],state['verify']),(3,2,2))
 def test_unknown_first_effect_stops_before_second_action(self):
  state,result=self.run_fixture(unknown_second=True)
  self.assertEqual(result['reason'],'effect_unavailable');self.assertEqual(result['completed_transitions'],1)
  self.assertEqual((state['observe'],state['execute'],state['verify']),(2,1,0))
 def test_stale_effect_observation_stops_before_second_action(self):
  state,result=self.run_fixture(stale_second=True)
  self.assertEqual(result['reason'],'stale_observation');self.assertEqual(result['completed_transitions'],1)
  self.assertEqual(state['execute'],1)
