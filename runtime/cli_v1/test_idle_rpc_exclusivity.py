import threading,time,unittest
from unittest.mock import Mock
from runtime.cli_v1.owned_guarded_session import OwnedGuardedSessionOwner

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

if __name__=='__main__':unittest.main()
