import threading
import unittest
from concurrent.futures import Future
from unittest.mock import Mock

from runtime.cli_v1.mcp_server import _DeferredOwnerClose
from runtime.cli_v1.owned_guarded_session import OwnedGuardedSessionOwner


class DeferredOwnerCloseTests(unittest.TestCase):
    def test_waits_for_all_futures_and_schedules_only_one_close(self):
        first=Future();second=Future();written=threading.Event();records=[]
        owner=Mock();owner.close_after_cancel_if_retired.return_value={'status':'cleanup_failed','cleanup_status':'UNKNOWN'}
        def write(report):records.append(report);written.set()
        deferred=_DeferredOwnerClose(owner,write)
        self.assertTrue(deferred.arm([first,second]))
        self.assertFalse(deferred.arm([first,second]))
        first.set_result(None)
        self.assertFalse(written.wait(.05));owner.close_after_cancel_if_retired.assert_not_called()
        second.set_result(None)
        self.assertTrue(written.wait(2));owner.close_after_cancel_if_retired.assert_called_once()
        self.assertEqual(records[0]['status'],'cleanup_failed')

    def test_close_exception_is_recorded_as_unknown(self):
        future=Future();written=threading.Event();records=[]
        owner=Mock();owner.close_after_cancel_if_retired.side_effect=RuntimeError('failure')
        def write(report):records.append(report);written.set()
        deferred=_DeferredOwnerClose(owner,write);deferred.arm([future]);future.set_result(None)
        self.assertTrue(written.wait(2))
        self.assertEqual(records[0]['status'],'close_unconfirmed')
        self.assertEqual(records[0]['cleanup_status'],'UNKNOWN')
        self.assertFalse(records[0]['replay_allowed'])

    def test_deferred_close_refuses_without_retired_owner_evidence(self):
        owner=object.__new__(OwnedGuardedSessionOwner)
        owner._cancel_transaction_lock=threading.Lock();owner.session_id='session'
        owner._retirement=None;owner._process=Mock();owner._process.is_alive.return_value=True
        owner._owner_client_disconnect=None;owner._owner_release_attempt=None
        owner._close_owned_transaction=Mock()
        result=owner.close_after_cancel_if_retired()
        self.assertEqual(result['status'],'busy')
        self.assertFalse(result['replay_allowed'])
        owner._close_owned_transaction.assert_not_called()

    def test_deferred_close_accepts_retired_owner_with_prior_cleanup(self):
        owner=object.__new__(OwnedGuardedSessionOwner)
        owner._cancel_transaction_lock=threading.Lock();owner.session_id='session'
        owner._retirement={'retired':True};owner._process=Mock();owner._process.is_alive.return_value=False
        owner._owner_client_disconnect={'status':'unknown'};owner._owner_release_attempt={'status':'not_attempted'}
        owner._close_owned_transaction=Mock(return_value={'status':'cleanup_failed','cleanup_status':'UNKNOWN'})
        result=owner.close_after_cancel_if_retired()
        self.assertEqual(result['status'],'cleanup_failed')
        owner._close_owned_transaction.assert_called_once()

if __name__=='__main__':unittest.main()
