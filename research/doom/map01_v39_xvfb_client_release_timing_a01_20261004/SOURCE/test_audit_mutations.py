import copy
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location("timing_audit", HERE / "audit.py")
AUDIT = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(AUDIT)
RAW = HERE.parent / "results/A01/RAW.json"


class RawAuditMutationTests(unittest.TestCase):
    def setUp(self):
        self.raw = json.loads(RAW.read_text())

    def assert_mutation_fails(self, mutate):
        row = copy.deepcopy(self.raw)
        mutate(row)
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "mutated.json"
            path.write_text(json.dumps(row))
            result = AUDIT.audit(path)
        self.assertEqual(result["result"], "FAIL_AUDIT")
        self.assertTrue(result["errors"])

    def test_missing_trial_fails(self):
        self.assert_mutation_fails(lambda row: row["trials"].pop())

    def test_wrong_target_window_fails(self):
        self.assert_mutation_fails(lambda row: row["trials"][0]["press_event"].__setitem__("window_id", -1))

    def test_unreleased_keymap_fails(self):
        self.assert_mutation_fails(lambda row: row["trials"][1].__setitem__("key_down_after_release", True))

    def test_unverified_owner_cleanup_fails(self):
        self.assert_mutation_fails(lambda row: row["owner_close"].__setitem__("verified", False))


if __name__ == "__main__":
    unittest.main(verbosity=2)
