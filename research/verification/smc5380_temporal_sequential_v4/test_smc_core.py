"""Construction tests for the SMC temporal trace and SPRT primitives."""
import unittest
from smc_core import *

class CoreTests(unittest.TestCase):
    def test_temporal_unsafe_admission_is_violation(self):
        self.assertTrue(temporal_violation([{"tick":0,"kind":"STALE_RECEIPT"},{"tick":1,"kind":"ACTION_ADMITTED_UNVERIFIED"}]))
    def test_unknown_by_deadline_is_safe(self):
        self.assertFalse(temporal_violation([{"tick":0,"kind":"VERIFIER_TIMEOUT"},{"tick":2,"kind":"UNKNOWN"}]))
    def test_no_terminal_by_deadline_is_violation(self):
        self.assertTrue(temporal_violation([{"tick":0,"kind":"ACK_DROPPED"}]))
    def test_expired_unknown_does_not_satisfy_deadline(self):
        self.assertTrue(temporal_violation([{"tick":3,"kind":"UNKNOWN"}],deadline=2))
    def test_generator_replays_exactly(self):
        self.assertEqual(make_trace(42,"correlated_verifier",P1),make_trace(42,"correlated_verifier",P1))
    def test_p_zero_and_one_trace_labels(self):
        self.assertFalse(one_trace(42,"timeout",0.0)[0])
        self.assertTrue(one_trace(42,"timeout",1.0)[0])
    def test_all_misses_accept_h0(self):
        r=sprt_from_samples([False]*MAX_SAMPLES)
        self.assertEqual(r["decision"],"ACCEPT_H0_AT_P0")
    def test_hits_reject_h0(self):
        r=sprt_from_samples([True]*MAX_SAMPLES)
        self.assertEqual(r["decision"],"FAIL_RATE_AT_OR_ABOVE_P1")
    def test_wilson_zero_event_upper_is_positive(self):
        lo,hi=wilson_interval(0,100)
        self.assertEqual(lo,0.0); self.assertGreater(hi,0.0)
if __name__=="__main__": unittest.main()
