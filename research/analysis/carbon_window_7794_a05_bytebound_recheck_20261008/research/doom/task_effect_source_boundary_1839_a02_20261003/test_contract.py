import importlib.util
from pathlib import Path
import unittest

BASE = Path(__file__).parent
spec = importlib.util.spec_from_file_location("a02_auditor", BASE / "auditor.py")
auditor = importlib.util.module_from_spec(spec)
spec.loader.exec_module(auditor)


class A02ConstructionTests(unittest.TestCase):
    def test_six_corruptions_are_individually_rejected_by_exact_comparison(self):
        clean = {"schema": "v", "source_sha256": "x", "sessions": [{"session_id": "p1-attack", "endpoint_locators": [], "physical_join": True}],
                 "attack_joins": 1, "attack_positive_sessions": 0, "control_positive_sessions": 0,
                 "sample_total": 1, "authority_grants": 0}
        mutants = auditor.corruption_cases(clean)
        self.assertEqual(set(mutants), {"drop_session", "duplicate_session", "forge_effect",
                                        "erase_physical_join", "alter_sample_count", "grant_authority"})
        for value in mutants.values():
            with self.assertRaises(AssertionError):
                auditor.check_summary(value, clean)


if __name__ == "__main__":
    unittest.main()
