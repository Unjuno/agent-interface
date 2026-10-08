"""Run explicitly: regression behavior against frozen kernel copies."""
import unittest
import os
from probe import load_kernel, make_flow


class CancellationBoundaryTests(unittest.TestCase):
    def setUp(self):
        self.k = load_kernel(os.environ.get('CANCEL_TEST_MODE') == 'candidate')

    def test_stale_release_refused_without_mutation(self):
        for ns in (0, 199, 200, 299):
            with self.subTest(ns=ns):
                flow = make_flow(self.k, 'begun')
                req = flow.request
                with self.assertRaises(self.k.ContractError):
                    flow.stop('cancelled', release=self.k.ReleaseReceipt(ns, True))
                self.assertEqual(flow.stage, self.k.Stage.AUTHORIZED)
                self.assertIs(flow.request, req)
                self.assertIsNone(flow.stop_reason)

    def test_equal_and_later_verified_release_accepted(self):
        for ns in (300, 301, 800):
            with self.subTest(ns=ns):
                flow = make_flow(self.k, 'begun')
                flow.stop('cancelled', release=self.k.ReleaseReceipt(ns, True))
                self.assertTrue(flow.outcome().release_verified)

    def test_rejected_first_begin_does_not_consume_start_bound(self):
        flow = make_flow(self.k, 'invalid_first_begin')
        flow.stop('cancelled', release=self.k.ReleaseReceipt(0, True))
        self.assertIsNone(flow.outcome().command_id)

    def test_duplicate_begin_does_not_weaken_first_start_bound(self):
        flow = make_flow(self.k, 'duplicate_begin')
        flow.stop('cancelled', release=self.k.ReleaseReceipt(350, True))
        self.assertTrue(flow.outcome().release_verified)

    def test_missing_unverified_and_held_release_refused(self):
        for receipt in (None, self.k.ReleaseReceipt(800, False),
                        self.k.ReleaseReceipt(800, False, ('A',))):
            with self.subTest(receipt=receipt):
                flow = make_flow(self.k, 'begun')
                with self.assertRaises(self.k.ContractError):
                    flow.stop('cancelled', release=receipt)
                self.assertIsNone(flow.stop_reason)


if __name__ == '__main__':
    unittest.main()
