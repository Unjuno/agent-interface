import unittest
import threading
from concurrent.futures import ThreadPoolExecutor
from unittest.mock import Mock

from runtime.cli_v1.mcp_server import _close_owner_after_cancel_drain


class CloseAfterCancelDrainTests(unittest.TestCase):
    def test_busy_close_is_retried_only_after_executor_drains(self):
        order=[];owner=Mock();executor=Mock()
        def close():
            order.append('close')
            return {'status':'busy'} if len(order)==1 else {'status':'cleanup_failed','cleanup_status':'UNKNOWN'}
        def shutdown(**kwargs):order.append('drain')
        owner.close.side_effect=close;executor.shutdown.side_effect=shutdown
        result=_close_owner_after_cancel_drain(owner,executor)
        self.assertEqual(order,['close','drain','close'])
        self.assertEqual(result['status'],'cleanup_failed')
        executor.shutdown.assert_called_once_with(wait=True,cancel_futures=False)

    def test_normal_close_is_not_repeated(self):
        owner=Mock();owner.close.return_value={'status':'closed'};executor=Mock()
        self.assertEqual(_close_owner_after_cancel_drain(owner,executor)['status'],'closed')
        owner.close.assert_called_once();executor.shutdown.assert_called_once()

    def test_still_busy_is_reported_without_infinite_retry(self):
        owner=Mock();owner.close.return_value={'status':'busy'};executor=Mock()
        self.assertEqual(_close_owner_after_cancel_drain(owner,executor)['status'],'busy')
        self.assertEqual(owner.close.call_count,2)

    def test_close_exception_still_drains_executor(self):
        owner=Mock();owner.close.side_effect=RuntimeError('close failure');executor=Mock()
        with self.assertRaises(RuntimeError):_close_owner_after_cancel_drain(owner,executor)
        executor.shutdown.assert_called_once_with(wait=True,cancel_futures=False)

    def test_real_executor_drains_before_retry(self):
        entered=threading.Event();release=threading.Event();first_close=threading.Event()
        executor=ThreadPoolExecutor(max_workers=1)
        def pending_cancel():
            entered.set()
            if not release.wait(3):raise RuntimeError('fixture timeout')
        executor.submit(pending_cancel)
        self.assertTrue(entered.wait(2))
        owner=Mock();owner.close.side_effect=[{'status':'busy'},{'status':'closed'}]
        result={}
        def close():
            first_close.set()
            result['report']=_close_owner_after_cancel_drain(owner,executor)
        thread=threading.Thread(target=close);thread.start()
        self.assertTrue(first_close.wait(1))
        try:
            thread.join(0.05)
            self.assertTrue(thread.is_alive())
            self.assertEqual(owner.close.call_count,1)
        finally:
            release.set();thread.join(3);executor.shutdown(wait=True)
        self.assertFalse(thread.is_alive())
        self.assertEqual(result['report']['status'],'closed')
        self.assertEqual(owner.close.call_count,2)

if __name__=='__main__':unittest.main()
