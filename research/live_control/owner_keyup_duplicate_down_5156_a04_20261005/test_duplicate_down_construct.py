"""Pre-freeze checks for the one repeated-DOWN fake-Xlib trace."""
import importlib.util
import os
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
os.environ.setdefault("OUT_DIR", str(HERE / "test-output-unused"))
spec = importlib.util.spec_from_file_location("a04_runner", HERE / "run_candidate.py")
runner = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = runner
spec.loader.exec_module(runner)


class DuplicateDownConstructionTests(unittest.TestCase):
    def test_duplicate_admission_is_preserved_and_up_is_ambiguous(self):
        row = runner.run_case()
        admissions = [e for e in row["events"] if e.get("event") == "input_admission"]
        releases = [e for e in row["events"] if e.get("event") == "input_release_transition"]
        self.assertEqual((len(admissions), len(releases)), (2, 1))
        self.assertEqual([e["admission_sequence"] for e in admissions], [1, 2])
        self.assertNotEqual(admissions[0]["admission_id"], admissions[1]["admission_id"])
        self.assertEqual(releases[0]["admission_identity_status"], "ambiguous_multiple_admissions")
        self.assertEqual(releases[0]["owner_keyup_join"], "MATCHED_EXPLICIT_KEYUP")
        self.assertEqual(releases[0]["admission_id"], admissions[1]["admission_id"])
        self.assertFalse(releases[0]["grants_input_authority"])
        self.assertFalse(releases[0]["physical_verification_authoritative"])

    def test_exact_operation_order_and_neutral_cleanup(self):
        row = runner.run_case()
        self.assertEqual(row["calls"], [
            ["input", 2, 38], ["sync", 1],
            ["input", 2, 38], ["sync", 2],
            ["input", 3, 38], ["sync", 3], ["sync", 4],
        ])
        self.assertEqual(row["final_down"], [])
        cleanup = [e for e in row["owner_records"] if e.get("event") == "owner_release"]
        self.assertEqual(len(cleanup), 1)
        self.assertTrue(cleanup[0]["verified"])


if __name__ == "__main__":
    unittest.main()
