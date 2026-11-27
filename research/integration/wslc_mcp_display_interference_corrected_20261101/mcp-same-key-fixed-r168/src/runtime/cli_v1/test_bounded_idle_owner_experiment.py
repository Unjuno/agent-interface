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
 def test_invalid_idle_cancel_reply_quarantines_without_cleanup(self):
  with tempfile.TemporaryDirectory() as td:
   root=Path(td);(root/'block-capture').write_text('block')
   owner=OwnedGuardedSessionOwner({'app':20},td,':fake-owned-idle',process_identity=True,query_worker=True,
                                  observation_worker=True,_owner_factory=fake_process_owner)
   original=None;reader=None;errors=[]
   try:
    owner.get();original=owner._control
    class InvalidReply:
     def send(self,request):pass
     def poll(self,timeout):return True
     def recv(self):return {'ok':False,'error':'invalid'}
    owner._control=InvalidReply()
    def observe():
     try:owner.observe_idle_until(deadline_ns=time.monotonic_ns()+1_000_000_000,cancel_token='invalid-ack')
     except Exception as e:errors.append(e)
    reader=threading.Thread(target=observe);reader.start();end=time.monotonic()+2
    while not (root/'capture-entered').exists() and time.monotonic()<end:time.sleep(.005)
    self.assertTrue((root/'capture-entered').exists())
    with patch.object(owner,'_cleanup_after_owner_retirement',side_effect=AssertionError('unfenced cleanup')):
     result=owner.cancel_guarded('invalid-ack')
    self.assertEqual(result['status'],'cancel_unconfirmed');self.assertFalse(result['release_attempted'])
    self.assertEqual(owner.state,'failed');self.assertTrue(owner.review_required)
    (root/'resume-capture').write_text('resume');reader.join(2)
    self.assertFalse(reader.is_alive());self.assertEqual(len(errors),1)
   finally:
    (root/'resume-capture').write_text('resume')
    if reader is not None:reader.join(2)
    if original is not None:owner._control=original
    owner.close()

 def test_first_idle_observation_refused_while_owner_is_closing(self):
  with tempfile.TemporaryDirectory() as td:
   root=Path(td);owner=OwnedGuardedSessionOwner({'app':20},td,':fake-owned-idle',process_identity=True,query_worker=True,
                                               observation_worker=True,_owner_factory=fake_process_owner)
   entered,resume=threading.Event(),threading.Event();worker=None
   try:
    owner.get();original=owner._request_locked
    def delayed(method,arguments=None):
     if method=='close':
      entered.set()
      if not resume.wait(2):raise RuntimeError('fixture timed out')
     return original(method,arguments)
    with patch.object(owner,'_request_locked',side_effect=delayed):
     worker=threading.Thread(target=owner.close);worker.start();self.assertTrue(entered.wait(1))
     with self.assertRaisesRegex(RuntimeError,'closing'):
      owner.observe_idle_until(deadline_ns=time.monotonic_ns()+1_000_000_000,cancel_token='too-late')
     self.assertFalse((root/'capture-entered').exists())
   finally:
    resume.set()
    if worker is not None:worker.join(3)
    owner.close()

 def test_new_owner_rpc_refused_while_idle_cancel_reply_is_inflight(self):
  with tempfile.TemporaryDirectory() as td:
   root=Path(td);(root/'block-capture').write_text('block')
   owner=OwnedGuardedSessionOwner({'app':20},td,':fake-owned-idle',process_identity=True,query_worker=True,
                                  observation_worker=True,_owner_factory=fake_process_owner)
   sent,finish=threading.Event(),threading.Event();results=[];errors=[];reader=canceller=None;original=None
   try:
    owner.get();original=owner._control
    class DelayedReply:
     def send(self,request):sent.set()
     def poll(self,timeout):finish.wait(2);return True
     def recv(self):return {'ok':True,'result':{'status':'not_active'},'snapshot':{}}
    owner._control=DelayedReply()
    def observe():
     try:results.append(owner.observe_idle_until(deadline_ns=time.monotonic_ns()+3_000_000_000,cancel_token='delayed-cancel'))
     except Exception as e:errors.append(e)
    reader=threading.Thread(target=observe);reader.start();end=time.monotonic()+2
    while not (root/'capture-entered').exists() and time.monotonic()<end:time.sleep(.005)
    self.assertTrue((root/'capture-entered').exists())
    canceller=threading.Thread(target=lambda:owner.cancel_guarded('delayed-cancel'));canceller.start();self.assertTrue(sent.wait(1))
    (root/'resume-capture').write_text('resume');reader.join(2)
    self.assertFalse(reader.is_alive());self.assertEqual(errors,[]);self.assertEqual(results[0]['status'],'observed')
    with self.assertRaisesRegex(RuntimeError,'cancel.*in.flight'):
     owner.invoke_guarded('guarded_observe',{},root/'next-call')
    close=owner.close()
    self.assertEqual(close['status'],'cleanup_deferred')
    self.assertFalse(close['release_attempted']);self.assertFalse(close['release_confirmed'])
   finally:
    finish.set();(root/'resume-capture').write_text('resume')
    if reader is not None:reader.join(2)
    if canceller is not None:canceller.join(2)
    if original is not None:owner._control=original
    owner.close()

 def test_late_successful_idle_cancel_response_stays_quarantined(self):
  with tempfile.TemporaryDirectory() as td:
   root=Path(td);(root/'block-owner-return').write_text('block')
   owner=OwnedGuardedSessionOwner({'app':20},td,':fake-owned-idle',process_identity=True,query_worker=True,
                                  observation_worker=True,_owner_factory=fake_process_owner)
   sent,finish=threading.Event(),threading.Event();results=[];errors=[];original=None;reader=canceller=None
   try:
    owner.get();original=owner._control
    class DelayedReply:
     def send(self,request):sent.set()
     def poll(self,timeout):finish.wait(2);return True
     def recv(self):return {'ok':True,'result':{'status':'cancel_requested'},'snapshot':{'state':'open','review_required':False}}
    owner._control=DelayedReply()
    def observe():
     try:owner.observe_idle_until(deadline_ns=time.monotonic_ns()+400_000_000,cancel_token='late-ack')
     except Exception as e:errors.append(e)
    reader=threading.Thread(target=observe);reader.start();end=time.monotonic()+2
    while not (root/'owner-return-entered').exists() and time.monotonic()<end:time.sleep(.005)
    self.assertTrue((root/'owner-return-entered').exists())
    with patch.object(owner,'_cleanup_after_owner_retirement',side_effect=AssertionError('unfenced cleanup')):
     canceller=threading.Thread(target=lambda:results.append(owner.cancel_guarded('late-ack')));canceller.start()
     self.assertTrue(sent.wait(1));reader.join(2);self.assertFalse(reader.is_alive())
     finish.set();canceller.join(2);self.assertFalse(canceller.is_alive())
    self.assertEqual(len(errors),1);self.assertEqual(results[0]['status'],'cancel_unconfirmed')
    self.assertEqual(results[0]['cleanup_status'],'UNKNOWN');self.assertFalse(results[0]['release_attempted'])
    self.assertEqual(owner.state,'failed');self.assertTrue(owner.review_required)
   finally:
    finish.set();(root/'resume-owner-return').write_text('resume')
    if reader is not None:reader.join(2)
    if canceller is not None:canceller.join(2)
    if original is not None:owner._control=original
    owner.close()

 def test_idle_observe_refuses_while_ordinary_cancel_is_inflight(self):
  with tempfile.TemporaryDirectory() as td:
   root=Path(td);sent,finish=threading.Event(),threading.Event()
   owner=OwnedGuardedSessionOwner({'app':20},td,':fake-owned-idle',process_identity=True,query_worker=True,
                                  observation_worker=True,_owner_factory=fake_process_owner)
   original=None;worker=None
   try:
    owner.get();original=owner._control
    class DelayedControl:
     def send(self,request):sent.set()
     def poll(self,timeout):finish.wait(2);return False
    owner._control=DelayedControl()
    with patch.object(owner,'_cleanup_after_owner_retirement',return_value=({'status':'unknown'},{'status':'not_attempted'})):
     worker=threading.Thread(target=lambda:owner.cancel_guarded('earlier-cancel'));worker.start();self.assertTrue(sent.wait(1))
     with self.assertRaisesRegex(RuntimeError,'cancel.*in.flight'):
      owner.observe_idle_until(deadline_ns=time.monotonic_ns()+1_000_000_000,cancel_token='idle-race')
     self.assertFalse((root/'capture-entered').exists())
     finish.set();worker.join(2);self.assertFalse(worker.is_alive())
   finally:
    finish.set()
    if worker is not None:worker.join(2)
    if original is not None:owner._control=original
    owner.close()

 def test_inflight_cancel_must_not_release_after_idle_timeout(self):
  with tempfile.TemporaryDirectory() as td:
   root=Path(td);(root/'block-owner-return').write_text('block')
   owner=OwnedGuardedSessionOwner({'app':20},td,':fake-owned-idle',process_identity=True,query_worker=True,
                                  observation_worker=True,_owner_factory=fake_process_owner)
   sent,allow_poll=threading.Event(),threading.Event();obs_errors=[];cancel_results=[];cancel_errors=[]
   original_control=None;observe_thread=cancel_thread=None
   try:
    owner.get();original_control=owner._control
    class DelayedControl:
     def send(self,request):sent.set()
     def poll(self,timeout):allow_poll.wait(2);return False
    owner._control=DelayedControl()
    def observe():
     try:owner.observe_idle_until(deadline_ns=time.monotonic_ns()+400_000_000,cancel_token='race-capture')
     except Exception as error:obs_errors.append(error)
    def cancel():
     try:cancel_results.append(owner.cancel_guarded('race-capture'))
     except Exception as error:cancel_errors.append(error)
    observe_thread=threading.Thread(target=observe);observe_thread.start();until=time.monotonic()+2
    while not (root/'owner-return-entered').exists() and time.monotonic()<until:time.sleep(.005)
    self.assertTrue((root/'owner-return-entered').exists())
    with patch.object(owner,'_cleanup_after_owner_retirement',side_effect=AssertionError('unfenced cleanup')):
     cancel_thread=threading.Thread(target=cancel);cancel_thread.start();self.assertTrue(sent.wait(1))
     observe_thread.join(2);self.assertFalse(observe_thread.is_alive());self.assertTrue(owner.review_required)
     allow_poll.set();cancel_thread.join(2)
     self.assertFalse(cancel_thread.is_alive());self.assertEqual(cancel_errors,[])
     self.assertEqual(len(cancel_results),1);self.assertFalse(cancel_results[0].get('release_attempted',False))
   finally:
    allow_poll.set();(root/'resume-owner-return').write_text('resume')
    if observe_thread is not None:observe_thread.join(2)
    if cancel_thread is not None:cancel_thread.join(2)
    if original_control is not None:owner._control=original_control
    owner.close()

 def test_quarantined_cancel_cannot_launch_unfenced_cleanup(self):
  with tempfile.TemporaryDirectory() as td:
   root=Path(td);(root/'block-owner-return').write_text('block')
   owner=OwnedGuardedSessionOwner({'app':20},td,':fake-owned-idle',process_identity=True,query_worker=True,
                                  observation_worker=True,_owner_factory=fake_process_owner)
   original_control=None
   try:
    owner.get()
    with self.assertRaisesRegex(RuntimeError,'deadline expired'):
     owner.observe_idle_until(deadline_ns=time.monotonic_ns()+300_000_000,cancel_token='capture-timeout')
    original_control=owner._control
    class TimedOutControl:
     def send(self,request):pass
     def poll(self,timeout):return False
    owner._control=TimedOutControl()
    with patch.object(owner,'_cleanup_after_owner_retirement',side_effect=AssertionError('unfenced cleanup')):
     result=owner.cancel_guarded('capture-timeout')
    self.assertFalse(result.get('release_attempted',False))
    self.assertFalse(result['release_confirmed'])
    self.assertEqual(result.get('cleanup_status'),'UNKNOWN')
   finally:
    if original_control is not None:owner._control=original_control
    (root/'resume-owner-return').write_text('resume');owner.close()

 def test_cancel_after_timeout_cannot_restore_quarantined_owner(self):
  with tempfile.TemporaryDirectory() as td:
   root=Path(td);(root/'block-owner-return').write_text('block')
   owner=OwnedGuardedSessionOwner({'app':20},td,':fake-owned-idle',process_identity=True,query_worker=True,
                                  observation_worker=True,_owner_factory=fake_process_owner)
   try:
    owner.get()
    with self.assertRaisesRegex(RuntimeError,'deadline expired'):
     owner.observe_idle_until(deadline_ns=time.monotonic_ns()+300_000_000,cancel_token='late-cancel')
    self.assertTrue((root/'owner-return-entered').exists())
    owner.cancel_guarded('late-cancel')
    self.assertEqual(owner.state,'failed');self.assertTrue(owner.review_required)
    with self.assertRaisesRegex(RuntimeError,'quarantined'):
     owner.observe_idle_until(deadline_ns=time.monotonic_ns()+1_000_000_000,cancel_token='new-read')
   finally:
    (root/'resume-owner-return').write_text('resume');owner.close()

 def test_quarantined_close_does_not_issue_unfenced_late_release(self):
  with tempfile.TemporaryDirectory() as td:
   root=Path(td);(root/'block-owner-return').write_text('block')
   owner=OwnedGuardedSessionOwner({'app':20},td,':fake-owned-idle',process_identity=True,query_worker=True,
                                  observation_worker=True,_owner_factory=fake_process_owner)
   try:
    owner.get()
    with self.assertRaisesRegex(RuntimeError,'deadline expired'):
     owner.observe_idle_until(deadline_ns=time.monotonic_ns()+300_000_000,cancel_token='close-after-timeout')
    self.assertTrue((root/'owner-return-entered').exists())
    with patch.object(owner,'_retirement_cleanup_result_fields',side_effect=AssertionError('unfenced release')):
     report=owner.close()
    self.assertFalse(report['release_confirmed']);self.assertEqual(report['cleanup_status'],'UNKNOWN')
    self.assertFalse(report['release_attempted'])
   finally:
    (root/'resume-owner-return').write_text('resume')
    owner.close()

 def test_late_owned_response_does_not_restore_quarantined_owner(self):
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
    worker.join(1)
    self.assertFalse(worker.is_alive());self.assertEqual(results,[]);self.assertEqual(len(errors),1)
    self.assertEqual(owner.state,'failed');self.assertTrue(owner.review_required)
    (root/'resume-owner-return').write_text('resume');time.sleep(.1)
    self.assertEqual(owner.state,'failed');self.assertTrue(owner.review_required)
    with self.assertRaisesRegex(RuntimeError,'quarantined'):
     owner.observe_idle_until(deadline_ns=time.monotonic_ns()+1_000_000_000,cancel_token='after-timeout')
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
    with self.assertRaisesRegex(RuntimeError,'deadline expired|idle observation unavailable'):
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
