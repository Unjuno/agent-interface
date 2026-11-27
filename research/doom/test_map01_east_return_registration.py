"""Registration freezes the bounded program and artifact identities without launching."""
import hashlib
import subprocess
import tempfile
from unittest.mock import patch
import unittest
from pathlib import Path
from map01_east_return_registration import build_spec
from map01_east_return_classification import SCOPED_RULES

class RegistrationTests(unittest.TestCase):
 def test_registration_binds_one_east_trial_and_exact_runtime(self):
  hashes={'driver_sha256':'1'*64,'launcher_sha256':'2'*64,'preflight_sha256':'3'*64,'auditor_sha256':'4'*64}
  spec=build_spec(Path('/tmp/trial'), 'map01-east-ab12.service', Path('/repo'), 'a'*40,'b'*40,{'/repo/source':'c'*64},hashes)
  self.assertEqual(spec['schema'],'map01-east-return-registration-v1');self.assertEqual(spec['arm'],'east-return')
  self.assertEqual(spec['repeat_limit'],1);self.assertEqual(spec['model_calls'],0)
  self.assertTrue(spec['guard_requires_new_frame']);self.assertEqual(spec['endpoint_rules'],SCOPED_RULES)
  self.assertEqual(spec['runtime_argv'][spec['runtime_argv'].index('--door-task-reverse-arm')+1],'east-return')
  self.assertEqual(spec['runtime_argv'][spec['runtime_argv'].index('--out')+1],'/tmp/trial/runtime')
  self.assertEqual(spec['east_reference_sha256'],'89a58ce4069bc4aff69805479164ed2cc9c96a61edb768a6685c1d6ad2fcc9cc')
  self.assertNotIn('--door-task-exit',spec['runtime_argv'])
 def test_registered_artifact_write_is_private_and_exclusive(self):
  from map01_east_return_prepare import write_exclusive
  with tempfile.TemporaryDirectory() as tmp:
   path=Path(tmp)/'artifact';write_exclusive(path,b'first')
   self.assertEqual(path.read_bytes(),b'first');self.assertEqual(path.stat().st_mode & 0o777,0o600)
   with self.assertRaises(FileExistsError):write_exclusive(path,b'second')
   self.assertEqual(path.read_bytes(),b'first')
 def test_timed_hold_is_an_explicit_registered_option(self):
  hashes={'driver_sha256':'1'*64,'launcher_sha256':'2'*64,'preflight_sha256':'3'*64,'auditor_sha256':'4'*64}
  args=(Path('/tmp/trial'),'map01-east-ab12.service',Path('/repo'),'a'*40,'b'*40,{'/repo/source':'c'*64},hashes)
  legacy=build_spec(*args);timed=build_spec(*args,timed_hold=True)
  self.assertNotIn('owner_timed_hold',legacy)
  self.assertEqual(timed['runtime_argv'],legacy['runtime_argv']+['--owner-timed-hold'])
  self.assertIs(timed['owner_timed_hold'],True)
  self.assertEqual(timed['endpoint_rules'],legacy['endpoint_rules'])
  with self.assertRaises(ValueError):build_spec(*args,timed_hold=1)
 def test_longer_turn_is_registered_and_requires_timed_hold(self):
  hashes={'driver_sha256':'1'*64,'launcher_sha256':'2'*64,'preflight_sha256':'3'*64,'auditor_sha256':'4'*64}
  args=(Path('/tmp/trial'),'map01-east-ab12.service',Path('/repo'),'a'*40,'b'*40,{'/repo/source':'c'*64},hashes)
  with self.assertRaises(ValueError):build_spec(*args,arm='east-return-turn75')
  spec=build_spec(*args,arm='east-return-turn75',timed_hold=True)
  self.assertEqual(spec['arm'],'east-return-turn75')
  self.assertEqual(spec['runtime_argv'][spec['runtime_argv'].index('--door-task-reverse-arm')+1],spec['arm'])
  self.assertIs(spec['owner_timed_hold'],True)
 def test_dirty_checkout_refuses_before_any_allocation(self):
  import map01_east_return_prepare as preparer
  with tempfile.TemporaryDirectory() as tmp:
   repo=Path(tmp);subprocess.run(['git','init','-q',str(repo)],check=True)
   (repo/'untracked').write_text('change')
   with patch.object(preparer,'CHECKOUT',repo),patch.object(preparer,'BASELINE',repo/'missing-baseline'):
    with self.assertRaisesRegex(ValueError,'committed and clean'):preparer.prepare()
   self.assertFalse((repo/'missing-baseline').exists())
 def test_reopen_arm_is_registered_only_with_timed_owner(self):
  hashes={'driver_sha256':'1'*64,'launcher_sha256':'2'*64,'preflight_sha256':'3'*64,'auditor_sha256':'4'*64}
  args=(Path('/tmp/trial'),'map01-east-ab12.service',Path('/repo'),'a'*40,'b'*40,{'/repo/source':'c'*64},hashes)
  with self.assertRaises(ValueError):build_spec(*args,arm='east-return-reopen')
  spec=build_spec(*args,arm='east-return-reopen',timed_hold=True)
  self.assertEqual(spec['arm'],'east-return-reopen')
  self.assertEqual(spec['runtime_argv'][spec['runtime_argv'].index('--door-task-reverse-arm')+1],'east-return-reopen')
  self.assertIn('--owner-timed-hold',spec['runtime_argv'])
  self.assertTrue(spec['guard_requires_new_frame'])
  self.assertEqual(spec['endpoint_rules'],SCOPED_RULES)

 def test_invalid_unit_revision_or_hash_is_rejected(self):
  hashes={'driver_sha256':'1'*64,'launcher_sha256':'2'*64,'preflight_sha256':'3'*64,'auditor_sha256':'4'*64}
  with self.assertRaises(ValueError):build_spec(Path('/tmp/trial'),'bad.service',Path('/repo'),'a'*40,'b'*40,{},hashes)
  with self.assertRaises(ValueError):build_spec(Path('/tmp/trial'),'map01-east-ab12.service',Path('/repo'),'bad','b'*40,{},hashes)
  with self.assertRaises(ValueError):build_spec(Path('/tmp/trial'),'map01-east-ab12.service',Path('/repo'),'a'*40,'b'*40,{},dict(hashes,driver_sha256='bad'))
if __name__=='__main__':unittest.main()
