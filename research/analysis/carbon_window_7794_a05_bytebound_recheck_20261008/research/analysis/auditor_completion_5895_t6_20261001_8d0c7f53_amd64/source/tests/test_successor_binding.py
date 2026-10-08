import unittest
from pathlib import Path

import audit
import candidate


class SuccessorAllocationBindingTests(unittest.TestCase):
    def test_orchestrator_and_auditor_are_bound_to_fresh_issue_5895_allocation(self):
        expected = "AUDIT-COMPLETION-5895-T6-AMD64-20261001-01-8d0c7f53"
        self.assertEqual(candidate.ALLOCATION, expected)
        self.assertIn(expected, Path(audit.__file__).read_text(encoding="utf-8"))

    def test_target_source_digest_pins_are_unchanged(self):
        self.assertEqual(candidate.TARGET_BLOB, "da805fb83f70a57ad68a0768186e214524689d40")
        self.assertEqual(candidate.EXPECTED_BLOB, "3d33bda096c4c8789e183e3f864ee7626e643a7e")
        self.assertEqual(candidate.FIXTURE_BLOB, "d1eb9a854cc810fa77ca173d7e2de287ee1bd64a")


if __name__ == "__main__":
    unittest.main()
