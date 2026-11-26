import types,unittest,ast,json,threading,copy
from pathlib import Path
from test_map01_verified_fixture_setup import session_module

def args(**changes):
 data=dict(door_task_arm='control',verified_fixture_setup=False,fresh_neutral_fixture_setup=False,
           load_fixture_manifest=Path('/tmp/candidate.json'),fixture_out=None,
           candidate_setup_evidence=Path('/tmp/evidence.json'),candidate_setup_evidence_sha256='a'*64,
           timeout_seconds=75,seed=990619,skill=1,renewal_passive_observer=True,
           fixture_setup_program_sha256=None,door_expected_manifest_sha256='b'*64,
           door_expected_save_sha256='c'*64,door_expected_iwad_sha256='a8772e088847032510d97ba2312406a6998f21cbab44d4ff10696faa9c0ecd4b',door_expected_restore_tic=870)
 data.update(changes);return types.SimpleNamespace(**data)

class DoorModeTests(unittest.TestCase):
 def test_explicit_door_mode_requires_proof_and_clock_gate(self):
  session=session_module()
  self.assertIsNone(session.validate_verified_fixture_setup(args(),object()))
  for gate,changes in ((None,{}),(object(),{'door_task_arm':'other'}),(object(),{'candidate_setup_evidence':None}),
    (object(),{'candidate_setup_evidence_sha256':'bad'}),(object(),{'fixture_out':Path('/tmp/save.png')}),
    (object(),{'verified_fixture_setup':True}),(object(),{'fresh_neutral_fixture_setup':True}),
    (object(),{'renewal_passive_observer':False}),(object(),{'timeout_seconds':76}),
    (object(),{'seed':2}),(object(),{'skill':2}),(object(),{'load_fixture_manifest':None}),
    (object(),{'door_expected_manifest_sha256':'bad'}),(object(),{'door_expected_save_sha256':None}),
    (object(),{'door_expected_restore_tic':None}),(object(),{'door_expected_iwad_sha256':None}),(object(),{'door_expected_iwad_sha256':'d'*64})):
   with self.subTest(changes=changes),self.assertRaises(ValueError):
    session.validate_verified_fixture_setup(args(**changes),gate)
 def test_door_pins_without_door_mode_are_rejected(self):
  session=session_module()
  with self.assertRaises(ValueError):
   session.validate_verified_fixture_setup(args(door_task_arm=None,candidate_setup_evidence=None,
      candidate_setup_evidence_sha256=None),object())

 def test_traverse_option_requires_door_mode_and_adds_private_variables(self):
  session=session_module()
  with self.assertRaises(ValueError):
   session.validate_verified_fixture_setup(args(door_task_arm=None,door_task_traverse=True,candidate_setup_evidence=None,candidate_setup_evidence_sha256=None,door_expected_manifest_sha256=None,door_expected_save_sha256=None,door_expected_iwad_sha256=None,door_expected_restore_tic=None),object())
  fake=types.SimpleNamespace(**{name:name for name in ('DEATHCOUNT','KILLCOUNT','POSITION_X','POSITION_Y','ANGLE','HEALTH')})
  self.assertEqual(session.door_game_variables(fake,True),['DEATHCOUNT','KILLCOUNT','POSITION_X','POSITION_Y','ANGLE','HEALTH'])
  self.assertEqual(session.door_game_variables(fake,False),['DEATHCOUNT','KILLCOUNT'])
 def test_exit_probe_requires_explicit_traversal_and_door_mode(self):
  session=session_module()
  self.assertIsNone(session.validate_verified_fixture_setup(args(door_task_traverse=True,door_task_exit=True,door_task_exit_arm='control'),object()))
  with self.assertRaises(ValueError):session.validate_verified_fixture_setup(args(door_task_traverse=False,door_task_exit=True,door_task_exit_arm='control'),object())
  with self.assertRaises(ValueError):session.validate_verified_fixture_setup(args(door_task_traverse=True,door_task_exit=True),object())
  with self.assertRaises(ValueError):session.validate_verified_fixture_setup(args(door_task_traverse=True,door_task_exit=False,door_task_exit_arm='control'),object())
  with self.assertRaises(ValueError):session.validate_verified_fixture_setup(args(door_task_arm=None,door_task_traverse=False,door_task_exit=True),object())
 def test_synthetic_scenario_copy_binds_the_read_bytes_exclusively(self):
  import hashlib,tempfile
  from unittest.mock import patch
  session=session_module()
  self.assertTrue(hasattr(session,'copy_synthetic_exit_scenario'))
  with tempfile.TemporaryDirectory() as temp:
   source=Path(temp)/'source.wad';target=Path(temp)/'private.wad';source.write_bytes(b'calibration')
   with patch.object(session,'SYNTHETIC_EXIT_PWAD_SHA256',hashlib.sha256(b'calibration').hexdigest()):
    session.copy_synthetic_exit_scenario(source,target)
    self.assertEqual(target.read_bytes(),b'calibration')
    with self.assertRaises(FileExistsError):session.copy_synthetic_exit_scenario(source,target)
    source.write_bytes(b'changed')
    with self.assertRaises(ValueError):session.copy_synthetic_exit_scenario(source,Path(temp)/'other')
 def test_synthetic_calibration_requires_isolated_fixed_scenario_and_arm(self):
  import tempfile
  from unittest.mock import patch
  session=session_module()
  self.assertTrue(hasattr(session,'validate_synthetic_exit_calibration'))
  with tempfile.TemporaryDirectory() as temp:
   scenario=Path(temp)/'scenario.wad';scenario.write_bytes(b'fixture')
   base=args(door_task_arm=None,door_task_traverse=False,door_task_exit=False,door_task_exit_arm=None,
       load_fixture_manifest=None,candidate_setup_evidence=None,candidate_setup_evidence_sha256=None,
       door_expected_manifest_sha256=None,door_expected_save_sha256=None,door_expected_iwad_sha256=None,
       door_expected_restore_tic=None,synthetic_exit_pwad=scenario,synthetic_exit_arm='use')
   with patch.object(session,'file_sha256',return_value='bd634d97942e6c88f5474d58f4181245d0f7475c9c2ec4595952f3657c5681f3'):
    self.assertIsNone(session.validate_synthetic_exit_calibration(base,None))
    for changes in ({'synthetic_exit_arm':None},{'synthetic_exit_arm':'invalid'},
                    {'door_task_arm':'use'},{'load_fixture_manifest':scenario},
                    {'fixture_out':scenario},{'renewal_passive_observer':False},
                    {'timeout_seconds':76},{'seed':2},{'skill':2}):
     altered=types.SimpleNamespace(**vars(base));altered.__dict__.update(changes)
     with self.subTest(changes=changes),self.assertRaises(ValueError):session.validate_synthetic_exit_calibration(altered,None)
    with self.assertRaises(ValueError):session.validate_synthetic_exit_calibration(base,object())
   with patch.object(session,'file_sha256',return_value='0'*64):
    with self.assertRaises(ValueError):session.validate_synthetic_exit_calibration(base,None)
 def test_binding_must_match_preregistered_candidate(self):
  session=session_module()
  binding={'candidate_manifest_sha256':'b'*64,'candidate_save_sha256':'c'*64,'expected_restore_tic':870}
  session.validate_door_candidate_binding(args(),binding,'a8772e088847032510d97ba2312406a6998f21cbab44d4ff10696faa9c0ecd4b')
  for changed in (dict(binding,candidate_manifest_sha256='d'*64),
                  dict(binding,candidate_save_sha256='d'*64),dict(binding,expected_restore_tic=715),{}):
   with self.subTest(changed=changed),self.assertRaises(ValueError):
    session.validate_door_candidate_binding(args(),changed,'a8772e088847032510d97ba2312406a6998f21cbab44d4ff10696faa9c0ecd4b')
  with self.assertRaises(ValueError):session.validate_door_candidate_binding(args(),binding,'e'*64)
 def test_actual_session_loop_marks_unfinished_eof_as_hold(self):
  source=Path(__file__).with_name('session_map01_v12.py')
  tree=ast.parse(source.read_text())
  main=next(node for node in tree.body if isinstance(node,ast.FunctionDef) and node.name=='main')
  loop=next(node for node in ast.walk(main) if isinstance(node,ast.For)
            and isinstance(node.iter,ast.Attribute) and node.iter.attr=='stdin')
  wrapper=ast.parse('def run():\n pass\n')
  wrapper.body[0].body=[loop]
  ast.fix_missing_locations(wrapper)
  events=[]
  scope={'sys':types.SimpleNamespace(stdin=[]),'door_coordinator':types.SimpleNamespace(pending='approach-1'),
         'emit':events.append}
  exec(compile(wrapper,str(source),'exec'),scope)
  with self.assertRaisesRegex(RuntimeError,'before finish'):scope['run']()
  self.assertEqual(events,[{'event':'door_settle','status':'HOLD','operation_id':'approach-1','reason':'stdin_eof_before_finish'}])
  scope['door_coordinator']=None;self.assertIsNone(scope['run']())
 def test_actual_loop_routes_door_submit_once_before_eof_hold(self):
  source=Path(__file__).with_name('session_map01_v12.py');tree=ast.parse(source.read_text())
  main=next(node for node in tree.body if isinstance(node,ast.FunctionDef) and node.name=='main')
  loop=next(node for node in ast.walk(main) if isinstance(node,ast.For)
            and isinstance(node.iter,ast.Attribute) and node.iter.attr=='stdin')
  wrapper=ast.parse('def run():\n pass\n');wrapper.body[0].body=[loop];ast.fix_missing_locations(wrapper)
  class Coordinator:
   cover_done=False
   pending='cover-0'
   def __init__(self):self.calls=[]
   def submit_cover(self,command,source):self.calls.append((command,source))
  class Executor:
   def submit(self,*args,**kwargs):raise AssertionError('ordinary submit must not run')
  coordinator=Coordinator();events=[];source_row={'id':'initial','sequence':1}
  command={'op':'submit','id':'cover-0','steps':[]}
  scope={'sys':types.SimpleNamespace(stdin=[json.dumps(command)]),'door_coordinator':coordinator,
         'emit':events.append,'args':types.SimpleNamespace(fresh_neutral_fixture_setup=False,verified_fixture_setup=False),
         'lock':threading.RLock(),'latest_observation':source_row,'deepcopy':copy.deepcopy,
         'json':json,'time':types.SimpleNamespace(perf_counter_ns=lambda:10),'executor':Executor(),
         'Expired':type('Expired',(Exception,),{})}
  exec(compile(wrapper,str(source),'exec'),scope)
  with self.assertRaisesRegex(RuntimeError,'before finish'):scope['run']()
  self.assertEqual(coordinator.calls,[(command,source_row)])
  self.assertEqual(events[-1]['reason'],'stdin_eof_before_finish')
 def test_v15_synthetic_mode_requires_owned_target_and_observer(self):
  import importlib.util
  source=Path(__file__).with_name('session_map01_v15.py')
  spec=importlib.util.spec_from_file_location('synthetic_v15_options',source);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
  self.assertTrue(hasattr(module,'validate_synthetic_runtime_options'))
  required=['--synthetic-exit-pwad','/tmp/map.wad','--synthetic-exit-arm','use',
            '--target-process-identity','--owned-input-service','--renewal-passive-observer']
  self.assertIsNone(module.validate_synthetic_runtime_options(required))
  for flag in ('--target-process-identity','--owned-input-service','--renewal-passive-observer'):
   with self.subTest(flag=flag),self.assertRaises(ValueError):module.validate_synthetic_runtime_options([x for x in required if x!=flag])
  with self.assertRaises(ValueError):module.validate_synthetic_runtime_options(required+['--post-load-clock-gate'])
  with self.assertRaises(ValueError):module.validate_synthetic_runtime_options(required+['--target-window-lifecycle'])
  for abbreviated in ('--synthetic-exit-p','--synthetic-exit-a','--synt'):
   with self.subTest(flag=abbreviated),self.assertRaises(ValueError):
    module.validate_synthetic_runtime_options([abbreviated,'x'])
 def test_v15_requires_owned_process_clock_and_observer(self):
  import importlib.util
  source=Path(__file__).with_name('session_map01_v15.py')
  spec=importlib.util.spec_from_file_location('door_v15_options',source);module=importlib.util.module_from_spec(spec)
  spec.loader.exec_module(module)
  required=['--door-task-arm','use','--target-process-identity','--owned-input-service',
            '--renewal-passive-observer','--post-load-clock-gate']
  module.validate_door_runtime_options(required)
  module.validate_door_runtime_options([])
  for flag in required[2:]:
   with self.subTest(flag=flag),self.assertRaises(ValueError):
    module.validate_door_runtime_options([x for x in required if x!=flag])
  with self.assertRaises(ValueError):module.validate_door_runtime_options(required+['--target-window-lifecycle'])
  with self.assertRaises(ValueError):module.validate_door_runtime_options(['--door-task-arm=use'])
if __name__=='__main__':unittest.main()
