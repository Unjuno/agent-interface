import threading
import unittest
from unittest.mock import Mock, patch

from runtime.cli_v1.owned_guarded_session import OwnedGuardedSessionOwner


class CloseCancelCustodyTests(unittest.TestCase):
    def test_close_during_cancel_does_not_close_supervisor_or_cache_closed(self):
        owner=object.__new__(OwnedGuardedSessionOwner)
        owner._cancel_transaction_lock=threading.Lock()
        owner._cleanup_supervisor=Mock()
        owner.close_report=None;owner._process=None;owner.session_id='session'
        owner.state='open';owner.review_required=False;owner._execution_unknown=False
        owner._cancel_transaction_lock.acquire()
        try:
            with patch('runtime.cli_v1.owned_guarded_session._CLOSE_TIMEOUT_S',0.05):
                result=owner.close()
        finally:
            owner._cancel_transaction_lock.release()
        self.assertEqual(result['status'],'busy')
        self.assertEqual(result['cleanup_status'],'UNKNOWN')
        self.assertFalse(result['release_confirmed'])
        self.assertFalse(result['replay_allowed'])
        self.assertIsNone(owner.close_report)
        self.assertEqual(owner.state,'open')
        owner._cleanup_supervisor.close.assert_not_called()

if __name__=='__main__':unittest.main()
