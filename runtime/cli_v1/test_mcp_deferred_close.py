import multiprocessing
import threading
import time
import unittest
from concurrent.futures import Future
from unittest.mock import Mock

from runtime.cli_v1.mcp_server import _DeferredOwnerClose
from runtime.cli_v1.owned_guarded_session import OwnedGuardedSessionOwner


class DeferredOwnerCloseTests(unittest.TestCase):
    def test_late_cancel_after_child_exit_stops_supervisor_without_release(self):
        owner=OwnedGuardedSessionOwner({'app':1}, '/tmp/deferred-close-test')
        child=multiprocessing.get_context('spawn').Process(target=time.sleep,args=(0,))
        child.start();owner._process=child;owner.state='open'
        owner._cleanup_supervisor=Mock()
        owner._cleanup_after_owner_retirement=Mock()
        try:
            child.join(3)
            self.assertEqual(child.exitcode,0)
            report=owner.close_after_cancel_if_retired()
            self.assertTrue(report['owner_process_retired'])
            self.assertEqual(report['owner_process_exitcode'],0)
            self.assertEqual(report['cleanup_status'],'UNKNOWN')
            self.assertFalse(report['release_confirmed'])
            owner._cleanup_after_owner_retirement.assert_not_called()
            owner._cleanup_supervisor.close.assert_called_once()
        finally:
            if child.is_alive():child.terminate()
            child.join(3)

    def test_late_cancel_with_live_child_retires_without_release(self):
        owner=OwnedGuardedSessionOwner({'app':1}, '/tmp/deferred-close-test')
        child=multiprocessing.get_context('spawn').Process(target=time.sleep,args=(30,))
        child.start();owner._process=child;owner.state='open'
        owner._cleanup_supervisor=Mock()
        owner._cleanup_after_owner_retirement=Mock()
        future=Future();written=threading.Event();records=[]
        deferred=_DeferredOwnerClose(owner,lambda report:(records.append(report),written.set()))
        try:
            deferred.arm([future])
            self.assertTrue(child.is_alive())
            future.set_result({'status':'not_active'})
            self.assertTrue(written.wait(5))
            self.assertFalse(child.is_alive())
            self.assertTrue(records[0]['owner_process_retired'])
            self.assertEqual(records[0]['cleanup_status'],'UNKNOWN')
            self.assertFalse(records[0]['release_confirmed'])
            self.assertFalse(records[0]['replay_allowed'])
            self.assertEqual(records[0]['owner_release_attempt']['status'],'not_attempted')
            owner._cleanup_after_owner_retirement.assert_not_called()
            owner._cleanup_supervisor.close.assert_called_once()
        finally:
            if child.is_alive():child.terminate()
            child.join(3)

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
        owner._retire=Mock(return_value={'retired':False})
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
