import threading,time,unittest
import tempfile
from pathlib import Path
from unittest.mock import Mock
from runtime.cli_v1.owned_guarded_session import OwnedGuardedSessionOwner
from runtime.cli_v1.test_bounded_idle_owner_experiment import fake_process_owner

def make_owner():
 owner=OwnedGuardedSessionOwner.__new__(OwnedGuardedSessionOwner)
 owner._idle_quarantine_lock=threading.RLock();owner._rpc_lock=threading.Lock()
 owner._idle_rpc_quarantined=False;owner._idle_rpc_inflight=False;owner._idle_observation_used=False
 owner._idle_cancel_calls_inflight=0;owner._cancel_calls_inflight=0;owner._idle_closing=False
 owner._process=object();owner.state='open';owner._execution_unknown=False;owner.review_required=False
 owner._cancel_idle_without_cleanup=Mock(return_value={'route':'idle'})
 owner._cancel_guarded_normal=Mock(return_value={'route':'ordinary'})
 return owner

class Exclusivity(unittest.TestCase):
 def test_idle_refused_while_normal_rpc_active_and_cancel_uses_normal_route(self):
  owner=make_owner();entered=threading.Event();resume=threading.Event()
  def normal(method,args):
   entered.set();resume.wait(2)
  owner._request_locked=normal
  worker=threading.Thread(target=lambda:owner._call('invoke_guarded'));worker.start()
  try:
   self.assertTrue(entered.wait(1))
   with self.assertRaisesRegex(RuntimeError,'RPC.*in.flight'):
    owner.observe_idle_until(deadline_ns=time.monotonic_ns()+250_000_000,cancel_token='idle')
   self.assertEqual(owner.cancel_guarded('ordinary')['route'],'ordinary')
  finally:resume.set();worker.join(2)

 def test_normal_rpc_refused_while_idle_reserved(self):
  owner=make_owner();owner._idle_rpc_inflight=True;owner._request_locked=Mock()
  with self.assertRaisesRegex(RuntimeError,'idle.*in.flight'):owner._call('invoke_guarded')
  owner._request_locked.assert_not_called()

class OwnedProcessExclusivity(unittest.TestCase):
 def test_real_owned_process_refuses_rpc_while_idle_capture_is_blocked(self):
  with tempfile.TemporaryDirectory() as td:
   root=Path(td);(root/'block-capture').write_text('block')
   owner=OwnedGuardedSessionOwner({'app':20},td,':fake-owned-idle',process_identity=True,query_worker=True,
                                  observation_worker=True,_owner_factory=fake_process_owner)
   results=[];errors=[];worker=None
   def observe():
    try:results.append(owner.observe_idle_until(deadline_ns=time.monotonic_ns()+3_000_000_000,cancel_token='idle-overlap'))
    except BaseException as error:errors.append(error)
   try:
    owner.get();worker=threading.Thread(target=observe);worker.start();deadline=time.monotonic()+2
    while not (root/'capture-entered').exists() and time.monotonic()<deadline:time.sleep(.005)
    self.assertTrue((root/'capture-entered').exists())
    with self.assertRaisesRegex(RuntimeError,'idle observation in flight'):
     owner.invoke_guarded('guarded_observe',{},root/'rejected')
    self.assertFalse((root/'rejected').exists())
    (root/'resume-capture').write_text('resume');worker.join(2)
    self.assertFalse(worker.is_alive());self.assertEqual(errors,[])
    self.assertEqual(results[0]['status'],'observed')
    self.assertEqual(owner.close()['status'],'closed')
   finally:
    (root/'resume-capture').write_text('resume')
    if worker is not None:worker.join(3)
    owner.close()

if __name__=='__main__':unittest.main()
