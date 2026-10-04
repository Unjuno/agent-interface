"""Release observations must belong to the execution's time interval or later."""
from dataclasses import replace
import unittest

from runtime.kernel import ContractError, ReleaseReceipt, RequestLifecycle
from runtime.kernel.test_kernel import binding, execution, lease, observation, request


class ReleaseEpochTests(unittest.TestCase):
    def test_old_empty_snapshot_cannot_complete_new_execution(self):
        for observed_ns in (0, 100, 499):
            with self.subTest(observed_ns=observed_ns):
                flow = RequestLifecycle()
                flow.record_observation(observation())
                flow.bind(binding())
                flow.authorize(lease(), now_ns=200)
                flow.begin_execution(request(), now_ns=300)
                with self.assertRaises(ContractError):
                    receipt = replace(execution(), release=ReleaseReceipt(observed_ns, True))
                    flow.record_execution(receipt)

    def test_unverified_snapshot_still_has_to_be_current(self):
        with self.assertRaises(ContractError):
            replace(execution(), release=ReleaseReceipt(499, False, ("A",)))

    def test_equal_start_does_not_invent_subtick_order(self):
        receipt = replace(execution(), release=ReleaseReceipt(500, True))
        self.assertTrue(receipt.release.released)
        instant = replace(receipt, ended_ns=500)
        self.assertEqual(instant.started_ns, instant.ended_ns)

    def test_release_after_execution_end_remains_representable(self):
        receipt = replace(execution(), release=ReleaseReceipt(800, True))
        self.assertGreater(receipt.release.observed_ns, receipt.ended_ns)

    def test_current_unverified_held_input_is_not_a_terminal_release(self):
        receipt = replace(execution(), release=ReleaseReceipt(500, False, ("A",)))
        flow = RequestLifecycle()
        flow.record_observation(observation())
        flow.bind(binding())
        flow.authorize(lease(), now_ns=200)
        flow.begin_execution(request(), now_ns=300)
        with self.assertRaises(ContractError):
            flow.record_execution(receipt)


if __name__ == "__main__":
    unittest.main()
