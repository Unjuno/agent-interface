"""Launcher preflight rejects reuse and changed trial inputs without allocating."""
import hashlib
import ast
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from map01_east_return_launcher_preflight import validate_unspent, retirement_disposition, validate_runtime_inputs, read_marker

class LauncherPreflightTests(unittest.TestCase):
 def test_runtime_pins_and_git_revision_are_checked_before_claim(self):
  with tempfile.TemporaryDirectory() as temp:
   base=Path(temp);checkout=base/'source';checkout.mkdir();trial=base/'trial';trial.mkdir()
   subprocess.run(['git','init','-q',str(checkout)],check=True)
   names=('session_map01_v12.py','session_map01_v15.py','map01_door_driver_protocol.py','map01_door_coordinator.py','map01_door_journal.py','map01_door_task_contract.py','map01_door_sector_scorer.py','map01_reverse_program.py','map01_candidate_setup_evidence_v1.py','map01_post_load_gate_v1.py','map01_east_return_caller_gate.py','map01_east_return_visual_guard.py','map01_os_east_return_driver.py','map01_east_return_launcher.py','map01_east_return_launcher_preflight.py','map01_east_return_audit.py')
   folder=checkout/'research/doom';folder.mkdir(parents=True)
   for name in names:(folder/name).write_text(name)
   subprocess.run(['git','-C',str(checkout),'add','.'],check=True)
   subprocess.run(['git','-C',str(checkout),'-c','user.name=Test','-c','user.email=test@example.invalid','commit','-qm','fixture'],check=True)
   def git(*args):return subprocess.check_output(['git','-C',str(checkout),*args],text=True).strip()
   python='/home/user/.cache/agent-interface-map01-20261103/bin/python'
   manifest='16f2bcf78b1d7739afd1fa0c141f1bbaee9dd2c9e3ff8e356ef3df743899d8d5';save='4e5b990cba8a86ca8a526ecdc59798c1869ea23c8f53468369e811f41d057ddc'
   evidence='40ef78b09f62fcd1b66cc6dc08257aa7d9d3f75fa0fe0797160c3d8fd48b58dc';wad='a8772e088847032510d97ba2312406a6998f21cbab44d4ff10696faa9c0ecd4b'
   candidate='/home/user/issue59-grandchild-bound-setup-yzkdlh9q/candidate/fixture.json'
   argv=[python,str(folder/'session_map01_v15.py'),'--out',str(trial/'runtime'),'--seed','990619','--timeout-seconds','75','--skill','1','--load-fixture-manifest',candidate,'--target-process-identity','--owned-input-service','--renewal-passive-observer','--post-load-clock-gate','--door-task-arm','use','--door-task-traverse','--door-task-reverse-arm','east-return','--candidate-setup-evidence',str(trial/'evidence.json'),'--candidate-setup-evidence-sha256',evidence,'--door-expected-manifest-sha256',manifest,'--door-expected-save-sha256',save,'--door-expected-iwad-sha256',wad,'--door-expected-restore-tic','870']
   spec={'arm':'east-return','checkout':str(checkout),'python':python,'runtime_argv':argv,'pythonpath':':'.join(str(checkout/x) for x in ('','research/doom','research/live_control','research/observation_gating','research/observation_tiles')),'candidate_manifest_sha256':manifest,'candidate_save_sha256':save,'candidate_evidence_sha256':evidence,'candidate_restore_tic':870,'revision':git('rev-parse','HEAD'),'tree':git('rev-parse','HEAD^{tree}'),'files':{str(folder/name):hashlib.sha256((folder/name).read_bytes()).hexdigest() for name in names}}
   for artifact,source in (('driver_sha256','map01_os_east_return_driver.py'),('launcher_sha256','map01_east_return_launcher.py'),('preflight_sha256','map01_east_return_launcher_preflight.py'),('auditor_sha256','map01_east_return_audit.py')):
    spec[artifact]=spec['files'][str(folder/source)]
   external=base/'external.dat';external.write_bytes(b'pinned external')
   external_sha=hashlib.sha256(external.read_bytes()).hexdigest();spec['files'][str(external)]=external_sha
   baseline=base/'baseline.json';baseline.write_text(json.dumps({'checkout':'/old/source','files':{**{'/old/source/research/doom/'+name:spec['files'][str(folder/name)] for name in names},str(external):external_sha}}))
   baseline_sha=hashlib.sha256(baseline.read_bytes()).hexdigest()
   driver=Path(__file__).with_name('map01_os_east_return_driver.py')
   node=next(x for x in ast.parse(driver.read_text()).body if isinstance(x,ast.FunctionDef) and x.name=='expected_runtime_argv')
   scope={'Path':Path,'root':trial};exec(compile(ast.Module(body=[node],type_ignores=[]),str(driver),'exec'),scope)
   self.assertEqual(scope['expected_runtime_argv'](spec),argv)
   timed=dict(spec,owner_timed_hold=True,runtime_argv=argv+['--owner-timed-hold'])
   self.assertEqual(scope['expected_runtime_argv'](timed),timed['runtime_argv'])
   with self.assertRaisesRegex(ValueError,'timed owner source pins missing'):
    validate_runtime_inputs(trial,timed,expected_checkout=checkout,baseline_path=baseline,baseline_sha256=baseline_sha)
   self.assertIsNone(validate_runtime_inputs(trial,spec,expected_checkout=checkout,baseline_path=baseline,baseline_sha256=baseline_sha))
   with self.assertRaisesRegex(ValueError,'baseline registration digest'):validate_runtime_inputs(trial,spec,expected_checkout=checkout,baseline_path=baseline,baseline_sha256='0'*64)
   changed_external=dict(spec,files=dict(spec['files'],**{str(external):'0'*64}))
   with self.assertRaisesRegex(ValueError,'baseline external'):validate_runtime_inputs(trial,changed_external,expected_checkout=checkout,baseline_path=baseline,baseline_sha256=baseline_sha)
   changed_copy=dict(spec,driver_sha256='0'*64)
   with self.assertRaisesRegex(ValueError,'artifact source'):validate_runtime_inputs(trial,changed_copy,expected_checkout=checkout,baseline_path=baseline,baseline_sha256=baseline_sha)
   missing_external=dict(spec,files={k:v for k,v in spec['files'].items() if k!=str(external)})
   with self.assertRaisesRegex(ValueError,'baseline'):validate_runtime_inputs(trial,missing_external,expected_checkout=checkout,baseline_path=baseline,baseline_sha256=baseline_sha)
   (folder/names[0]).write_text('changed')
   with self.assertRaisesRegex(ValueError,'digest'):validate_runtime_inputs(trial,spec,expected_checkout=checkout,baseline_path=baseline,baseline_sha256=baseline_sha)
   (folder/names[0]).write_text(names[0]);(checkout/'unexpected').write_text('new')
   with self.assertRaisesRegex(ValueError,'dirty'):validate_runtime_inputs(trial,spec,expected_checkout=checkout,baseline_path=baseline,baseline_sha256=baseline_sha)
   self.assertFalse((trial/'claim.json').exists())
 def test_incomplete_marker_is_preserved_as_unknown(self):
  with tempfile.TemporaryDirectory() as temp:
   path=Path(temp)/'marker.json';path.write_bytes(b'{\"properties\":')
   row,status=read_marker(path)
   self.assertIsNone(row);self.assertEqual(status,'invalid_json')
   self.assertEqual(path.read_bytes(),b'{\"properties\":')
   path.write_text('[]');self.assertEqual(read_marker(path),(None,'invalid_shape'))
   path.write_text('{\"passed\":true}');self.assertEqual(read_marker(path),({'passed':True},'valid'))
 def test_missing_runtime_binding_is_refused_before_claim(self):
  with tempfile.TemporaryDirectory() as temp:
   with self.assertRaisesRegex(ValueError,'runtime'):
    validate_runtime_inputs(Path(temp),{},expected_checkout=Path(temp),baseline_path=Path(temp)/'baseline.json',baseline_sha256='0'*64)
 def test_absent_unit_does_not_prove_an_observed_service_retired(self):
  self.assertEqual(retirement_disposition(True,True,False),(True,False))
  self.assertEqual(retirement_disposition(True,True,True),(True,True))
  self.assertEqual(retirement_disposition(True,False,True),(False,False))
 def test_unspent_exact_files_and_pins_are_required(self):
  with tempfile.TemporaryDirectory() as temp:
   root=Path(temp);root.chmod(0o700)
   names=('driver.py','launcher.py','evidence.json','registration.json','visual_guard.py','reference.png','east-reference.png','audit.py','preflight.py')
   for name in names:(root/name).write_bytes(name.encode())
   def sha(name):return hashlib.sha256((root/name).read_bytes()).hexdigest()
   spec={'root':str(root),'launcher_sha256':sha('launcher.py'),'driver_sha256':sha('driver.py'),
    'candidate_evidence_sha256':sha('evidence.json'),'visual_guard_sha256':sha('visual_guard.py'),
    'reference_png_sha256':sha('reference.png'),'east_reference_sha256':sha('east-reference.png'),'auditor_sha256':sha('audit.py'),'preflight_sha256':sha('preflight.py')}
   spec.update(python='/home/user/.cache/agent-interface-map01-20261103/bin/python',schema='map01-east-return-registration-v1',arm='east-return',repeat_limit=1,model_calls=0,unit='map01-east-example.service',unit_options=['UMask=0077','PrivateTmp=yes','PrivateNetwork=yes','RuntimeMaxSec=60s','TimeoutStopSec=5s','KillMode=control-group'])
   self.assertIsNone(validate_unspent(root,spec,expected_east_sha=sha('east-reference.png'),expected_initial_sha=sha('reference.png'),expected_guard_sha=sha('visual_guard.py')))
   missing_python=dict(spec);missing_python.pop('python')
   with self.assertRaisesRegex(ValueError,'python'):validate_unspent(root,missing_python,expected_east_sha=sha('east-reference.png'),expected_initial_sha=sha('reference.png'),expected_guard_sha=sha('visual_guard.py'))
   altered_ref=dict(spec,reference_png_sha256='0'*64)
   with self.assertRaisesRegex(ValueError,'initial reference'):validate_unspent(root,altered_ref,expected_east_sha=sha('east-reference.png'),expected_initial_sha=sha('reference.png'),expected_guard_sha=sha('visual_guard.py'))
   altered=dict(spec,unit_options=['PrivateTmp=no'])
   with self.assertRaisesRegex(ValueError,'isolation'):validate_unspent(root,altered,expected_east_sha=sha('east-reference.png'),expected_initial_sha=sha('reference.png'),expected_guard_sha=sha('visual_guard.py'))
   (root/'claim.json').write_text('{}')
   with self.assertRaisesRegex(ValueError,'unspent'):validate_unspent(root,spec,expected_east_sha=sha('east-reference.png'),expected_initial_sha=sha('reference.png'),expected_guard_sha=sha('visual_guard.py'))
   (root/'claim.json').unlink();(root/'driver.py').write_bytes(b'changed')
   with self.assertRaisesRegex(ValueError,'digest'):validate_unspent(root,spec,expected_east_sha=sha('east-reference.png'),expected_initial_sha=sha('reference.png'),expected_guard_sha=sha('visual_guard.py'))
   (root/'driver.py').write_bytes(b'driver.py')
   with self.assertRaisesRegex(ValueError,'reference'):validate_unspent(root,spec,expected_east_sha='0'*64,expected_initial_sha=sha('reference.png'),expected_guard_sha=sha('visual_guard.py'))
 def test_launcher_refuses_wrong_reference_before_claiming_service(self):
  with tempfile.TemporaryDirectory() as temp:
   root=Path(temp);root.chmod(0o700);here=Path(__file__).parent
   (root/'launcher.py').write_bytes((here/'map01_east_return_launcher.py').read_bytes())
   (root/'preflight.py').write_bytes((here/'map01_east_return_launcher_preflight.py').read_bytes())
   for name in ('driver.py','evidence.json','visual_guard.py','reference.png','east-reference.png','audit.py'):
    (root/name).write_bytes(name.encode())
   def sha(name):return hashlib.sha256((root/name).read_bytes()).hexdigest()
   spec={'root':str(root),'launcher_sha256':sha('launcher.py'),'preflight_sha256':sha('preflight.py'),
    'driver_sha256':sha('driver.py'),'candidate_evidence_sha256':sha('evidence.json'),
    'visual_guard_sha256':sha('visual_guard.py'),'reference_png_sha256':sha('reference.png'),
    'east_reference_sha256':sha('east-reference.png'),'auditor_sha256':sha('audit.py')}
   spec.update(python='/home/user/.cache/agent-interface-map01-20261103/bin/python',schema='map01-east-return-registration-v1',arm='east-return',repeat_limit=1,model_calls=0,unit='map01-east-example.service',unit_options=['UMask=0077','PrivateTmp=yes','PrivateNetwork=yes','RuntimeMaxSec=60s','TimeoutStopSec=5s','KillMode=control-group'])
   registration=root/'registration.json';registration.write_text(json.dumps(spec))
   for flags in ([],['-B']):
    result=subprocess.run([sys.executable,*flags,str(root/'launcher.py'),sha('registration.json')],capture_output=True,text=True,timeout=10)
    self.assertNotEqual(result.returncode,0);self.assertIn('east reference',result.stderr)
    self.assertFalse((root/'claim.json').exists());self.assertFalse((root/'launch.json').exists())
    self.assertFalse((root/'__pycache__').exists())
if __name__=='__main__':unittest.main()
