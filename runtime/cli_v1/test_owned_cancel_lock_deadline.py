import threading
import time
import unittest
from unittest.mock import Mock

from runtime.cli_v1.owned_guarded_session import OwnedGuardedSessionOwner


class OwnedCancelLockDeadlineTests(unittest.TestCase):
    def test_contended_control_lock_returns_unknown_without_sending(self):
        owner=object.__new__(OwnedGuardedSessionOwner)
        owner._cancel_transaction_lock=threading.Lock()
        owner._process=Mock();owner._process.is_alive.return_value=True
        owner._control=Mock();owner._control_lock=threading.Lock()
        owner._execution_unknown=False;owner.review_required=False
        owner._control_lock.acquire();results={}
        def invoke():
            try:results['result']=owner.cancel_guarded('op',deadline_monotonic_ns=time.monotonic_ns()+50_000_000)
            except BaseException as exc:results['error']=repr(exc)
        thread=threading.Thread(target=invoke);thread.start()
        thread.join(timeout=0.5);returned_before_unlock=not thread.is_alive()
        owner._control_lock.release();thread.join(timeout=2)
        self.assertTrue(returned_before_unlock,'cancellation waited for a contended lock past its deadline')
        self.assertFalse(thread.is_alive())
        self.assertNotIn('error',results)
        self.assertEqual(results['result']['status'],'cancel_unconfirmed')
        self.assertEqual(results['result']['cleanup_status'],'UNKNOWN')
        self.assertFalse(results['result']['replay_allowed'])
        self.assertTrue(owner.review_required)
        owner._control.send.assert_not_called()

if __name__=='__main__':unittest.main()
