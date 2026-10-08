"""Ordinary test-first source checks; not automatic repository discovery."""
import os
import unittest
from fixture import authorized_flow, bound_flow, load_kernel, request_for


class AuthorityBeginOrderTests(unittest.TestCase):
    def setUp(self):
        self.k = load_kernel(os.environ.get('AUTHORITY_ORDER_ARM', 'baseline'))

    def assert_unchanged(self, flow, before):
        self.assertEqual(set(vars(flow)), set(before))
        for name, value in before.items():
            self.assertIs(vars(flow)[name], value, name)

    def test_before_grant_refused_without_mutation(self):
        for ns in (199, 200, 300, 399):
            with self.subTest(ns=ns):
                flow, binding, lease = authorized_flow(self.k, 400)
                before = dict(vars(flow))
                with self.assertRaises(self.k.ContractError):
                    flow.begin_execution(request_for(self.k, binding, lease), now_ns=ns)
                self.assert_unchanged(flow, before)

    def test_equal_later_begin_and_late_receipt_completion(self):
        for ns in (400, 999):
            with self.subTest(ns=ns):
                flow, binding, lease = authorized_flow(self.k, 400)
                req = request_for(self.k, binding, lease)
                flow.begin_execution(req, now_ns=ns)
                self.assertIs(flow.request, req)
                receipt = self.k.ExecutionReceipt('clock-command', 'clock-backend', 'a'*64,
                    'clock-lease', 7, 'clock-surface', ns, 1200, 1,
                    self.k.EffectOccurrence.POSSIBLE, self.k.ReleaseReceipt(1300, True))
                flow.record_execution(receipt)
                self.assertIs(flow.execution, receipt)

    def test_refused_stale_begin_then_corrected_begin(self):
        flow, binding, lease = authorized_flow(self.k, 400)
        req = request_for(self.k, binding, lease)
        before = dict(vars(flow))
        with self.assertRaises(self.k.ContractError):
            flow.begin_execution(req, now_ns=300)
        self.assert_unchanged(flow, before)
        flow.begin_execution(req, now_ns=400)
        self.assertIs(flow.request, req)
        self.assertEqual(flow.execution_started_ns, 400)

    def test_failed_authorization_then_successful_retry(self):
        flow, binding, lease = bound_flow(self.k)
        before = dict(vars(flow))
        with self.assertRaises(self.k.ContractError):
            flow.authorize(lease, now_ns=1000)
        self.assert_unchanged(flow, before)
        self.assertIsNone(getattr(flow, 'authorized_ns', None))
        flow.authorize(lease, now_ns=400)
        after = dict(vars(flow))
        with self.assertRaises(self.k.ContractError):
            flow.authorize(lease, now_ns=200)
        self.assert_unchanged(flow, after)
        flow.begin_execution(request_for(self.k, binding, lease), now_ns=400)

    def test_wrong_request_and_duplicate_begin_preserve_first(self):
        flow, binding, lease = authorized_flow(self.k, 400)
        before = dict(vars(flow))
        with self.assertRaises(self.k.ContractError):
            flow.begin_execution(request_for(self.k, binding, lease, False), now_ns=400)
        self.assert_unchanged(flow, before)
        req = request_for(self.k, binding, lease)
        flow.begin_execution(req, now_ns=400)
        after = dict(vars(flow))
        with self.assertRaises(self.k.ContractError):
            flow.begin_execution(request_for(self.k, binding, lease), now_ns=500)
        self.assert_unchanged(flow, after)

    def test_cancel_without_begin_retains_original_semantics(self):
        flow, _, _ = authorized_flow(self.k, 400)
        flow.stop('cancelled without begin', release=self.k.ReleaseReceipt(0, True))
        self.assertIsNone(flow.outcome().command_id)
        self.assertTrue(flow.outcome().release_verified)

    def test_invalid_clock_values_do_not_consume_begin(self):
        for value in (True, False, 400.0, -1, None, '400'):
            with self.subTest(value=value):
                flow, binding, lease = authorized_flow(self.k, 400)
                before = dict(vars(flow))
                with self.assertRaises(self.k.ContractError):
                    flow.begin_execution(request_for(self.k, binding, lease), now_ns=value)
                self.assert_unchanged(flow, before)

    def test_current_receipt_cancel_release_bounds_preserved(self):
        flow, binding, lease = authorized_flow(self.k, 400)
        req = request_for(self.k, binding, lease)
        flow.begin_execution(req, now_ns=400)
        before = dict(vars(flow))
        stale = self.k.ExecutionReceipt('clock-command', 'clock-backend', 'a'*64,
            'clock-lease', 7, 'clock-surface', 399, 700, 1,
            self.k.EffectOccurrence.POSSIBLE, self.k.ReleaseReceipt(800, True))
        with self.assertRaises(self.k.ContractError):
            flow.record_execution(stale)
        self.assert_unchanged(flow, before)
        with self.assertRaises(self.k.ContractError):
            flow.stop('cancelled', release=self.k.ReleaseReceipt(399, True))
        self.assert_unchanged(flow, before)
        flow.stop('cancelled', release=self.k.ReleaseReceipt(400, True))
        self.assertTrue(flow.outcome().release_verified)
        with self.assertRaises(self.k.ContractError):
            self.k.ExecutionReceipt('clock-command', 'clock-backend', 'a'*64,
                'clock-lease', 7, 'clock-surface', 400, 700, 1,
                self.k.EffectOccurrence.POSSIBLE, self.k.ReleaseReceipt(399, True))


if __name__ == '__main__':
    unittest.main()
