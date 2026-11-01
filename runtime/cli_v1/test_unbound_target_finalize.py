import os,signal,subprocess,sys,threading,unittest
from unittest.mock import Mock,patch
from runtime.cli_v1.owned_target_session import OwnedTargetGuardedSessionOwner
from runtime.guarded_x11_v1.owned_target_process import OwnedTargetProcess

@unittest.skipUnless(sys.platform.startswith('linux') and callable(getattr(os,'pidfd_open',None))
    and callable(getattr(signal,'pidfd_send_signal',None)), 'Linux pidfd support required')
class FinalizeTests(unittest.TestCase):
    def setUp(self):
        self.target=OwnedTargetProcess.launch([sys.executable,'-c','import time;time.sleep(20)'],disposable=True)
        self.token=self.target.claim_session();self.owner=object.__new__(OwnedTargetGuardedSessionOwner)
        o=self.owner;o._owned_target_process=self.target;o._target_custody=self.token;o._owned_target_binding=None
        o._target_retirement_lock=threading.RLock();o._target_cancel_guard=threading.Lock();o._rpc_lock=threading.Lock();o._control_lock=threading.Lock()
        o._process=Mock();o._process.is_alive.return_value=False;o._process.exitcode=0
        o._retirement={'retired':True,'exitcode':0};o.close_report={'status':'cleanup_failed','cleanup_status':'UNKNOWN','verified':False}
        o._target_identity_supervisor_retirement={'retired':True,'exitcode':0}
    def tearDown(self):
        if self.target.running:signal.pidfd_send_signal(self.target._pidfd,signal.SIGKILL);self.target._process.wait(timeout=2)
        self.target.close(_custody=self.token)
    def kill_target(self):
        signal.pidfd_send_signal(self.target._pidfd,signal.SIGKILL);self.target._process.wait(timeout=2)
    def test_exited_target_handle_closed_without_reclassifying_task(self):
        self.kill_target();fd=self.target._pidfd;result=self.owner.finalize_exited_unbound_target()
        self.assertEqual(result['status'],'handle_closed');self.assertEqual(result['cleanup_status'],'UNKNOWN')
        self.assertFalse(result['replay_allowed']);self.assertIsNone(result['task_success'])
        with self.assertRaises(OSError):os.fstat(fd)
    def test_close_twice_preserves_supervisor_retirement(self):
        self.kill_target();self.owner._owned_target_retirement=None
        supervisor=Mock();supervisor.close.side_effect=[{'retired':True,'exitcode':0},{'retired':True,'exitcode':None}]
        self.owner._target_identity_supervisor=supervisor
        with patch('runtime.cli_v1.owned_guarded_session.OwnedGuardedSessionOwner.close',return_value=self.owner.close_report):
            self.owner.close();self.owner.close()
        self.assertEqual(self.owner.finalize_exited_unbound_target()['status'],'handle_closed')
    def test_ambiguous_close_never_becomes_success_or_closes_reused_fd(self):
        self.kill_target();fd=self.target._pidfd;real_close=os.close
        def ambiguous(number):
            self.assertEqual(number,fd);real_close(number);raise OSError('ambiguous close')
        with patch('runtime.guarded_x11_v1.owned_target_process.os.close',side_effect=ambiguous):
            first=self.owner.finalize_exited_unbound_target()
        self.assertEqual(first['status'],'refused')
        replacement=os.open('/dev/null',os.O_RDONLY)
        try:
            self.assertEqual(replacement,fd)
            second=self.owner.finalize_exited_unbound_target()
            self.assertEqual(second['status'],'refused',second);os.fstat(replacement)
        finally:real_close(replacement)
    def test_live_target_is_not_signalled(self):
        result=self.owner.finalize_exited_unbound_target()
        self.assertEqual(result['status'],'refused');self.assertTrue(self.target.running)
    def test_live_owner_or_supervisor_refuses(self):
        self.kill_target();self.owner._process.is_alive.return_value=True
        self.assertEqual(self.owner.finalize_exited_unbound_target()['status'],'refused')
        self.owner._process.is_alive.return_value=False;self.owner._target_identity_supervisor_retirement={'retired':False}
        self.assertEqual(self.owner.finalize_exited_unbound_target()['status'],'refused');os.fstat(self.target._pidfd)
    def test_bound_target_or_busy_lock_refuses(self):
        self.kill_target();self.owner._owned_target_binding={'status':'bound'}
        self.assertEqual(self.owner.finalize_exited_unbound_target()['status'],'refused')
        self.owner._owned_target_binding=None;self.owner._target_cancel_guard.acquire()
        try:self.assertEqual(self.owner.finalize_exited_unbound_target()['status'],'refused')
        finally:self.owner._target_cancel_guard.release()
        os.fstat(self.target._pidfd)
if __name__=='__main__':unittest.main(verbosity=2)
