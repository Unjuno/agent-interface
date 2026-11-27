"""A pending fixture must not claim its restored clock was measured."""
import json,os,sys,tempfile,types,unittest
from unittest.mock import Mock,patch
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from test_map01_verified_fixture_setup import session_module
class CandidateClockTests(unittest.TestCase):
 def test_candidate_clock_is_a_post_save_observation_not_restore_proof(self):
  s=session_module()
  fields=s.fixture_clock_fields(True,529)
  self.assertIsNone(fields['episode_tic'])
  self.assertEqual(fields['post_save_refresh_episode_tic'],529)
  self.assertIsNone(fields['restored_episode_tic'])
  self.assertEqual(fields['restored_episode_tic_status'],'unmeasured')
  self.assertEqual(s.fixture_clock_fields(False,529),{'episode_tic':529})
 def test_candidate_clock_rejects_invalid_values(self):
  s=session_module()
  for value in (None,True,-1):
   with self.subTest(value=value),self.assertRaises(ValueError):s.fixture_clock_fields(True,value)
 def test_actual_candidate_save_reuses_one_post_refresh_reading(self):
  from test_map01_session_retirement_boundary import command_loop
  for mode in ('loaded','fresh'):
   with self.subTest(mode=mode), tempfile.TemporaryDirectory() as temp:
    run=command_loop(json.dumps({'op':'save_fixture'})+'\n'); scope=run.__globals__
    captured={}; emitted=[]; order=[]
    def write(path,identity,engine,source,fixture):
     order.append('write'); captured.update(fixture)
    def tick():
     order.append('tic'); return 111 if mode=='fresh' and order.count('tic')==1 else 529
    fake_end=types.SimpleNamespace(path=None,display=':120',clock_reserve_deadline_ns=10**30,
      after_load=Mock(),_owner_and_source=Mock(return_value=('owner',0,{},{})))
    scope.update(os=os,CANDIDATE_FIXTURE_SCHEMA='map01_os_input_fixture_candidate_v1',
      close_before_control_effect=lambda *args:None,validate_setup_completed=lambda *args:None,
      validate_fresh_neutral_completed=lambda *args:None,validate_fresh_neutral_snapshot=lambda *args:None,
      require_fresh_neutral_deadline=lambda *args,**kwargs:None,write_verified_fixture=write,
      wait_for_stable_file=lambda *args:order.append('stable'),setup_events=[],
      setup_sources={'coast':{'renewal_owner_id':'owner','input_owner_generation':0}},
      last_accepted={'id':'coast'},last_terminal={'id':'coast'},post_load_gate=object(),
      fresh_gate=types.SimpleNamespace(display=':120'),setup_directory_identity=(1,2))
    root=Path(temp); session=types.SimpleNamespace(tmp=root)
    args=types.SimpleNamespace(out=root,fixture_out=root/'fixture.png',verified_fixture_setup=mode=='loaded',
      fresh_neutral_fixture_setup=mode=='fresh',fixture_setup_program_sha256='a'*64,timeout_seconds=75,
      skill=1,seed=990619)
    game=types.SimpleNamespace(save=lambda path:order.append('save'),advance_action=lambda *args:order.append('advance'),
      get_episode_time=tick)
    backend=types.SimpleNamespace(snapshot=lambda *args:order.append('snapshot'))
    with patch.dict(sys.modules,{'map01_post_load_gate_v1':types.SimpleNamespace(PostLoadGate=lambda *a:fake_end)}):
     run(Mock(),backend,game,args,session,emitted.append,{'sequence':5,'image':'frame'},0)
    saved=next(row for row in emitted if row.get('event')=='fixture_saved')
    expected={'episode_tic':None,'post_save_refresh_episode_tic':529,
              'restored_episode_tic':None,'restored_episode_tic_status':'unmeasured'}
    self.assertEqual({key:captured[key] for key in expected},expected)
    self.assertEqual({key:saved[key] for key in expected},expected)
    self.assertEqual(order.count('tic'),2 if mode=='fresh' else 1)
    self.assertLess(order.index('save'),order.index('advance'))
    self.assertLess(order.index('advance'),order.index('stable'))
    self.assertLess(order.index('stable'),len(order)-1-order[::-1].index('tic'))

 def test_actual_legacy_save_keeps_numeric_clock_receipt(self):
  from test_map01_session_retirement_boundary import command_loop
  with tempfile.TemporaryDirectory() as temp:
   root=Path(temp);run=command_loop(json.dumps({'op':'save_fixture'})+'\n');scope=run.__globals__
   scope.update(os=os,CANDIDATE_FIXTURE_SCHEMA='map01_os_input_fixture_candidate_v1',
     close_before_control_effect=lambda *args:None,wait_for_stable_file=lambda *args:None,
     file_sha256=lambda path:'x',shutil=types.SimpleNamespace(copy2=lambda *args:None))
   args=types.SimpleNamespace(out=root,fixture_out=root/'fixture.png',verified_fixture_setup=False,
     fresh_neutral_fixture_setup=False,timeout_seconds=75,skill=1,seed=990619)
   game=types.SimpleNamespace(save=lambda path:None,advance_action=lambda *args:None,get_episode_time=lambda:529)
   emitted=[]; backend=types.SimpleNamespace(snapshot=lambda *args:None)
   run(Mock(),backend,game,args,types.SimpleNamespace(tmp=root),emitted.append,{'sequence':5,'image':'frame'},0)
   receipt=next(row for row in emitted if row.get('event')=='fixture_saved')
   manifest=json.loads((root/'fixture.json').read_text())
   self.assertEqual(manifest['episode_tic'],529);self.assertEqual(receipt['episode_tic'],529)
   self.assertFalse(any(key in receipt or key in manifest for key in
     ('post_save_refresh_episode_tic','restored_episode_tic','restored_episode_tic_status')))

if __name__=='__main__':unittest.main()
