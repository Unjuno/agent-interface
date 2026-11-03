import threading
import time
import unittest
from concurrent.futures import ThreadPoolExecutor
from unittest.mock import Mock

from runtime.cli_v1.mcp_server import _close_owner_after_cancel_drain


class BoundedCancelDrainTests(unittest.TestCase):
    def test_pending_cancel_returns_busy_without_close_then_allows_retry(self):
        entered=threading.Event();release=threading.Event()
        executor=ThreadPoolExecutor(max_workers=1)
        def blocked():
            entered.set()
            if not release.wait(3):raise RuntimeError('fixture timeout')
        future=executor.submit(blocked);owner=Mock();owner.close.return_value={'status':'closed'}
        self.assertTrue(entered.wait(1))
        try:
            started=time.monotonic()
            result=_close_owner_after_cancel_drain(owner,executor,[future],drain_timeout_s=0.05)
            self.assertLess(time.monotonic()-started,0.5)
            self.assertEqual(result['status'],'busy')
            self.assertEqual(result['reason'],'cancellation_drain_timeout')
            self.assertEqual(result['cleanup_status'],'UNKNOWN')
            self.assertFalse(result['replay_allowed'])
            self.assertFalse(future.done())
            owner.close.assert_not_called()
        finally:
            release.set();future.result(timeout=2);executor.shutdown(wait=True)
        result=_close_owner_after_cancel_drain(owner,executor,[future],drain_timeout_s=0.05)
        self.assertEqual(result['status'],'closed')
        owner.close.assert_called_once()

    def test_no_pending_cancel_closes_without_waiting(self):
        owner=Mock();owner.close.return_value={'status':'closed'};executor=ThreadPoolExecutor(max_workers=1)
        result=_close_owner_after_cancel_drain(owner,executor,[],drain_timeout_s=0.05)
        self.assertEqual(result['status'],'closed')
        owner.close.assert_called_once()

if __name__=='__main__':unittest.main()
