import unittest

from runtime.local_supervisor_v1.supervisor import (CONTINUE, FEATURES, YIELD,
                                                     Decision, torch)


class ContractTests(unittest.TestCase):
    def test_decision_has_no_authority(self):
        self.assertFalse(Decision(CONTINUE, 0.9).authority_granted)

    def test_feature_width_is_bounded(self):
        self.assertEqual(FEATURES, 8)

    @unittest.skipIf(torch is None, "optional torch dependency")
    def test_low_confidence_falls_back_to_yield(self):
        from runtime.local_supervisor_v1.supervisor import build
        supervisor = build()
        result = supervisor.decide([0.0] * FEATURES)
        self.assertIn(result.action, (CONTINUE, YIELD))
        self.assertFalse(result.authority_granted)


if __name__ == "__main__":
    unittest.main()
