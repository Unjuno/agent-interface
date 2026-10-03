"""Removing/reversing the causal guard must break these behavior tests."""
import os
import unittest
from fixtures import begun, receipt
from frozen_kernel import ContractError, Stage

if os.environ.get('BEGIN_CAUSALITY_ARM') == 'candidate':
    from candidate import BeginBoundLifecycle as Flow
else:
    from frozen_kernel import RequestLifecycle as Flow


class BeginBoundaryTests(unittest.TestCase):
    def test_receipt_start_before_accepted_begin_is_refused(self):
        flow = begun(Flow, 3)
        with self.assertRaises(ContractError):
            flow.record_execution(receipt(2, 4))

    def test_refusal_preserves_begun_command_and_stage(self):
        flow = begun(Flow, 3)
        original_request = flow.request
        try:
            flow.record_execution(receipt(0, 4))
        except ContractError:
            pass
        self.assertIs(flow.request, original_request)
        self.assertEqual(flow.stage, Stage.AUTHORIZED)
        self.assertIsNone(flow.execution)

    def test_equal_tick_is_representable(self):
        flow = begun(Flow, 3)
        flow.record_execution(receipt(3, 3))
        self.assertEqual(flow.stage, Stage.EXECUTED)

    def test_later_start_end_and_release_are_representable(self):
        flow = begun(Flow, 3)
        flow.record_execution(receipt(5, 20))
        self.assertEqual(flow.execution.ended_ns, 20)

    def test_manifest_mismatch_remains_refused(self):
        flow = begun(Flow, 3)
        with self.assertRaises(ContractError):
            flow.record_execution(receipt(3, 4, False))
        self.assertEqual(flow.stage, Stage.AUTHORIZED)

    def test_rejected_second_begin_does_not_move_lower_bound(self):
        flow = begun(Flow, 3)
        with self.assertRaises(ContractError):
            flow.begin_execution(flow.request, now_ns=10)
        flow.record_execution(receipt(3, 4))
        self.assertEqual(flow.stage, Stage.EXECUTED)


if __name__ == '__main__':
    unittest.main()
