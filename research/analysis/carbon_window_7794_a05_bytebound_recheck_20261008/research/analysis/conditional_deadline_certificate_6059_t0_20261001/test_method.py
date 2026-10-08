"""Pre-freeze construction tests; formal invocation receipts are separate."""
import importlib.util
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).parent
spec = importlib.util.spec_from_file_location("candidate", ROOT / "candidate.py")
candidate = importlib.util.module_from_spec(spec)
spec.loader.exec_module(candidate)
DATA = json.loads((ROOT / "scenarios.json").read_text(encoding="utf-8"))


class CandidateConstructionTests(unittest.TestCase):
    def test_frozen_expected_labels(self):
        for case in DATA["scenarios"]:
            with self.subTest(case=case["id"]):
                self.assertEqual(candidate.classify(case)[0], case["expected"])

    def test_empirical_lower_never_proves_impossibility(self):
        case = next(c for c in DATA["scenarios"] if c["id"] == "empirical_lower_bound_cannot_prove_impossible")
        self.assertNotEqual(candidate.classify(case)[0], "CERTIFIED_DEADLINE_IMPOSSIBLE")

    def test_missing_timeout_cancellation_bound_is_unknown(self):
        case = {"deadline": 10, "stages": [{"unbounded": True, "typed_terminal": True, "timeout": 3}]}
        self.assertEqual(candidate.classify(case)[0], "UNKNOWN_UNBOUNDED_STAGE")

    def test_shared_resource_never_uses_naive_independent_sum(self):
        case = next(c for c in DATA["scenarios"] if c["id"] == "shared_resource_invalidates_composition")
        self.assertTrue(sum(s["upper"] for s in case["stages"]) <= case["deadline"])
        self.assertEqual(candidate.classify(case)[0], "UNKNOWN_SHARED_RESOURCE_CONTENTION")


if __name__ == "__main__":
    unittest.main(verbosity=2)
