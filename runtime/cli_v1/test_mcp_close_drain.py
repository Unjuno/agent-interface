import unittest
from unittest.mock import Mock

from runtime.cli_v1.mcp_server import _close_owner_after_cancel_drain


class CloseAfterCancelDrainTests(unittest.TestCase):
    def test_executor_shutdown_precedes_normal_close(self):
        order=[];owner=Mock();executor=Mock()
        owner.close.side_effect=lambda:(order.append('close') or {'status':'closed'})
        executor.shutdown.side_effect=lambda **kwargs:order.append('drain-start')
        result=_close_owner_after_cancel_drain(owner,executor,[],drain_timeout_s=0.05)
        self.assertEqual(order,['drain-start','close'])
        self.assertEqual(result['status'],'closed')
        executor.shutdown.assert_called_once_with(wait=False,cancel_futures=False)

    def test_still_busy_is_reported_without_retry(self):
        owner=Mock();owner.close.return_value={'status':'busy'};executor=Mock()
        self.assertEqual(_close_owner_after_cancel_drain(owner,executor,[],drain_timeout_s=0.05)['status'],'busy')
        owner.close.assert_called_once()

    def test_close_exception_still_stops_executor_submissions(self):
        owner=Mock();owner.close.side_effect=RuntimeError('close failure');executor=Mock()
        with self.assertRaises(RuntimeError):_close_owner_after_cancel_drain(owner,executor,[],drain_timeout_s=0.05)
        executor.shutdown.assert_called_once_with(wait=False,cancel_futures=False)

    def test_no_executor_still_closes(self):
        owner=Mock();owner.close.return_value={'status':'closed'}
        self.assertEqual(_close_owner_after_cancel_drain(owner,None,[],drain_timeout_s=0.05)['status'],'closed')

if __name__=='__main__':unittest.main()
