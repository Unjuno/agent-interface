"""Construction-only check that the independent full training replay matches retained packages."""
import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, "/src")
import audit_formal


class ConstructionReplayTests(unittest.TestCase):
    def test_upstream_independent_reconstruction_matches_construction_package(self):
        actual = audit_formal.regenerate(7865001)
        root = Path(__file__).parent / "construction-output"
        for arm in audit_formal.ARMS:
            d = root / arm
            artifact = json.loads((d / "skill.json").read_text(encoding="utf-8"))
            expected = json.loads((d / "expected.json").read_text(encoding="utf-8"))
            self.assertEqual(artifact["tensors"], {r: actual[arm]["roles"][r]["state"] for r in audit_formal.ROLES})
            self.assertEqual(expected["roles"], actual[arm]["roles"])
            self.assertTrue(actual[arm]["base_immutable"])
            self.assertTrue(actual[arm]["support16_prefix_of_64"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
