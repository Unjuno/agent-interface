"""Receipt admission must use the first successfully accepted begin."""
from dataclasses import replace
import unittest

from runtime.kernel import ContractError, RequestLifecycle, Stage
from runtime.kernel.test_kernel import binding, execution, lease, observation, request, released


def authorized():
    flow = RequestLifecycle()
    flow.record_observation(observation())
    flow.bind(binding())
    flow.authorize(lease(), now_ns=200)
    return flow


def receipt(start, end=700):
    return replace(execution(), started_ns=start, ended_ns=end, release=released(max(end, 800)))


class ExecutionBeginEpochTests(unittest.TestCase):
    def test_prebegin_start_refused_without_consuming_any_state(self):
        for start in (0, 199, 200, 299):
            with self.subTest(start=start):
                flow = authorized()
                flow.begin_execution(request(), now_ns=300)
                before = dict(vars(flow))
                with self.assertRaises(ContractError):
                    flow.record_execution(receipt(start))
                self.assertEqual(set(vars(flow)), set(before))
                for field, original in before.items():
                    self.assertIs(vars(flow)[field], original, field)

    def test_same_tick_and_later_start_are_accepted(self):
        for start, end in ((300, 300), (301, 700), (1200, 1400)):
            with self.subTest(start=start, end=end):
                flow = authorized()
                flow.begin_execution(request(), now_ns=300)
                accepted = receipt(start, end)
                flow.record_execution(accepted)
                self.assertIs(flow.execution, accepted)
                self.assertIs(flow.stage, Stage.EXECUTED)

    def test_refused_receipt_can_be_followed_by_current_receipt(self):
        flow = authorized()
        flow.begin_execution(request(), now_ns=300)
        with self.assertRaises(ContractError):
            flow.record_execution(receipt(299))
        flow.record_execution(receipt(300))
        self.assertIs(flow.stage, Stage.EXECUTED)

    def test_refused_receipt_does_not_disable_verified_cancellation(self):
        flow = authorized()
        flow.begin_execution(request(), now_ns=300)
        with self.assertRaises(ContractError):
            flow.record_execution(receipt(299))
        flow.stop('cancelled', release=released(300))
        self.assertTrue(flow.outcome().release_verified)

    def test_rejected_first_begin_does_not_set_the_bound(self):
        flow = authorized()
        with self.assertRaises(ContractError):
            flow.begin_execution(request(surface='other'), now_ns=600)
        flow.begin_execution(request(), now_ns=300)
        flow.record_execution(receipt(300))
        self.assertIs(flow.stage, Stage.EXECUTED)

    def test_duplicate_begin_does_not_replace_first_bound(self):
        flow = authorized()
        flow.begin_execution(request(), now_ns=300)
        with self.assertRaises(ContractError):
            flow.begin_execution(request(), now_ns=600)
        flow.record_execution(receipt(300))
        self.assertIs(flow.stage, Stage.EXECUTED)

    def test_original_identity_checks_remain_required(self):
        for field, wrong in (('command_id', 'other'), ('invariant_manifest_id', '0' * 64),
                             ('lease_id', 'other'), ('observation_sequence', 8),
                             ('surface_id', 'other'), ('action_count', 2)):
            with self.subTest(field=field):
                flow = authorized()
                flow.begin_execution(request(), now_ns=300)
                with self.assertRaises(ContractError):
                    flow.record_execution(replace(receipt(300), **{field: wrong}))
                self.assertIs(flow.stage, Stage.AUTHORIZED)
                self.assertIsNone(flow.execution)

    def test_receipt_without_successful_begin_is_refused(self):
        flow = authorized()
        with self.assertRaises(ContractError):
            flow.record_execution(receipt(300))
        self.assertIs(flow.stage, Stage.AUTHORIZED)
        self.assertIsNone(flow.request)


if __name__ == '__main__':
    unittest.main()
