"""Construction tests run before the frozen one-shot differential harness."""
import unittest
from differential import analyze


class DifferentialControls(unittest.TestCase):
    def test_pristine_and_all_controls(self):
        result = analyze()
        self.assertEqual(result["decision"], "PASS_AUDITOR_SEMANTIC_COMPATIBILITY_AND_IDENTITY_SCOPED")
        self.assertEqual(result["legacy_baseline"]["errors"], [])
        self.assertEqual(result["successor_baseline"]["errors"], [])
        self.assertEqual(len(result["semantic_controls"]), 12)
        self.assertTrue(all(x["legacy_rejected"] and x["successor_rejected"] for x in result["semantic_controls"].values()))
        self.assertEqual(len(result["identity_controls"]), 5)
        self.assertTrue(all(x["legacy_accepted"] and x["successor_rejected"] for x in result["identity_controls"].values()))


if __name__ == "__main__":
    unittest.main()
