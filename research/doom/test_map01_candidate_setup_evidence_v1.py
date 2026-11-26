"""Offline seal and setup-only candidate evidence checks."""
import hashlib,json,tempfile,time,types,unittest
from unittest.mock import Mock,patch
from test_map01_verified_fixture_setup import session_module
from pathlib import Path
from map01_candidate_setup_evidence_v1 import read_sealed_directory, verify_setup_candidate, EvidenceError

def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()
class CandidateEvidenceTests(unittest.TestCase):
 def test_seal_requires_exact_inventory_and_hashes(self):
  with tempfile.TemporaryDirectory() as temp:
   root=Path(temp); (root/'value').write_bytes(b'original')
   seal={'passed':True,'complete_service_retirement':True,
         'files':{'value':{'bytes':8,'sha256':digest(root/'value')}}}
   (root/'seal.json').write_text(json.dumps(seal))
   self.assertEqual(read_sealed_directory(root,digest(root/'seal.json')),seal)
   (root/'value').write_bytes(b'changed!')
   with self.assertRaises(EvidenceError):read_sealed_directory(root,digest(root/'seal.json'))
   (root/'value').write_bytes(b'original');(root/'extra').write_bytes(b'extra')
   with self.assertRaises(EvidenceError):read_sealed_directory(root,digest(root/'seal.json'))
 def test_seal_never_accepts_an_unretired_run(self):
  with tempfile.TemporaryDirectory() as temp:
   root=Path(temp);(root/'seal.json').write_text(json.dumps({'passed':True,'complete_service_retirement':False,'files':{}}))
   with self.assertRaises(EvidenceError):read_sealed_directory(root,digest(root/'seal.json'))
 def test_unbound_or_forged_attestation_is_rejected_before_load(self):
  with tempfile.TemporaryDirectory() as temp:
   root=Path(temp); candidate=root/'candidate.json'; candidate.write_text('{}')
   evidence=root/'evidence.json'; evidence.write_text(json.dumps({'schema':'wrong'}))
   with self.assertRaises(EvidenceError):
    verify_setup_candidate(candidate,evidence,'0'*64,'1.3.0','a'*64,1,990619,75,root/'wad')
   with self.assertRaises(EvidenceError):
    verify_setup_candidate(candidate,evidence,digest(evidence),'1.3.0','a'*64,1,990619,75,root/'wad')

 def test_candidate_evidence_is_allowed_only_in_verified_setup_with_hash(self):
  session=session_module()
  with tempfile.TemporaryDirectory() as temp:
   root=Path(temp)
   args=types.SimpleNamespace(verified_fixture_setup=True,load_fixture_manifest=root/'parent.json',
     fixture_out=root/'child.png',renewal_passive_observer=True,fixture_setup_program_sha256='a'*64,
     candidate_setup_evidence=root/'evidence.json',candidate_setup_evidence_sha256='b'*64,timeout_seconds=75)
   self.assertIsNotNone(session.validate_verified_fixture_setup(args,object()))
   for changed,gate in (({'verified_fixture_setup':False},object()),
                        ({'candidate_setup_evidence_sha256':None},object()),
                        ({'candidate_setup_evidence':None},object()),
                        ({'candidate_setup_evidence_sha256':'bad'},object()),({'timeout_seconds':600},object()), ({},None)):
    wrong=types.SimpleNamespace(**{**vars(args),**changed})
    with self.subTest(changed=changed),self.assertRaises(ValueError):
     session.validate_verified_fixture_setup(wrong,gate)

 def test_candidate_load_is_bound_to_bytes_and_exact_restored_tic(self):
  session=session_module()
  with tempfile.TemporaryDirectory() as temp:
   root=Path(temp);source=root/'source.png';dest=root/'copy.png';source.write_bytes(b'save')
   binding={'candidate_save_sha256':digest(source),'expected_restore_tic':528}
   game=types.SimpleNamespace(load=Mock(),get_episode_time=Mock(return_value=528))
   actual,receipt=session.load_setup_candidate(game,source,dest,binding,20,time.perf_counter_ns())
   self.assertEqual(actual,528);self.assertEqual(receipt['observed_restore_tic'],528)
   self.assertLess(receipt['natural_progress_upper_tic'],528)
   game.load.assert_called_once_with(str(dest))
   dest.unlink();source.write_bytes(b'changed');game.load.reset_mock()
   with self.assertRaises(ValueError):session.load_setup_candidate(game,source,dest,binding,20,time.perf_counter_ns())
   game.load.assert_not_called()
   dest.unlink();source.write_bytes(b'save');game.get_episode_time.return_value=529
   with self.assertRaises(ValueError):session.load_setup_candidate(game,source,dest,binding,20,time.perf_counter_ns())
   self.assertEqual(game.load.call_count,1)

 def test_equal_preload_tic_is_rejected_before_engine_load(self):
  session=session_module()
  with tempfile.TemporaryDirectory() as temp:
   root=Path(temp);source=root/'source.png';source.write_bytes(b'save')
   game=types.SimpleNamespace(load=Mock(),get_episode_time=Mock(return_value=528))
   with self.assertRaises(ValueError):
    session.load_setup_candidate(game,source,root/'copy.png',
      {'candidate_save_sha256':digest(source),'expected_restore_tic':528},528,time.perf_counter_ns())
   game.load.assert_not_called()

 def test_bound_parent_load_passes_restore_tic_to_gate_and_provenance(self):
  session=session_module()
  with tempfile.TemporaryDirectory() as temp:
   root=Path(temp);manifest=root/'parent.json';manifest.write_bytes(b'manifest')
   save=root/'save.png';save.write_bytes(b'save');engine_tmp=root/'session';engine_tmp.mkdir()
   binding={'candidate_manifest_sha256':digest(manifest),'candidate_save_sha256':digest(save),
     'expected_restore_tic':528,'source_post_save_tic':529,'evidence_sha256':'a'*64}
   fixture={'save_sha256':digest(save),'episode_tic':529,'setup_input_contract':'setup'}
   game=types.SimpleNamespace(load=Mock(),get_episode_time=Mock(side_effect=[20,528]))
   session_context=types.SimpleNamespace(tmp=engine_tmp)
   gate=types.SimpleNamespace(after_load=Mock(return_value={'passed':True}))
   loaded,gate_result=session.load_bound_fixture(game,session_context,manifest,'engine','wad',1,
       (fixture,save,binding),gate,time.perf_counter_ns())
   self.assertEqual(gate_result,{'passed':True});gate.after_load.assert_called_once_with(game,session_context,expected_tic=528)
   self.assertEqual(loaded['observed_restore_tic'],528)
   self.assertEqual(loaded['setup_candidate_evidence']['source_post_save_tic'],529)
   self.assertEqual(loaded['setup_candidate_evidence']['expected_restore_tic'],528)
   self.assertEqual(loaded['manifest_sha256'],digest(manifest))
   self.assertEqual(game.load.call_count,1)
 def test_bound_parent_bad_copy_never_calls_load_or_gate(self):
  session=session_module()
  with tempfile.TemporaryDirectory() as temp:
   root=Path(temp);manifest=root/'parent.json';manifest.write_bytes(b'manifest')
   save=root/'save.png';save.write_bytes(b'changed');engine_tmp=root/'session';engine_tmp.mkdir()
   binding={'candidate_manifest_sha256':digest(manifest),'candidate_save_sha256':'a'*64,
     'expected_restore_tic':528,'source_post_save_tic':529,'evidence_sha256':'b'*64}
   game=types.SimpleNamespace(load=Mock(),get_episode_time=Mock(return_value=20))
   session_context=types.SimpleNamespace(tmp=engine_tmp)
   gate=types.SimpleNamespace(after_load=Mock())
   with self.assertRaises(ValueError):
    session.load_bound_fixture(game,session_context,manifest,'engine','wad',1,
       ({'save_sha256':'a'*64,'episode_tic':529,'setup_input_contract':'setup'},save,binding),gate,time.perf_counter_ns())
   game.load.assert_not_called();gate.after_load.assert_not_called()

 def test_natural_progress_could_reach_expected_rejects_before_gate(self):
  session=session_module()
  with tempfile.TemporaryDirectory() as temp:
   root=Path(temp);manifest=root/'parent.json';manifest.write_bytes(b'manifest')
   save=root/'save.png';save.write_bytes(b'save');engine_tmp=root/'session';engine_tmp.mkdir()
   binding={'candidate_manifest_sha256':digest(manifest),'candidate_save_sha256':digest(save),
     'expected_restore_tic':528,'source_post_save_tic':529,'evidence_sha256':'b'*64}
   game=types.SimpleNamespace(load=Mock(),get_episode_time=Mock(side_effect=[20,528]))
   gate=types.SimpleNamespace(after_load=Mock())
   with patch.object(session.time,'perf_counter_ns',side_effect=[2_000_000_000,20_000_000_000,20_000_000_001]):
    with self.assertRaises(ValueError):
     session.load_bound_fixture(game,types.SimpleNamespace(tmp=engine_tmp),manifest,'engine','wad',1,
       ({'save_sha256':digest(save),'episode_tic':529,'setup_input_contract':'setup'},save,binding),gate,1_000_000_000)
   game.load.assert_called_once();gate.after_load.assert_not_called()

if __name__=='__main__':unittest.main()
