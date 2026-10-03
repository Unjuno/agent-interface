"""Cancellation evidence must follow the first accepted begin in its clock."""
from dataclasses import replace
import unittest

from runtime.kernel import ContractError, RequestLifecycle, Stage
from runtime.kernel.test_kernel import observation, binding, lease, request, released


def authorized():
    flow = RequestLifecycle()
    flow.record_observation(observation())
    flow.bind(binding())
    flow.authorize(lease(), now_ns=200)
    return flow


class CancelReleaseEpochTests(unittest.TestCase):
    def test_prebegin_release_refused_without_mutation(self):
        for ns in (0, 199, 200, 299):
            with self.subTest(ns=ns):
                flow = authorized()
                first = request()
                flow.begin_execution(first, now_ns=300)
                with self.assertRaises(ContractError):
                    flow.stop('cancelled', release=released(ns))
                self.assertEqual(flow.stage, Stage.AUTHORIZED)
                self.assertIs(flow.request, first)
                self.assertIsNone(flow.stop_reason)

    def test_same_or_later_release_accepted(self):
        for ns in (300, 301, 800):
            with self.subTest(ns=ns):
                flow = authorized()
                flow.begin_execution(request(), now_ns=300)
                flow.stop('cancelled', release=released(ns))
                self.assertTrue(flow.outcome().release_verified)

    def test_stale_release_refusal_allows_fresh_cancellation(self):
        flow = authorized()
        flow.begin_execution(request(), now_ns=300)
        with self.assertRaises(ContractError):
            flow.stop('stale', release=released(299))
        flow.stop('fresh', release=released(300))
        self.assertEqual(flow.outcome().reason, 'fresh')

    def test_rejected_first_begin_does_not_create_start_bound(self):
        for req, now in ((request(surface='other'), 300),
                         (request(), 1000), (request(), False)):
            with self.subTest(req=req, now=now):
                flow = authorized()
                with self.assertRaises(ContractError):
                    flow.begin_execution(req, now_ns=now)
                flow.stop('not_started', release=released(0))
                self.assertIsNone(flow.outcome().command_id)

    def test_later_valid_begin_sets_its_own_bound(self):
        flow = authorized()
        with self.assertRaises(ContractError):
            flow.begin_execution(request(surface='other'), now_ns=300)
        flow.begin_execution(request(), now_ns=400)
        with self.assertRaises(ContractError):
            flow.stop('too_early', release=released(350))
        flow.stop('current', release=released(400))
        self.assertTrue(flow.outcome().release_verified)

    def test_duplicate_refusal_preserves_first_begin_bound(self):
        for second in (request(), replace(request(), command_id='other')):
            with self.subTest(second=second):
                flow = authorized()
                flow.begin_execution(request(), now_ns=300)
                with self.assertRaises(ContractError):
                    flow.begin_execution(second, now_ns=400)
                flow.stop('after_first_begin', release=released(350))
                self.assertEqual(flow.outcome().command_id, 'cmd-1')
                self.assertTrue(flow.outcome().release_verified)


if __name__ == '__main__':
    unittest.main()
