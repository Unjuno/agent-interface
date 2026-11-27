"""Ordering of graceful service retirement and cancellation-channel closure."""
import threading
import unittest
from types import SimpleNamespace
from input_owner_service_adapter import OwnedOwnerAdapter


class AdapterCloseOrderTests(unittest.TestCase):
    def test_service_can_retire_before_parent_closes_control_channel(self):
        adapter=object.__new__(OwnedOwnerAdapter)
        adapter._lock=threading.RLock();adapter._obligation=None
        adapter._attempted=set();adapter._close_result=None;adapter._closed=False;adapter._closing=False
        adapter.service_id='service';adapter.owner_id='owner';adapter.close_timeout=1
        order=[]
        adapter.client=SimpleNamespace(close=lambda:(order.append('ordinary') or {'verified':True}))
        adapter.control=SimpleNamespace(outcomes={},close=lambda:order.append('control'))
        def wait(_timeout):
            order.append('wait')
            return {'verified':'control' not in order}
        adapter.service=SimpleNamespace(wait=wait,close_channel=lambda:order.append('channels'))
        receipt=adapter.close()
        self.assertTrue(receipt['verified'],receipt)
        self.assertLess(order.index('wait'),order.index('control'))


if __name__=='__main__':unittest.main()
