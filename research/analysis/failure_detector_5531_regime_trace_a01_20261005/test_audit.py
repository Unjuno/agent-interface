import unittest

from audit import contiguous_zero_based, regime_for_busy, strictly_increasing


class TraceAuditTests(unittest.TestCase):
    def test_heartbeat_sequence_rejects_gap_duplicate_and_boolean_alias(self):
        self.assertTrue(contiguous_zero_based([0, 1, 2]))
        self.assertFalse(contiguous_zero_based([0, 2]))
        self.assertFalse(contiguous_zero_based([0, 0]))
        self.assertFalse(contiguous_zero_based([False, 1]))

    def test_clock_audit_requires_strict_increase(self):
        self.assertTrue(strictly_increasing([10, 11, 20]))
        self.assertFalse(strictly_increasing([10, 10]))
        self.assertFalse(strictly_increasing([10, 9]))
        self.assertTrue(strictly_increasing([]))

    def test_host_cpu_regime_boundary_is_frozen_and_inclusive(self):
        self.assertEqual(regime_for_busy(49.999), "ordinary")
        self.assertEqual(regime_for_busy(50.0), "elevated")
        self.assertEqual(regime_for_busy(100.0), "elevated")


if __name__ == "__main__":
    unittest.main()
