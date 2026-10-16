"""Fault injection: a slow logger must not sit between expiry check and input."""
import time,unittest
from types import SimpleNamespace
from unittest.mock import patch
import session_v3,session_v4
from lease import Lease


class TestInputBoundary(unittest.TestCase):
    def run_case(self,module):
        b=module.Backend.__new__(module.Backend);b.held=set();b.touched=set()
        b.session=SimpleNamespace(d=SimpleNamespace(keysym_to_keycode=lambda _:1,sync=lambda:None))
        b.lease=Lease(time.perf_counter_ns()+100_000_000)
        b.emit=lambda _:time.sleep(.2)
        injections=[]
        with patch.object(module.suite.base.xtest,'fake_input',lambda *a,**kw:injections.append(time.perf_counter_ns())):
            b.raw('a',True)
        return injections[0]-b.lease.deadline
    def test_archived_revision_exposes_logger_gap(self):
        self.assertGreater(self.run_case(session_v3),0)
    def test_current_revision_injects_before_slow_logging(self):
        self.assertLess(self.run_case(session_v4),0)


if __name__=='__main__':unittest.main()
