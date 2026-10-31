"""Local prototype: bounded idle capture through the actual guarded owner."""
from types import SimpleNamespace
import tempfile,threading,time,unittest
from pathlib import Path
from unittest.mock import patch
from runtime.cli_v1.mcp_guarded import GuardedSessionOwner
from runtime.cli_v1.test_mcp_process_identity import FakeX
from runtime.guarded_x11_v1.test_observation_worker import reader_backend
from runtime.cli_v1.owned_guarded_session import OwnedGuardedSessionOwner
from runtime.cli_v1.test_mcp_owned_process import _Cleanup

def fake_process_owner(targets,directory,display_name,options):
 cleanup=_Cleanup();fake=FakeX(cleanup);fake.backend.d.get_display_name=lambda:':fake-owned-idle'
 fake.backend.d.display=SimpleNamespace(info=SimpleNamespace(resource_id_base=0x1200000))
 root=Path(directory)
 def capture(*args):
  (root/'capture-entered').write_text('entered')
  while (root/'block-capture').exists() and not (root/'resume-capture').exists():time.sleep(.005)
  return SimpleNamespace(data=fake.raw,depth=24,visual=1)
 backend=reader_backend(fake,capture);backend.d.create_resource_object=lambda kind,xid:SimpleNamespace(id=xid)
 for name,kw in [('runtime.guarded_x11_v1.observation_worker.open_readonly_backend',{'return_value':backend}),
                 ('runtime.guarded_x11_v1.observation_worker.read_linux_x11_process_identity',{'return_value':fake.generation})]:
  p=patch(name,**kw);p.start();cleanup.addCleanup(p.stop)
 owner=GuardedSessionOwner(targets,directory,display_name,**options);owner._owned_process_test_cleanup=cleanup
 if (root/'block-owner-return').exists():
  original=owner.observe_idle_until
  def blocked_return(**kwargs):
   result=original(**kwargs);(root/'owner-return-entered').write_text('entered')
   while not (root/'resume-owner-return').exists():time.sleep(.005)
   return result
  owner.observe_idle_until=blocked_return
 return owner


class BoundedIdleOwnerExperiment(unittest.TestCase):
 def exercise(self, blocked):
  fake=FakeX(self);fake.backend.d.get_display_name=lambda:':fake-owner-idle'
  fake.backend.d.create_resource_object=lambda kind,xid:SimpleNamespace(id=xid)
  entered,resume,closed=threading.Event(),threading.Event(),threading.Event()
  def capture(*args):
   entered.set()
   if blocked and not resume.wait(2):raise RuntimeError('test did not resume')
   return SimpleNamespace(data=fake.raw,depth=24,visual=1)
  backend=reader_backend(fake,capture);backend.d.create_resource_object=lambda kind,xid:SimpleNamespace(id=xid)
  backend.d.close=lambda:closed.set()
  with tempfile.TemporaryDirectory() as td, \
       patch('runtime.guarded_x11_v1.observation_worker.open_readonly_backend',return_value=backend), \
       patch('runtime.guarded_x11_v1.observation_worker.read_linux_x11_process_identity',return_value=fake.generation):
   owner=GuardedSessionOwner({'app':20},td,':fake-owner-idle',process_identity=True,query_worker=True,observation_worker=True)
   owner.get();self.assertTrue(hasattr(owner,'observe_idle_until'),'bounded owner entry point absent')
   results=[];errors=[]
   def invoke():
    try:results.append(owner.observe_idle_until(deadline_ns=time.monotonic_ns()+1_000_000_000,cancel_token='owner-idle'))
    except BaseException as e:errors.append(e)
   worker=threading.Thread(target=invoke);worker.start()
   try:
    self.assertTrue(entered.wait(1))
    if blocked:
     ack=owner.cancel_guarded('owner-idle');self.assertEqual(ack['status'],'cancel_requested')
     worker.join(1);self.assertFalse(worker.is_alive());self.assertEqual(results,[])
     self.assertEqual(len(errors),1);self.assertEqual(owner.bridge.sequence,0)
     self.assertTrue(owner.bridge.review_required)
     resume.set();self.assertTrue(closed.wait(2));self.assertEqual(owner.bridge.sequence,0)
    else:
     worker.join(1);self.assertFalse(worker.is_alive());self.assertEqual(errors,[])
     self.assertEqual(results[0]['status'],'observed');self.assertEqual(results[0]['source']['sequence'],1)
     self.assertEqual(results[0]['observation_report']['status'],'returned')
     self.assertFalse(results[0]['observation_report']['input_dispatched'])
    self.assertEqual(fake.emissions,[])
   finally:
    resume.set();worker.join(2);owner.close()
 def test_owner_healthy_capture(self):self.exercise(False)
 def test_owner_cancel_blocked_capture_discards_late_frame(self):self.exercise(True)

class BoundedIdleOwnedProcessExperiment(unittest.TestCase):
 def test_characterize_parent_accepts_late_owned_response(self):
  with tempfile.TemporaryDirectory() as td:
   root=Path(td);(root/'block-owner-return').write_text('block')
   owner=OwnedGuardedSessionOwner({'app':20},td,':fake-owned-idle',process_identity=True,query_worker=True,
                                  observation_worker=True,_owner_factory=fake_process_owner)
   results=[];errors=[];worker=None
   try:
    owner.get();deadline=time.monotonic_ns()+300_000_000
    def invoke():
     try:results.append(owner.observe_idle_until(deadline_ns=deadline,cancel_token='owned-late'))
     except Exception as error:errors.append(error)
    worker=threading.Thread(target=invoke);worker.start();end=time.monotonic()+2
    while not (root/'owner-return-entered').exists() and time.monotonic()<end:time.sleep(.005)
    self.assertTrue((root/'owner-return-entered').exists())
    while time.monotonic_ns()<=deadline:time.sleep(.005)
    self.assertTrue(worker.is_alive())
    (root/'resume-owner-return').write_text('resume');worker.join(2)
    self.assertFalse(worker.is_alive());self.assertEqual(errors,[])
    self.assertEqual(results[0]['status'],'observed');self.assertEqual(results[0]['source']['sequence'],1)
    self.assertGreater(time.monotonic_ns(),deadline)
   finally:
    (root/'resume-owner-return').write_text('resume')
    if worker is not None:worker.join(2)
    owner.close()

 def test_parent_discards_response_delayed_past_observation_deadline(self):
  with tempfile.TemporaryDirectory() as td:
   root=Path(td);(root/'block-owner-return').write_text('block')
   owner=OwnedGuardedSessionOwner({'app':20},td,':fake-owned-idle',process_identity=True,query_worker=True,
                                  observation_worker=True,_owner_factory=fake_process_owner)
   results=[];errors=[];worker=None
   try:
    owner.get();deadline=time.monotonic_ns()+300_000_000
    def invoke():
     try:results.append(owner.observe_idle_until(deadline_ns=deadline,cancel_token='owned-return'))
     except Exception as error:errors.append(error)
    worker=threading.Thread(target=invoke);worker.start();end=time.monotonic()+2
    while not (root/'owner-return-entered').exists() and time.monotonic()<end:time.sleep(.005)
    self.assertTrue((root/'owner-return-entered').exists())
    worker.join(.7)
    self.assertFalse(worker.is_alive(),'parent RPC still blocks after the observation deadline')
    self.assertEqual(results,[]);self.assertEqual(len(errors),1)
   finally:
    (root/'resume-owner-return').write_text('resume')
    if worker is not None:worker.join(2)
    owner.close()

 def test_spawned_owner_deadline_discards_late_capture(self):
  with tempfile.TemporaryDirectory() as td:
   root=Path(td);(root/'block-capture').write_text('block')
   owner=OwnedGuardedSessionOwner({'app':20},td,':fake-owned-idle',process_identity=True,query_worker=True,
                                  observation_worker=True,_owner_factory=fake_process_owner)
   try:
    owner.get();start=time.monotonic_ns()
    with self.assertRaisesRegex(RuntimeError,'idle observation unavailable'):
     owner.observe_idle_until(deadline_ns=start+300_000_000,cancel_token='owned-expiry')
    self.assertTrue((root/'capture-entered').exists())
    self.assertEqual(owner.snapshot()['observation_sequence'],0);self.assertTrue(owner.review_required)
    (root/'resume-capture').write_text('resume')
    self.assertEqual(owner.snapshot()['observation_sequence'],0)
   finally:
    (root/'resume-capture').write_text('resume');owner.close()

 def test_spawned_owner_cancel_stops_blocked_read_without_publishing(self):
  with tempfile.TemporaryDirectory() as td:
   root=Path(td);(root/'block-capture').write_text('block')
   owner=OwnedGuardedSessionOwner({'app':20},td,':fake-owned-idle',process_identity=True,query_worker=True,
                                  observation_worker=True,_owner_factory=fake_process_owner)
   results=[];errors=[];worker=None
   try:
    owner.get()
    def invoke():
     try:results.append(owner.observe_idle_until(deadline_ns=time.monotonic_ns()+3_000_000_000,cancel_token='owned-blocked'))
     except Exception as error:errors.append(error)
    worker=threading.Thread(target=invoke);worker.start();end=time.monotonic()+2
    while not (root/'capture-entered').exists() and time.monotonic()<end:time.sleep(.005)
    self.assertTrue((root/'capture-entered').exists())
    ack=owner.cancel_guarded('owned-blocked')
    self.assertEqual(ack['status'],'cancel_requested')
    worker.join(2);self.assertFalse(worker.is_alive());self.assertEqual(results,[]);self.assertEqual(len(errors),1)
    self.assertTrue(owner.review_required)
    (root/'resume-capture').write_text('resume')
    self.assertEqual(owner.snapshot()['observation_sequence'],0)
   finally:
    (root/'resume-capture').write_text('resume')
    if worker is not None:worker.join(2)
    owner.close()

 def test_spawned_owner_returns_a_qualified_capture(self):
  with tempfile.TemporaryDirectory() as td:
   owner=OwnedGuardedSessionOwner({'app':20},td,':fake-owned-idle',process_identity=True,query_worker=True,
                                  observation_worker=True,_owner_factory=fake_process_owner)
   try:
    owner.get()
    result=owner.observe_idle_until(deadline_ns=time.monotonic_ns()+3_000_000_000,cancel_token='owned-idle')
    self.assertEqual(result['status'],'observed');self.assertEqual(result['source']['sequence'],1)
    self.assertFalse(result['observation_report']['input_dispatched'])
   finally:owner.close()
