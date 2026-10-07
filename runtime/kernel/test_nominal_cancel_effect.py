"""Receipt/refusal recovery must not erase possible accepted execution."""
from dataclasses import fields
from types import SimpleNamespace
import unittest

from runtime.kernel import ContractError, EffectOccurrence, RequestLifecycle
from runtime.kernel.test_kernel import observation, binding, lease, request, execution, released


class JointRefusalRecoveryTests(unittest.TestCase):
    def authorized(self):
        flow = RequestLifecycle()
        flow.record_observation(observation())
        flow.bind(binding())
        flow.authorize(lease(), now_ns=200)
        return flow

    def test_refused_nominal_receipt_and_cleanup_preserve_possible_effect(self):
        flow = self.authorized()
        flow.begin_execution(request(), now_ns=300)
        before = vars(flow).copy()
        for value, consume in (
            (execution(), flow.record_execution),
            (released(800), lambda receipt: flow.stop('shaped cleanup', release=receipt)),
        ):
            shaped = SimpleNamespace(**{field.name: getattr(value, field.name) for field in fields(value)})
            with self.assertRaises(ContractError):
                consume(shaped)
            self.assertEqual(vars(flow), before)
        with self.assertRaises(ContractError):
            flow.stop('stale cleanup', release=released(299))
        self.assertEqual(vars(flow), before)
        flow.stop('recorded cleanup', release=released(800))
        result = flow.outcome()
        self.assertEqual(result.command_id, 'cmd-1')
        self.assertTrue(result.effect_occurred)
        self.assertFalse(result.effect_verified)
        self.assertTrue(result.release_verified)

    def test_stop_after_begin_without_receipt_preserves_possible_effect(self):
        flow = self.authorized()
        flow.begin_execution(request(), now_ns=300)
        flow.stop('receipt unavailable', release=released())
        self.assertTrue(flow.outcome().effect_occurred)
        self.assertFalse(flow.outcome().effect_verified)

    def test_stop_before_begin_does_not_claim_possible_effect(self):
        flow = self.authorized()
        flow.stop('before begin', release=released())
        self.assertIsNone(flow.outcome().command_id)
        self.assertFalse(flow.outcome().effect_occurred)

    def test_rejected_begin_does_not_claim_possible_effect(self):
        flow = self.authorized()
        with self.assertRaises(ContractError):
            flow.begin_execution(request(), now_ns=1000)
        flow.stop('expired begin refused', release=released(1000))
        self.assertFalse(flow.outcome().effect_occurred)

    def test_explicit_no_effect_receipt_survives_stop(self):
        flow = self.authorized()
        flow.begin_execution(request(), now_ns=300)
        flow.record_execution(execution(EffectOccurrence.NONE))
        flow.stop('completed without effect')
        self.assertFalse(flow.outcome().effect_occurred)

    def test_stale_cancel_refusal_then_fresh_release_preserves_possible_effect(self):
        flow = self.authorized()
        flow.begin_execution(request(), now_ns=300)
        before = vars(flow).copy()
        with self.assertRaises(ContractError):
            flow.stop('stale cleanup', release=released(299))
        self.assertEqual(vars(flow), before)
        flow.stop('fresh cleanup', release=released(800))
        self.assertTrue(flow.outcome().effect_occurred)
        self.assertFalse(flow.outcome().effect_verified)
        self.assertTrue(flow.outcome().release_verified)


if __name__ == '__main__':
    unittest.main()
