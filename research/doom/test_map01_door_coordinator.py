import threading,unittest
from map01_door_coordinator import DoorCoordinator
from test_map01_door_task_contract import state,command,finish

class Gate:
 clock_reserve_deadline_ns=5_000_000_000
 def clock(self):return 1_550_000_000
 def _clock_reserve_deadline(self,engine,started):return 1_900_000_000
 def _owner_and_source(self,backend,source,command,started):
  return 'owner',0,{'sample_started_ns':1_520_000_000,'sample_finished_ns':1_540_000_000},{}
 def check_submit(self,command,backend,source,*,terminal,accepted):
  return 1_900_000_000 if command['id']=='cover-0' else 1_800_000_000

class Executor:
 def __init__(self):
  self.lock=threading.RLock();self.active=None;self.calls=[]
  self.admission_publication_errors={};self.terminal_publication_errors={};self.release_publication_errors={}
 def submit(self,*args,**kwargs):self.calls.append((args,kwargs))

class Capture:
 def completed(self,identifier,terminal,accepted,events):self.events=events

class CoordinatorTests(unittest.TestCase):
 def test_cover_is_fixed_once_and_verified_after_idle(self):
  executor=Executor();run=DoorCoordinator('use',Gate(),object(),executor,lambda:1_500_000_000)
  source=state();source['id']='initial'
  c=command('cover-0',[{'op':'coast','duration_ms':200,'sample_ms':100}])
  run.submit_cover(c,source)
  self.assertEqual(executor.calls[0][1],{'admission_deadline_ns':1_900_000_000})
  with self.assertRaises(ValueError):run.submit_cover(c,source)
  captured=Capture();finish(captured,c)
  for event in captured.events:run.record(event)
  self.assertEqual(run.settle(),'DONE')
  self.assertTrue(run.cover_done)
 def test_first_move_is_submitted_only_after_cover_and_binds_both_deadlines(self):
  executor=Executor();run=DoorCoordinator('use',Gate(),object(),executor,lambda:1_500_000_000)
  initial=state();initial['id']='initial'
  cover=command('cover-0',[{'op':'coast','duration_ms':200,'sample_ms':100}])
  run.submit_cover(cover,initial)
  move=command('approach-1',[{'op':'hold','keys':['Up'],'duration_ms':600}],2)
  source=state(2,1_400_000_000);source.update(id='cover-0',step=0,frame_rgb_sha256='a'*64,event='observation',emit_ns=1_700_000_000)
  with self.assertRaises(ValueError):run.submit_next(move,source)
  captured=Capture();finish(captured,cover)
  for event in captured.events:run.record(event)
  self.assertEqual(run.settle(),'DONE')
  run.submit_next(move,source)
  self.assertEqual(len(executor.calls),2)
  self.assertEqual(executor.calls[-1][1],{'admission_deadline_ns':1_800_000_000})
  self.assertEqual(run.contract.deadline,1_800_000_000)
  with self.assertRaises(ValueError):run.submit_next(move,source)
 def test_shorter_cover_lease_is_forwarded(self):
  executor=Executor();run=DoorCoordinator('use',Gate(),object(),executor,lambda:1_500_000_000)
  initial=state();initial['id']='initial'
  cover=command('cover-0',[{'op':'coast','duration_ms':200,'sample_ms':100}])
  cover['valid_until_ns']=1_700_000_000
  run.submit_cover(cover,initial)
  self.assertEqual(executor.calls[0][1],{'admission_deadline_ns':1_700_000_000})
 def test_cover_target_change_is_not_used_for_first_move(self):
  executor=Executor();run=DoorCoordinator('use',Gate(),object(),executor,lambda:1_500_000_000)
  initial=state();initial['id']='initial'
  cover=command('cover-0',[{'op':'coast','duration_ms':200,'sample_ms':100}])
  run.submit_cover(cover,initial)
  captured=Capture();finish(captured,cover)
  for event in captured.events:
   if event.get('event') in ('typed_observation','observation'):
    event['target_process_identity']['digest']='other'
    event['target_renewal_window_identity']['digest']='other-window'
   run.record(event)
  self.assertEqual(run.settle(),'DONE')
  changed=next(event for event in captured.events if event.get('event')=='observation')
  move=command('approach-1',[{'op':'hold','keys':['Up'],'duration_ms':600}],changed['sequence'])
  with self.assertRaises(ValueError):run.submit_next(move,changed)
  self.assertEqual(len(executor.calls),1)
  self.assertFalse(run.journal.ready)
 def test_uncertain_cover_dispatch_is_sticky(self):
  class FailingExecutor(Executor):
   def submit(self,*args,**kwargs):
    super().submit(*args,**kwargs)
    raise RuntimeError('dispatch outcome unknown')
  executor=FailingExecutor();run=DoorCoordinator('use',Gate(),object(),executor,lambda:1_500_000_000)
  source=state();source['id']='initial'
  cover=command('cover-0',[{'op':'coast','duration_ms':200,'sample_ms':100}])
  with self.assertRaises(RuntimeError):run.submit_cover(cover,source)
  self.assertFalse(run.journal.ready)
  with self.assertRaises(ValueError):run.submit_cover(cover,source)
  self.assertEqual(len(executor.calls),1)
 def test_finish_requires_settled_journal(self):
  executor=Executor();run=DoorCoordinator('use',Gate(),object(),executor,lambda:1_500_000_000)
  run.contract.index=5;run.cover_done=True
  self.assertTrue(run.finished)
  run.pending='intervention'
  self.assertFalse(run.finished)
  run.pending=None;run.journal.fail('completion timeout')
  self.assertFalse(run.finished)
 def test_router_rejects_unrelated_operations_and_early_finish(self):
  from map01_door_coordinator import route_door_command
  executor=Executor();run=DoorCoordinator('use',Gate(),object(),executor,lambda:1_500_000_000)
  for op in ('save_fixture','rotate_input_owner','probe_cover_renewal','refresh_owner_source'):
   with self.subTest(op=op),self.assertRaises(ValueError):
    route_door_command({'op':op},run,None)
  with self.assertRaises(ValueError):route_door_command({'op':'finish'},run,None)
  self.assertEqual(route_door_command({'op':'clock'},run,None),'passthrough')
  self.assertEqual(route_door_command({'op':'cancel'},run,None),'passthrough')
 def test_invalid_cover_does_not_dispatch(self):
  executor=Executor();run=DoorCoordinator('control',Gate(),object(),executor,lambda:1_500_000_000)
  source=state();source['id']='initial'
  c=command('cover-0',[{'op':'hold','keys':['e'],'duration_ms':120}])
  with self.assertRaises(ValueError):run.submit_cover(c,source)
  self.assertEqual(executor.calls,[])
if __name__=='__main__':unittest.main()
